"""
Shared ASL fingerspelling recognition service.

Wraps Google's pretrained MediaPipe HandLandmarker (hand pose detection) and
our own trained classifier (landmarks -> A-Z letter). This is a singleton
loaded once at process start and reused by BOTH the standalone Recognition
API and the camera-based Learning-module challenges, per the project
requirement that they share one recognition model rather than two.

The service is intentionally stateless per call (no temporal smoothing here)
— smoothing across frames is a UX concern owned by the frontend, which knows
the actual frame cadence and can debounce/require-hand-released logic. This
endpoint always returns its best single-frame estimate.
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

import cv2
import joblib
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

from app.config import get_settings

ML_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "ml" / "scripts"
if str(ML_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(ML_SCRIPTS_DIR))

from landmark_utils import landmarks_to_feature_vector  # noqa: E402

settings = get_settings()


class RecognitionService:
    def __init__(self) -> None:
        self._landmarker: vision.HandLandmarker | None = None
        self._classifier = None
        self._label_encoder = None
        self._model_loaded = False
        self._load_error: str | None = None
        self._try_load()

    def _try_load(self) -> None:
        try:
            landmarker_path = Path(settings.hand_landmarker_task_path)
            model_path = Path(settings.recognition_model_path)

            if not landmarker_path.exists():
                raise FileNotFoundError(f"hand landmarker model not found: {landmarker_path}")
            if not model_path.exists():
                raise FileNotFoundError(
                    f"trained classifier not found: {model_path}. "
                    "Run the ml/ training pipeline first (see ml/README.md)."
                )

            options = vision.HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(landmarker_path)),
                num_hands=1,
                min_hand_detection_confidence=0.5,
                min_hand_presence_confidence=0.5,
            )
            self._landmarker = vision.HandLandmarker.create_from_options(options)

            bundle = joblib.load(model_path)
            self._classifier = bundle["classifier"]
            self._label_encoder = bundle["label_encoder"]
            self._model_loaded = True
        except Exception as e:  # noqa: BLE001
            self._load_error = str(e)
            self._model_loaded = False

    @property
    def is_ready(self) -> bool:
        return self._model_loaded

    @property
    def load_error(self) -> str | None:
        return self._load_error

    @staticmethod
    def decode_base64_image(image_base64: str) -> np.ndarray:
        if "," in image_base64 and image_base64.strip().startswith("data:"):
            image_base64 = image_base64.split(",", 1)[1]
        img_bytes = base64.b64decode(image_base64)
        arr = np.frombuffer(img_bytes, dtype=np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("could not decode image")
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    def predict(self, rgb_image: np.ndarray) -> tuple[bool, str | None, float]:
        """Returns (hand_detected, predicted_letter_or_None, confidence_0_to_1)."""
        if not self._model_loaded:
            raise RuntimeError(f"recognition model not loaded: {self._load_error}")

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
        result = self._landmarker.detect(mp_image)

        if not result.hand_landmarks:
            return False, None, 0.0

        landmarks = result.hand_landmarks[0]
        coords = [(p.x, p.y, p.z) for p in landmarks]
        features = landmarks_to_feature_vector(coords).reshape(1, -1)

        probs = self._classifier.predict_proba(features)[0]
        best_idx = int(np.argmax(probs))
        confidence = float(probs[best_idx])
        letter = str(self._label_encoder.inverse_transform([best_idx])[0])

        return True, letter, confidence


_service: RecognitionService | None = None


def get_recognition_service() -> RecognitionService:
    global _service
    if _service is None:
        _service = RecognitionService()
    return _service
