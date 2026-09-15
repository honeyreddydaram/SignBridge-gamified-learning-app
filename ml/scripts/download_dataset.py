"""
Download the ASL alphabet image dataset used to train the recognition model.

Dataset: Marxulia/asl_sign_languages_alphabets_v03 (HuggingFace Hub)
  https://huggingface.co/datasets/Marxulia/asl_sign_languages_alphabets_v03
  10,873 images across all 26 A-Z classes, public, no authentication required.

License is not specified by the uploader on the dataset card, so this project
does NOT redistribute the images: this script only downloads them to a local,
gitignored `ml/data/raw/` directory for your own training run. See
ml/DATA_CARD.md for full provenance and usage notes.

Usage:
    python download_dataset.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import requests

DATASET_ID = "Marxulia/asl_sign_languages_alphabets_v03"
PARQUET_URL = (
    f"https://huggingface.co/api/datasets/{DATASET_ID}/parquet/default/train/0.parquet"
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PARQUET_PATH = RAW_DIR / "train.parquet"


def download() -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if PARQUET_PATH.exists() and PARQUET_PATH.stat().st_size > 0:
        print(f"Already downloaded: {PARQUET_PATH} ({PARQUET_PATH.stat().st_size / 1e6:.1f} MB)")
        return PARQUET_PATH

    print(f"Downloading {DATASET_ID} ...")
    with requests.get(PARQUET_URL, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        written = 0
        with open(PARQUET_PATH, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                written += len(chunk)
                if total:
                    pct = 100 * written / total
                    print(f"\r  {written / 1e6:.1f} / {total / 1e6:.1f} MB ({pct:.0f}%)", end="")
        print()

    print(f"Saved to {PARQUET_PATH}")
    return PARQUET_PATH


if __name__ == "__main__":
    try:
        download()
    except requests.RequestException as e:
        print(f"Download failed: {e}", file=sys.stderr)
        sys.exit(1)
