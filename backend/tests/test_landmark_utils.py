import sys
from pathlib import Path

import numpy as np
import pytest

ML_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "ml" / "scripts"
sys.path.insert(0, str(ML_SCRIPTS_DIR))

from landmark_utils import FEATURE_DIM, landmarks_to_feature_vector  # noqa: E402


def _fake_hand(offset=(0.0, 0.0, 0.0), scale=1.0):
    """21 landmarks with a fixed, arbitrary but non-degenerate shape."""
    base = [(0.0, 0.0, 0.0)] + [(0.01 * i, 0.02 * i, 0.0) for i in range(1, 21)]
    return [(x * scale + offset[0], y * scale + offset[1], z + offset[2]) for x, y, z in base]


def test_output_shape():
    features = landmarks_to_feature_vector(_fake_hand())
    assert features.shape == (FEATURE_DIM,)


def test_translation_invariance():
    a = landmarks_to_feature_vector(_fake_hand(offset=(0, 0, 0)))
    b = landmarks_to_feature_vector(_fake_hand(offset=(0.5, -0.3, 0)))
    np.testing.assert_allclose(a, b, atol=1e-5)


def test_scale_invariance():
    a = landmarks_to_feature_vector(_fake_hand(scale=1.0))
    b = landmarks_to_feature_vector(_fake_hand(scale=3.0))
    np.testing.assert_allclose(a, b, atol=1e-5)


def test_wrong_landmark_count_raises():
    with pytest.raises(ValueError):
        landmarks_to_feature_vector([(0, 0, 0)] * 10)
