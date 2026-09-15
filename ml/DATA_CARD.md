# Data Card — ASL Alphabet Recognition

## Source

- **Dataset**: [`Marxulia/asl_sign_languages_alphabets_v03`](https://huggingface.co/datasets/Marxulia/asl_sign_languages_alphabets_v03) (HuggingFace Hub)
- **Access**: public, no authentication required, downloaded via `ml/scripts/download_dataset.py`
- **License**: not specified by the uploader on the dataset card. Because of that, **this project does not redistribute the images** — only the download script is committed to the repo (`ml/data/` is gitignored). Used here for non-commercial, educational purposes only.
- **Size**: 10,873 images, 26 classes (A-Z), roughly balanced (380-420 images/class as originally distributed).

## Important structural property discovered during preprocessing

Inspecting filenames (`extract_landmarks.py` / analysis during development) revealed the images are **not 10,873 independent photos**. Each letter has:

- ~16-20 unique original source photos (filenames like `A9.jpg`, `K4.jpg`)
- Exactly **one** of those source photos per letter is heavily augmented (rotation/brightness/crop, filenames like `A9_aug_383.jpg`) into 300+ near-duplicate variants
- The rest appear exactly once, unaugmented

Total unique source photos: **520** (20/letter as distributed; 417 after hand-detection filtering, see below).

This matters a lot for methodology:
- **Naive random image-level splitting would leak**: augmented copies of the same source photo could land in both train and test, inflating accuracy with near-duplicates.
- **A single fixed group-level train/val split is unstable**: whichever split receives a letter's one heavily-augmented photo gets 20-30x more data for that letter than a split that doesn't. This was caught empirically during training (see `ml/MODEL_CARD.md`).

## Preprocessing (`extract_landmarks.py`)

1. Decode each image, run Google's pretrained MediaPipe HandLandmarker (`num_hands=1`, `min_hand_detection_confidence=0.3`).
2. **Hand detection rate: 79.44%** (8,638 / 10,873) — images where MediaPipe found no hand are dropped, not imputed. Drop rate is roughly even across letters (59-124 per letter out of ~420), see `ml/data/processed/extraction_report.json` for exact per-letter counts.
3. For detected hands, normalize the 21 (x, y, z) landmarks: origin at wrist, scale by wrist-to-middle-finger-MCP distance (see `landmark_utils.py`) — this is the SAME code path used at inference time.
4. Record each image's `base_id` (letter + source photo number, stripped of the `_aug_N` suffix) for leakage-safe grouping.

## Train/test methodology (`train.py`)

1. Cap each source photo to at most 20 images (prevents the one heavily-augmented photo per letter from dominating).
2. Split by `base_id` (source photo), never by individual image: 80% of source photos per letter → trainval pool, 20% → held-out test set.
3. Model selection: 5-fold **GroupKFold** cross-validation within the trainval pool (grouped by `base_id`, so no leakage within folds either) — not a single fixed validation split (see MODEL_CARD.md for why).
4. Final model refit on the entire trainval pool, evaluated exactly once on the untouched test set.

## Known limitations

- Effective diversity is bounded by ~16-20 unique real photos per letter, not 10,873 — augmentation adds pose/lighting variety from those source photos but not new people/hands.
- Held-out test set is small (~77 images, ~3/letter after the 80/20 photo-level split) because it's bounded by the true count of unique source photos. See the Wilson confidence interval reported in `ml/reports/metrics.json` for how much uncertainty that implies.
- All source photos appear to come from a small number of signers/hands — no claim of generalization across skin tones, hand sizes, or camera hardware is made or tested.
