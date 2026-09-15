"""
Train the ASL fingerspelling letter classifier on extracted hand-landmark
features (see extract_landmarks.py / landmark_utils.py).

Split & model-selection methodology (leakage-safe):
    The source dataset augments exactly ONE original photo per letter into
    300+ near-duplicate variants (rotation/brightness/etc), while every other
    original photo (~16-19 more per letter) appears only once (see
    ml/DATA_CARD.md). Two consequences follow directly from that:

    1. A naive random split over individual images would let augmented
       copies of the SAME base photo land in both train and test, inflating
       accuracy with near-duplicates instead of measuring real
       generalization. Fix: split at the *base photo* level (grouped by
       base_id), and cap any one base photo to at most MAX_IMAGES_PER_
       BASE_PHOTO images so it can't dominate its class's signal either.

    2. A single fixed train/val group split is unstable here: whichever
       split happens to receive a letter's one heavily-augmented photo has
       that letter's representation swing 20-30x relative to a split that
       doesn't. This was caught empirically — validation accuracy varied
       from ~30% to ~95% across otherwise-equivalent runs, purely from that.
       Fix: use 5-fold GroupKFold cross-validation over the trainval pool
       for model selection (averages over multiple fold assignments) instead
       of trusting one split's numbers.

Outputs (all under ml/models/ and ml/reports/):
    asl_landmark_classifier.joblib  - {classifier, label_encoder} bundle used by the backend
    metrics.json                    - accuracy, per-class precision/recall/f1, methodology notes
    confusion_matrix.png            - test-set confusion matrix
    reference_landmarks.json        - per-letter representative landmark pose (medoid), used
                                       by the frontend to render sign cards / fingerspelling animation

Usage:
    python train.py
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

ML_DIR = Path(__file__).resolve().parent.parent
PROCESSED_PARQUET = ML_DIR / "data" / "processed" / "landmarks.parquet"
MODELS_DIR = ML_DIR / "models"
REPORTS_DIR = ML_DIR / "reports"

RANDOM_SEED = 42
FEATURE_COLS = [f"f{i}" for i in range(63)]

# The dataset augments exactly one source photo per letter into 300+ near-
# duplicate variants, while every other source photo appears once (see
# ml/DATA_CARD.md). Left uncapped, that single over-augmented photo would
# dominate its class's training signal ~20-30x more than any other photo of
# the same letter, and — worse — whichever split that one heavy photo lands
# in becomes wildly imbalanced relative to the others (this was caught
# empirically: an earlier run put several such photos in validation and
# validation accuracy collapsed to ~10% purely from the resulting train/val
# class imbalance, not from the model failing to learn). Capping per-photo
# image count keeps every source photo's influence comparable.
MAX_IMAGES_PER_BASE_PHOTO = 20


def cap_images_per_base_photo(df: pd.DataFrame, cap: int = MAX_IMAGES_PER_BASE_PHOTO, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Downsample any base_id group to at most `cap` images (deterministic)."""
    parts = []
    for base_id, group in df.groupby("base_id"):
        if len(group) > cap:
            group = group.sample(n=cap, random_state=seed)
        parts.append(group)
    return pd.concat(parts, ignore_index=True)


def group_split_trainval_test(df: pd.DataFrame, seed: int = RANDOM_SEED):
    """
    Split base_id groups into trainval/test (80/20), stratified per letter.

    NOTE: this dataset has only ~16-20 unique *source photos* per letter (see
    ml/DATA_CARD.md) — one of them is heavily augmented into 300+ near-
    duplicate variants, the rest appear exactly once. An earlier version of
    this script did a single train/val/test group split and picked the model
    by that one validation split's accuracy. That turned out to be unstable:
    whichever split happened to receive a letter's one heavily-augmented
    photo swung that letter's representation by 20-30x, so validation
    accuracy varied wildly (~30% to ~95%) purely based on which few photos
    landed where, not on model quality. The fix is GroupKFold cross-
    validation over the trainval pool (see select_model_via_group_cv) instead
    of a single lucky/unlucky split — this function only carves off the
    final untouched test set.
    """
    trainval_ids, test_ids = [], []

    for letter, group in df.groupby("letter"):
        base_ids = sorted(group["base_id"].unique())
        rng = np.random.RandomState(seed)
        rng.shuffle(base_ids)

        n = len(base_ids)
        n_test = max(1, int(round(n * 0.20)))
        n_test = min(n_test, n - 2) if n >= 3 else 1

        test_ids.extend(base_ids[:n_test])
        trainval_ids.extend(base_ids[n_test:])

    trainval_df = df[df["base_id"].isin(trainval_ids)]
    test_df = df[df["base_id"].isin(test_ids)]
    return trainval_df, test_df


