"""
Shared hand-landmark feature extraction.

This module is imported by BOTH the training pipeline (ml/scripts/*) and the
backend inference service (backend/app/services/recognition_service.py) so
that features fed to the classifier at train time and at inference time are
produced by *exactly* the same code path. That is what makes it possible to
share one recognition model between the standalone Recognition module and the
camera-based Learning challenges, per the project requirement.
"""

from __future__ import annotations

import numpy as np

NUM_LANDMARKS = 21
FEATURE_DIM = NUM_LANDMARKS * 3  # x, y, z per landmark


def landmarks_to_feature_vector(landmarks: list[tuple[float, float, float]]) -> np.ndarray:
    """
    Convert 21 raw (x, y, z) MediaPipe hand landmarks (image-normalized coords,
    roughly 0..1 for x/y) into a translation- and scale-invariant feature
    vector suitable for a classifier.

    Invariance matters because the same letter must be recognized regardless
    of where the hand is in frame or how close it is to the camera.
    """
    if len(landmarks) != NUM_LANDMARKS:
        raise ValueError(f"expected {NUM_LANDMARKS} landmarks, got {len(landmarks)}")

    pts = np.array(landmarks, dtype=np.float64)  # shape (21, 3)

    # Translation invariance: origin at the wrist (landmark 0).
    wrist = pts[0].copy()
    pts -= wrist

    # Scale invariance: normalize by the distance from wrist to the middle
    # finger MCP joint (landmark 9), a stable proxy for overall hand size.
    scale = np.linalg.norm(pts[9])
    if scale < 1e-6:
        scale = 1e-6
    pts /= scale

    return pts.flatten().astype(np.float32)  # shape (63,)
