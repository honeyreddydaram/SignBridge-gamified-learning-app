# SignBridge

A full-stack ASL (American Sign Language) accessibility and learning app with three integrated modules:

1. **Recognition** — real webcam ASL fingerspelling recognition (A-Z), backed by a landmark-based classifier trained on real data (see `ml/`).
2. **Interpretation** — English text → ASL, with A-Z fingerspelling and a small set of recognized whole-word signs, clearly distinguished from each other and from full grammatical ASL translation (which this app does **not** claim to do).
3. **Learn** — a gamified A-Z curriculum (lesson path, XP, streaks, hearts, achievements, quizzes, and camera-based "show the sign" challenges) that reuses the **same** recognition model as module 1.

See `ml/MODEL_CARD.md` for the actual, honestly-measured accuracy of the trained model (not invented), `ml/DATA_CARD.md` for dataset provenance, and `ARCHITECTURE.md` for how the pieces fit together.

## Stack

| Layer | Choice |
|---|---|
| Frontend | React 19 + TypeScript + Vite 5 + Tailwind CSS 4 |
| Backend | FastAPI (Python) |
| Database | SQLite (dev, zero-setup) / PostgreSQL (via `docker-compose.yml`), SQLAlchemy + Alembic migrations |
| Auth | JWT (python-jose) + bcrypt |
| ML | MediaPipe HandLandmarker (pretrained hand-pose detector) + a scikit-learn classifier trained from scratch on real data |

Why this stack is explained in-line in `ARCHITECTURE.md`.

## Repository layout

```
backend/    FastAPI app, SQLAlchemy models, Alembic migrations, tests
frontend/   React + TypeScript + Vite app
ml/         Dataset download, preprocessing, training, evaluation, model artifacts
docker-compose.yml, backend/Dockerfile, frontend/Dockerfile
```

## Prerequisites

- Python 3.13 (a virtualenv is used; see below)
- Node.js 20+
- No GPU required — the ML pipeline runs on CPU by design (see MODEL_CARD.md)

## Setup & run (local, no Docker)

### 1. ML pipeline — train the recognition model first

The backend won't have a working `/api/recognition/predict` until this has been run once (it degrades gracefully otherwise — see Known Limitations).

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.lock.txt   # exact, verified-working versions
# (requirements.txt lists the same deps with looser pins, if you prefer)

cd ../ml/scripts
python download_dataset.py          # ~74 MB, HuggingFace, no auth needed
python download_hand_landmarker.py  # ~8 MB, Google's pretrained model
python extract_landmarks.py         # ~3-4 minutes on CPU
python train.py                     # ~1-2 minutes on CPU
```

This produces `ml/models/asl_landmark_classifier.joblib`, `ml/reports/metrics.json`, `ml/reports/confusion_matrix.png`, and `ml/models/reference_landmarks.json` — all real outputs of the run, nothing pre-generated or faked.

### 2. Backend

```bash
cd backend
# (venv already active from step 1)
copy ..\.env.example .env      # Windows
# cp ../.env.example .env      # macOS/Linux
alembic upgrade head
python -m app.seed             # idempotent: seeds the 26-letter curriculum + achievements
uvicorn app.main:app --reload --port 8000
```

Backend runs at `http://localhost:8000`. Interactive API docs: `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173` and proxies `/api/*` to `http://127.0.0.1:8000` (see `frontend/vite.config.ts`).

Open `http://localhost:5173`, sign up, and use the app.

## Tests

```bash
cd backend
python -m pytest tests/ -v
```

18 tests covering auth (including a bcrypt-72-byte-limit regression test), lesson progression/unlocking/XP/achievements, interpretation (sign vs. fingerspell distinction), and the landmark normalization math shared between training and inference.

## Docker (best-effort — see Known Limitations)

```bash
docker compose up --build
```

Opens the app at `http://localhost:8080` with Postgres instead of SQLite. **This was written but could not be build-tested** in the environment this repo was created in, because Docker Desktop's engine wasn't running there (only the CLI was available). Review the Dockerfiles before relying on this path.

## Known limitations (see also ml/MODEL_CARD.md)

- **Recognition accuracy is measured, not assumed**: 85.7% on a held-out test set of 77 images from the *same* source dataset (95% CI: 76.2%-91.8%). Real-world webcam accuracy on a different camera/lighting/hand has not been measured and is likely lower — treat live recognition as a genuine, working demonstration, not a validated production recognizer.
- Interpretation module's whole-word sign dictionary is a small (30-word), hand-curated reference set, not a certified ASL dictionary, and does not produce grammatical ASL (see the in-app disclaimer, sourced from `backend/app/api/interpretation.py`).
- Sign cards / fingerspelling visuals are SVG hand-skeletons rendered from real per-letter landmark data computed by the training pipeline (`ml/models/reference_landmarks.json`) — not stock photos or hand-drawn art, because the training dataset's license doesn't permit redistributing its images.
- Docker Compose is untested end-to-end (see above).
- UI was verified via the built production bundle, TypeScript compilation, and direct HTTP testing of every endpoint the frontend calls (through the same dev-server proxy path the browser uses) — not via an interactive browser session, since no browser automation tool was available in the development environment. See the final report in the conversation for exactly what was and wasn't exercised.
