# SignBridge

A full-stack ASL (American Sign Language) accessibility and learning app with three integrated modules:

1. **Recognition** — real webcam ASL fingerspelling recognition (A-Z), backed by a landmark-based classifier trained on real data (see `ml/`).
2. **Interpretation** — a *communication* tool: type English, see it play back immediately as short looping ASL sign clips (real video of an actual signer, autoplaying/looping, minimal UI), with A-Z fingerspelling as the fallback for anything else. Only 18 of the 114 verified words have a video dedicated to just that one sign (safe to loop cleanly) — those are what Interpretation shows; the rest fingerspell here even though they're supported for teaching in Learning (see below). Clearly distinguished from full grammatical ASL translation, which this app does **not** claim to do.
3. **Learn** — a gamified curriculum with two independently-unlocking tracks: the A-Z alphabet (lesson path, quizzes, camera challenges validated by the recognition model), and 10 vocabulary categories covering all 114 verified words (real video + description + source attribution + replay controls + comprehension quiz + ungraded camera self-practice per category). Both tracks share XP, streaks, hearts, and achievements. Camera challenges are alphabet-only — see Known Limitations for why.

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
python -m app.seed             # idempotent: seeds both lesson tracks (26 letters + 10 vocab categories) + achievements
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

31 tests covering auth (including a bcrypt-72-byte-limit regression test), lesson progression/unlocking/XP/achievements for both tracks (including a regression test that vocabulary completions don't accidentally trigger the alphabet-specific achievement), interpretation's communication-mode restriction (dedicated-video words play, compilation-video words fingerspell), and the landmark normalization math shared between training and inference.

## Docker (best-effort — see Known Limitations)

```bash
docker compose up --build
```

Opens the app at `http://localhost:8080` with Postgres instead of SQLite. **This was written but could not be build-tested** in the environment this repo was created in, because Docker Desktop's engine wasn't running there (only the CLI was available). Review the Dockerfiles before relying on this path.

## The 114-word vocabulary manifest — one dataset, two playback modes

`ml/word_signs_verified.json` holds 114 words, each with a real YouTube video of an actual signer performing that sign. Every entry was individually verified via YouTube's oEmbed endpoint (not guessed) — full sourcing rationale, per-channel breakdown, and the list of words considered but left out (rather than padded with a lower-confidence guess) is in `ml/word_signs_research_report.md`. Lifeprint/ASL University was deliberately excluded: their site explicitly prohibits embedding their material.

This single manifest (`backend/app/asl_signs.py`, not duplicated) backs both:
- **Learning's vocabulary lessons** — all 114 words, full context (description, source attribution, replay controls), grouped into 10 thematic categories.
- **Interpretation's communication mode** — only the 18 words whose video is dedicated to just that one sign (`is_dedicated_video`, computed at load time from how many words share a `video_id`). The other 96 are backed by compilation videos (e.g. one "Colors" video covers all 10 colors) that can't be cleanly looped to show a single sign without showing its neighbors too — wrong for a communication tool, fine for a teaching one. Those 96 words fingerspell in Interpretation but still have full video in Learning.

## Interpretation's media-source limitation (researched, not assumed)

Before redesigning Interpretation as a "type it, watch it play instantly" communication tool, we looked for a source of short, cleanly-licensed single-sign clips that could cover more than 18 words — specifically one whose license permits redistribution or looped derivative use (not just linking/embedding, which the 114-word YouTube manifest already has). We checked:
- **Wikimedia Commons**: has ASL alphabet/fingerspelling charts under CC/PD licenses, but no individual word-level sign videos with real license metadata.
- **Government sources**: the FCC's ASL Video Library exists but covers FCC-service topics, not general vocabulary — no applicable federal ASL dictionary found.
- **Commercial ASL dictionaries** (SigningSavvy, SignASL.org, etc.): broad word coverage, but no license grant permitting redistribution or app use — same restriction category as Lifeprint.

**No redistributable source with meaningful coverage was found.** This is a real, researched gap, not an assumption — see the fork research summarized in this project's conversation history. Given that, Interpretation uses the existing legitimately-embedded YouTube manifest, restricted to the subset (18/114 words) where looping doesn't show extraneous signs, rather than using a lower-quality or license-uncertain asset just to raise the count.

A word only gets a video in either module if it has a verified entry — nothing is shown on a guess. `backend/tests/test_word_signs_data.py` validates the manifest's structure on every test run (no live network calls in CI; the actual video links were verified manually — see the research report).

## Known limitations (see also ml/MODEL_CARD.md)

- **Recognition accuracy is measured, not assumed**: 85.7% on a held-out test set of 77 images from the *same* source dataset (95% CI: 76.2%-91.8%). Real-world webcam accuracy on a different camera/lighting/hand has not been measured and is likely lower — treat live recognition as a genuine, working demonstration, not a validated production recognizer.
- Interpretation's communication mode covers 18/114 words with clean single-sign video; the rest fingerspell there (see above) even though all 114 have full video in Learning.
- Neither module produces grammatical ASL (see the in-app disclaimer, sourced from `backend/app/api/interpretation.py`) — this is a fingerspelling/vocabulary aid, not a translator.
- **Vocabulary lessons have no recognition-graded camera challenge** (unlike the alphabet track). The trained recognition model only classifies static A-Z fingerspelling handshapes from a single frame — it was never trained on, and cannot validate, dynamic multi-frame word-level signs like HELLO. Vocabulary lessons instead end with an ungraded "mirror practice" step (learner's own camera feed, self-directed, explicitly not auto-graded) rather than fabricating a validation capability the model doesn't have. See `backend/app/curriculum.py`'s `generate_vocabulary_exercises` docstring.
- A few Learning-module source videos are compilations reused across several related words (e.g. one "Colors" video backs all 10 color entries) — noted per-entry in `ml/word_signs_verified.json`'s `notes` field, and flagged as a maintenance risk (single point of failure if a compilation video is taken down) in `ml/word_signs_research_report.md`.
- Sign cards / fingerspelling visuals are SVG hand-skeletons rendered from real per-letter landmark data computed by the training pipeline (`ml/models/reference_landmarks.json`) — not stock photos or hand-drawn art, because the training dataset's license doesn't permit redistributing its images.
- Docker Compose is untested end-to-end (see above).
- UI was verified via the built production bundle, TypeScript compilation, and direct HTTP testing of every endpoint the frontend calls (through the same dev-server proxy path the browser uses) — not via an interactive browser session, since no browser automation tool was available in the development environment.
