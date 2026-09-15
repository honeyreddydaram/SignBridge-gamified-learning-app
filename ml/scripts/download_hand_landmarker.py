"""
Download Google's pretrained MediaPipe HandLandmarker task bundle.

This is the off-the-shelf hand-pose detector we use to turn a raw camera
frame into 21 (x, y, z) hand-joint coordinates. It is NOT the ASL letter
classifier — that part is trained from scratch in train.py on top of these
landmarks. Source: Google's public MediaPipe Solutions model zoo, Apache 2.0.
"""

from pathlib import Path

import requests

URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
DEST = Path(__file__).resolve().parent.parent / "models" / "hand_landmarker.task"


def download() -> Path:
    DEST.parent.mkdir(parents=True, exist_ok=True)
    if DEST.exists() and DEST.stat().st_size > 1_000_000:
        print(f"Already present: {DEST} ({DEST.stat().st_size / 1e6:.1f} MB)")
        return DEST
    print(f"Downloading hand_landmarker.task from {URL} ...")
    resp = requests.get(URL, timeout=120)
    resp.raise_for_status()
    DEST.write_bytes(resp.content)
    print(f"Saved {DEST} ({DEST.stat().st_size / 1e6:.1f} MB)")
    return DEST


if __name__ == "__main__":
    download()
