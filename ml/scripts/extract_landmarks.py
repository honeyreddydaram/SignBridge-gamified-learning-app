"""
Preprocessing step: turn the raw ASL alphabet image dataset into a table of
hand-landmark feature vectors (see landmark_utils.py) ready for training.

For every image:
  1. Decode bytes -> RGB array.
  2. Run Google's pretrained MediaPipe HandLandmarker to find 21 hand joints.
  3. If a hand was found, normalize the joints into a 63-dim feature vector.
  4. Record which *base source photo* the image came from (stripping any
     "_aug_N" augmentation suffix) so training can later split train/val/test
     by base photo rather than by individual augmented image — augmented
     copies of the same photo must never be split across sets, or evaluation
     numbers would be inflated by leakage.

Images where no hand is detected are dropped and counted, not silently
imputed with zeros — this is logged and reported in ml/DATA_CARD.md.

Usage:
    python extract_landmarks.py
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
from mediapipe.tasks.python import BaseOptions, vision

from landmark_utils import landmarks_to_feature_vector

ML_DIR = Path(__file__).resolve().parent.parent
RAW_PARQUET = ML_DIR / "data" / "raw" / "train.parquet"
LANDMARKER_MODEL = ML_DIR / "models" / "hand_landmarker.task"
OUTPUT_PARQUET = ML_DIR / "data" / "processed" / "landmarks.parquet"
REPORT_PATH = ML_DIR / "data" / "processed" / "extraction_report.json"

LABEL_TO_LETTER = {i: chr(ord("A") + i) for i in range(26)}


def base_id_from_path(path: str) -> str:
    stem = re.sub(r"\.[a-zA-Z]+$", "", path)
    return re.sub(r"_aug_\d+$", "", stem)


def build_landmarker() -> vision.HandLandmarker:
    options = vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(LANDMARKER_MODEL)),
        num_hands=1,
        min_hand_detection_confidence=0.3,
        min_hand_presence_confidence=0.3,
    )
    return vision.HandLandmarker.create_from_options(options)


def decode_image(img_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def main() -> None:
    if not RAW_PARQUET.exists():
        raise SystemExit(f"Missing {RAW_PARQUET} — run download_dataset.py first.")
    if not LANDMARKER_MODEL.exists():
        raise SystemExit(f"Missing {LANDMARKER_MODEL} — run download_hand_landmarker.py first.")

    OUTPUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(RAW_PARQUET)
    print(f"Loaded {len(df)} raw images")

    landmarker = build_landmarker()

    rows = []
    no_hand_count = 0
    no_hand_by_label: dict[str, int] = {}
    start = time.time()

    for i, rec in enumerate(df.itertuples(index=False)):
        img_dict = rec.image
        label = int(rec.label)
        letter = LABEL_TO_LETTER[label]
        path = img_dict["path"]

        rgb = decode_image(img_dict["bytes"])
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect(mp_image)

        if not result.hand_landmarks:
            no_hand_count += 1
            no_hand_by_label[letter] = no_hand_by_label.get(letter, 0) + 1
            continue

        lm = result.hand_landmarks[0]
        coords = [(p.x, p.y, p.z) for p in lm]
        features = landmarks_to_feature_vector(coords)

        row = {
            "base_id": base_id_from_path(path),
            "source_path": path,
            "label": label,
            "letter": letter,
        }
        for j, v in enumerate(features):
            row[f"f{j}"] = float(v)
        rows.append(row)

        if (i + 1) % 500 == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            print(f"  {i + 1}/{len(df)} processed ({rate:.0f} img/s, {no_hand_count} no-hand so far)")

    elapsed = time.time() - start
    print(f"Done in {elapsed:.1f}s. {len(rows)} usable, {no_hand_count} dropped (no hand detected).")

    out_df = pd.DataFrame(rows)
    out_df.to_parquet(OUTPUT_PARQUET, index=False)
    print(f"Saved features to {OUTPUT_PARQUET}")

    report = {
        "total_images": len(df),
        "usable_images": len(rows),
        "no_hand_detected": no_hand_count,
        "detection_rate_pct": round(100 * len(rows) / len(df), 2),
        "no_hand_by_letter": no_hand_by_label,
        "unique_base_photos_usable": out_df["base_id"].nunique() if len(out_df) else 0,
        "elapsed_seconds": round(elapsed, 1),
    }
    import json

    REPORT_PATH.write_text(json.dumps(report, indent=2))
    print(f"Report saved to {REPORT_PATH}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
