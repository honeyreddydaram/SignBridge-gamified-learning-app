# Model Card — ASL Alphabet Landmark Classifier

All numbers on this page are copied directly from `ml/reports/metrics.json`,
produced by `ml/scripts/train.py`. Regenerate by re-running the pipeline
(see `ml/README.md`) — nothing here is hand-edited or estimated.

## What this model is

A classifier that maps a **normalized 21-point MediaPipe hand landmark pose**
(63 numbers: x, y, z per landmark, wrist-origin + scale normalized — see
`ml/scripts/landmark_utils.py`) to one of 26 ASL fingerspelling letters
(A-Z). It does **not** operate on raw pixels — hand detection is a separate,
pretrained step (Google's MediaPipe HandLandmarker).

## Architecture & selection

Four candidates were compared via 5-fold GroupKFold cross-validation
(grouped by source photo) over the trainval pool (n=834 images / 340 source
photos):

| Candidate | Mean 5-fold group-CV accuracy |
|---|---|
| Random Forest (300 trees) | 33.8% |
| **MLP (128, 64 hidden units)** — selected | **40.4%** |
| SVM (RBF kernel) | 39.0% |
| k-NN (k=5, distance-weighted) | 35.8% |

MLP was selected and refit on the full trainval pool, then evaluated once on
the held-out test set.

## Held-out test results

- **Test accuracy: 85.7%** (66/77 correct)
- **95% Wilson confidence interval: [76.2%, 91.8%]** (n=77 — small, see caveat below)
- Macro-averaged F1: 0.863, weighted F1: 0.861

Confusion matrix: `ml/reports/confusion_matrix.png`. Full per-letter
precision/recall/F1: `ml/reports/metrics.json`.

Weakest letters in this test run (n=2-3 examples each, so treat as
indicative, not conclusive): **R, S** (precision 0.50), **K, M** (F1 0.67).
These involve fine finger-crossing/tucking distinctions (R/U, S/T/N/M) that
are genuinely harder to separate from a single static landmark frame.

## Why cross-validation accuracy (40%) is much lower than test accuracy (86%) — explained, not hidden

This gap looks alarming out of context, so here is the actual mechanism,
verified during development (not a guess):

1. The source dataset gives each letter only ~16-20 unique real photos; one
   of them is augmented into 300+ variants, the rest appear once (see
   `ml/DATA_CARD.md`).
2. Within any single CV fold, that one heavily-augmented photo is sometimes
   in the fold's training portion and sometimes in its validation portion.
   When it's absent from a fold's training portion, that letter has only a
   handful of real (unaugmented) training examples for that fold —
   genuinely harder to learn from than the full trainval pool.
3. CV folds therefore train on **less data, and sometimes on a materially
   weaker sample of a given letter**, than the final model does. The final
   model is refit on the *entire* trainval pool (all 340 source photos),
   so it has access to every letter's full augmented family. This is a
   known effect of cross-validation on small datasets — it's a
   conservative, "worst-case-ish" estimate of a smaller model, not an
   estimate of the model actually shipped.

An earlier, less careful version of this pipeline used a single fixed
train/val split instead of cross-validation for model selection, and got
validation accuracy anywhere from ~30% to ~95% across reruns depending
purely on which random split the one heavily-augmented photo happened to
land in — that instability is what prompted switching to GroupKFold CV in
the first place. The 40%/86% gap reported here is the honest result of the
more rigorous methodology, not a step backward.

## Practical implications for the live app

- **Confidence threshold** (`RECOGNITION_CONFIDENCE_THRESHOLD=0.75` by
  default, see `backend/.env.example`) rejects low-confidence predictions
  rather than showing a possibly-wrong letter — appropriate given the model
  is trained on a small, single-source-diversity dataset.
- **Do not treat 85.7% as "the" accuracy of the shipped model in general
  webcam use.** It is the accuracy on 77 held-out photos from the *same*
  dataset (same lighting/background/photography style). Real-world webcam
  accuracy — different camera, lighting, hand, background — has **not**
  been measured and is very likely lower. Treat the app's live recognition
  as a demonstration of a real, working, honestly-evaluated pipeline, not
  as a validated production-grade recognizer.
- The letters flagged as weakest above (R, S, K, M) are worth extra
  skepticism if the live demo seems to confuse them.

## Reproducing these numbers

```bash
cd ml/scripts
python download_dataset.py
python download_hand_landmarker.py
python extract_landmarks.py
python train.py
```

Each step prints its own real-time progress and writes its outputs under
`ml/data/`, `ml/models/`, and `ml/reports/` — nothing is precomputed or
checked into git (see `.gitignore`).
