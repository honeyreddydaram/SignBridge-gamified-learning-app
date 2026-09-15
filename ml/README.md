# ML Pipeline

Real, reproducible training pipeline for the ASL fingerspelling recognizer. No step here is precomputed or faked — running these scripts is how `ml/models/` and `ml/reports/` got their contents in the first place.

See `DATA_CARD.md` (dataset provenance + methodology) and `MODEL_CARD.md` (actual measured results) for the full story — this file is just the "how to run it" reference.

## Pipeline

```bash
cd ml/scripts
python download_dataset.py          # HuggingFace: Marxulia/asl_sign_languages_alphabets_v03 (~74MB, no auth)
python download_hand_landmarker.py  # Google's pretrained MediaPipe HandLandmarker (~8MB)
python extract_landmarks.py         # runs hand detection over all 10,873 images (~3-4 min CPU)
python train.py                     # trains + evaluates the classifier (~1-2 min CPU)
```

Each script prints real progress and writes real output — there's nothing to configure to get "a result"; the numbers you get are the numbers that were actually produced.

## Outputs

| Path | What it is |
|---|---|
| `data/raw/train.parquet` | Downloaded dataset (gitignored) |
| `data/processed/landmarks.parquet` | Extracted 63-dim feature vectors + labels (gitignored) |
| `data/processed/extraction_report.json` | Hand-detection rate, per-letter drop counts |
| `models/hand_landmarker.task` | Google's pretrained hand-pose model (gitignored, downloaded) |
| `models/asl_landmark_classifier.joblib` | The trained classifier + label encoder (gitignored, produced by train.py) |
| `models/reference_landmarks.json` | Per-letter representative hand pose, used by the frontend for sign cards |
| `reports/metrics.json` | Full evaluation: accuracy, CI, per-class precision/recall/F1, methodology notes |
| `reports/confusion_matrix.png` | Visual confusion matrix on the held-out test set |

Everything under `data/`, and the two large `models/*` artifacts, is gitignored — re-run the pipeline to regenerate them locally rather than expecting them to be in the repo.

## Key files

- `landmark_utils.py` — the ONE normalization function (wrist-origin + scale invariant), imported by both this pipeline and the backend's inference service. See `ARCHITECTURE.md` at the repo root for why that matters.
- `train.py` — has the full methodology writeup in its module docstring (leakage-safe splitting, why cross-validation is used instead of a single validation split, per-photo capping). Worth reading before treating the numbers as self-explanatory.
