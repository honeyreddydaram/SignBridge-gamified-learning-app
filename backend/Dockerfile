# Build context is the REPO ROOT (not backend/), so this image can bake in
# ml/models — see docker-compose.yml and render.yaml, both of which set the
# build context accordingly. This lets the same image run standalone (Render)
# and locally (docker-compose, where a volume mount at the same path
# transparently overrides these baked-in files with the host's live copies).

FROM python:3.13-slim

WORKDIR /app

# libgl1/libglib needed by opencv-python-headless + mediapipe at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.lock.txt backend/requirements.lock.txt
RUN pip install --no-cache-dir -r backend/requirements.lock.txt

COPY backend/ backend/

# ml/models/{asl_landmark_classifier.joblib,reference_landmarks.json} and
# ml/word_signs_verified.json are real trained/derived/curated artifacts
# committed to the repo (see ml/README.md and asl_signs.py). hand_landmarker
# .task is Google's pretrained model, deliberately NOT committed (see
# ml/.gitignore) -- fetched here at build time instead, same script the
# local setup instructions use.
COPY ml/models/asl_landmark_classifier.joblib ml/models/asl_landmark_classifier.joblib
COPY ml/models/reference_landmarks.json ml/models/reference_landmarks.json
COPY ml/word_signs_verified.json ml/word_signs_verified.json
COPY ml/scripts/download_hand_landmarker.py ml/scripts/download_hand_landmarker.py
RUN python ml/scripts/download_hand_landmarker.py

WORKDIR /app/backend

EXPOSE 8000

# $PORT is set by hosts like Render; defaults to 8000 for docker-compose/local.
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