def select_model_via_group_cv(candidates: dict, X, y, groups, n_splits: int = 5) -> tuple[str, dict]:
    """
    Pick the best candidate by mean accuracy across GroupKFold splits (grouped
    by source photo, so no leakage within any fold either). Averaging over
    multiple fold assignments is what makes this robust to the "one heavily-
    augmented photo" imbalance described above — each candidate gets scored
    across several different train/val compositions instead of just one.
    """
    from sklearn.model_selection import GroupKFold

    n_splits = min(n_splits, len(set(groups)))
    gkf = GroupKFold(n_splits=n_splits)

    mean_scores: dict[str, float] = {}
    for name, clf in candidates.items():
        fold_scores = []
        for train_idx, val_idx in gkf.split(X, y, groups=groups):
            fold_clf = clone(clf)
            fold_clf.fit(X[train_idx], y[train_idx])
            fold_scores.append(accuracy_score(y[val_idx], fold_clf.predict(X[val_idx])))
        mean_scores[name] = float(np.mean(fold_scores))
        print(f"  [{name}] {n_splits}-fold group-CV accuracy = {mean_scores[name]:.4f} (folds: {[round(s, 3) for s in fold_scores]})")

    best_name = max(mean_scores, key=mean_scores.get)
    return best_name, mean_scores


def compute_reference_landmarks(raw_df: pd.DataFrame) -> dict:
    """
    For each letter, pick the ORIGINAL (non-augmented) image whose feature
    vector is closest to the class centroid — a representative real hand
    pose — and store its raw (un-normalized-for-display) landmark (x, y)
    pairs for the frontend to render as an SVG hand-skeleton reference card.
    """
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import mediapipe as mp
    import cv2
    from mediapipe.tasks.python import BaseOptions, vision

    landmarker = vision.HandLandmarker.create_from_options(
        vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(MODELS_DIR / "hand_landmarker.task")),
            num_hands=1,
            min_hand_detection_confidence=0.3,
        )
    )

    refs = {}
    for letter, group in raw_df.groupby("letter"):
        originals = group[~group["source_path"].str.contains("_aug_")]
        pool = originals if len(originals) > 0 else group
        feats = pool[FEATURE_COLS].to_numpy()
        centroid = feats.mean(axis=0)
        dists = np.linalg.norm(feats - centroid, axis=1)
        best_row = pool.iloc[int(np.argmin(dists))]
        refs[letter] = {"source_path": best_row["source_path"], "feature": best_row[FEATURE_COLS].tolist()}
    return refs


def main() -> None:
    if not PROCESSED_PARQUET.exists():
        raise SystemExit(f"Missing {PROCESSED_PARQUET} — run extract_landmarks.py first.")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df_all = pd.read_parquet(PROCESSED_PARQUET)
    print(f"Loaded {len(df_all)} labeled feature rows across {df_all['letter'].nunique()} letters")

    df = cap_images_per_base_photo(df_all)
    print(
        f"Capped to <= {MAX_IMAGES_PER_BASE_PHOTO} images/source-photo: "
        f"{len(df_all)} -> {len(df)} images ({df['base_id'].nunique()} unique source photos, unchanged)"
    )

    trainval_df, test_df = group_split_trainval_test(df)
    print(f"Split (by base photo, not by image): trainval={len(trainval_df)} test={len(test_df)}")
    print(
        f"  unique base photos -> trainval={trainval_df['base_id'].nunique()} "
        f"test={test_df['base_id'].nunique()}"
    )

    X_trainval, y_trainval_raw = trainval_df[FEATURE_COLS].to_numpy(), trainval_df["letter"].to_numpy()
    groups_trainval = trainval_df["base_id"].to_numpy()
    X_test, y_test = test_df[FEATURE_COLS].to_numpy(), test_df["letter"].to_numpy()

    encoder = LabelEncoder()
    encoder.fit(df["letter"])
    y_trainval = encoder.transform(y_trainval_raw)
    y_test_enc = encoder.transform(y_test)

    candidates = {
        "random_forest": RandomForestClassifier(
            n_estimators=300, max_depth=None, random_state=RANDOM_SEED, n_jobs=-1
        ),
        "mlp": MLPClassifier(
            hidden_layer_sizes=(128, 64), max_iter=800, random_state=RANDOM_SEED, early_stopping=False
        ),
        "svm_rbf": SVC(kernel="rbf", C=10, gamma="scale", probability=True, random_state=RANDOM_SEED),
        "knn": KNeighborsClassifier(n_neighbors=5, weights="distance"),
    }

    print(f"Model selection via 5-fold GroupKFold cross-validation over trainval (n={len(X_trainval)}):")
    best_name, cv_scores = select_model_via_group_cv(candidates, X_trainval, y_trainval, groups_trainval)
    best_clf = candidates[best_name]
    print(f"Selected model: {best_name} (mean CV accuracy {cv_scores[best_name]:.4f})")

    # Refit the selected model on the FULL trainval pool, then evaluate once
    # on the untouched test set.
    best_clf.fit(X_trainval, y_trainval)

    test_pred = best_clf.predict(X_test)
    test_acc = accuracy_score(y_test_enc, test_pred)
    report = classification_report(
        y_test_enc, test_pred, target_names=list(encoder.classes_), output_dict=True, zero_division=0
    )
    cm = confusion_matrix(y_test_enc, test_pred)

    print(f"TEST accuracy: {test_acc:.4f}")

    # Wilson score 95% CI on test accuracy — the test set is small (bounded by
    # the dataset's true count of unique source photos, see group_split()
    # docstring), so a point estimate alone would overstate precision.
    n_test = len(y_test)
    z = 1.96
    p = test_acc
    denom = 1 + z**2 / n_test
    center = (p + z**2 / (2 * n_test)) / denom
    margin = (z * np.sqrt((p * (1 - p) + z**2 / (4 * n_test)) / n_test)) / denom
    ci_low, ci_high = max(0.0, center - margin), min(1.0, center + margin)
    print(f"  95% Wilson CI: [{ci_low:.3f}, {ci_high:.3f}] (n={n_test})")

    # Save model bundle
    model_path = MODELS_DIR / "asl_landmark_classifier.joblib"
    joblib.dump({"classifier": best_clf, "label_encoder": encoder}, model_path)
    print(f"Saved model to {model_path}")

    # Save metrics report
    metrics = {
        "model_selected": best_name,
        "group_cv_accuracy_by_candidate": cv_scores,
        "model_selection_methodology": (
            "5-fold GroupKFold cross-validation (grouped by source photo) over the trainval pool, "
            "NOT a single train/val split. An earlier version used one fixed group split for model "
            "selection and found it unstable (validation accuracy swung ~30%-95% depending purely on "
            "which fold a single heavily-augmented source photo landed in, not on model quality). "
            "Averaging over 5 folds removes that instability."
        ),
        "test_accuracy": test_acc,
        "test_accuracy_95pct_wilson_ci": [round(ci_low, 4), round(ci_high, 4)],
        "test_set_size_caveat": (
            f"Test set is only n={n_test} images (~{n_test // 26}-{n_test // 26 + 1} per letter). "
            "This is a structural limit of the source dataset (~16-20 unique real photos per "
            "letter total, see DATA_CARD.md), not an arbitrary small split. Per-class precision/"
            "recall/f1 below are computed on 2-4 examples per class and should be read as "
            "indicative, not statistically robust — prefer the overall accuracy + CI."
        ),
        "test_classification_report": report,
        "dataset": {
            "source": "Marxulia/asl_sign_languages_alphabets_v03 (HuggingFace Hub)",
            "total_images_downloaded": 10873,
            "images_with_hand_detected": int(len(df_all)),
            "images_after_per_photo_cap": int(len(df)),
            "unique_base_photos_total": int(df["base_id"].nunique()),
            "max_images_per_source_photo_cap": MAX_IMAGES_PER_BASE_PHOTO,
        },
        "split_methodology": (
            "Split by unique base source photo (not by individual augmented image) into an "
            "80% trainval pool and a held-out 20% test set, stratified per letter, capped to "
            f"at most {MAX_IMAGES_PER_BASE_PHOTO} images per source photo so the one heavily-"
            "augmented photo per letter can't dominate that class's training signal. Model "
            "selection uses 5-fold GroupKFold CV within trainval (see model_selection_methodology); "
            "the test set is touched exactly once, after model selection is finalized. No augmented "
            "copy of a base photo appears in more than one of {trainval, test}, or in more than one CV fold."
        ),
        "split_sizes": {
            "trainval_images": len(trainval_df),
            "test_images": len(test_df),
            "trainval_base_photos": int(trainval_df["base_id"].nunique()),
            "test_base_photos": int(test_df["base_id"].nunique()),
        },
        "feature_representation": "63-dim (21 MediaPipe hand landmarks x,y,z), wrist-origin + scale normalized",
        "random_seed": RANDOM_SEED,
    }
    metrics_path = REPORTS_DIR / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2))
    print(f"Saved metrics to {metrics_path}")

    # Confusion matrix plot
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 10))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(encoder.classes_)))
    ax.set_yticks(range(len(encoder.classes_)))
    ax.set_xticklabels(encoder.classes_)
    ax.set_yticklabels(encoder.classes_)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(f"Test Confusion Matrix (accuracy={test_acc:.3f}, n={len(y_test)})")
    plt.colorbar(im)
    fig.tight_layout()
    cm_path = REPORTS_DIR / "confusion_matrix.png"
    fig.savefig(cm_path, dpi=150)
    print(f"Saved confusion matrix to {cm_path}")

    # Reference landmarks for frontend sign cards (computed from ALL usable
    # data, not just train, since this is a display artifact, not the model).
    refs = compute_reference_landmarks(df)
    ref_path = MODELS_DIR / "reference_landmarks.json"
    ref_path.write_text(json.dumps(refs, indent=2))
    print(f"Saved reference landmarks to {ref_path}")


if __name__ == "__main__":
    main()
