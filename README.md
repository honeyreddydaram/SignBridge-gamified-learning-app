# SignBridge

An AI-powered ASL (American Sign Language) accessibility platform that pairs real-time fingerspelling recognition with a mastery-based, gamified learning curriculum.

## Why SignBridge?

Most "ASL apps" are either a static dictionary (look up a word, see a picture) or a single demo model with no path from *seeing* a sign to actually *knowing* it. SignBridge tries to close that gap: a real computer-vision recognizer gives learners honest feedback instead of just a video to imitate, real signer video (not stock photos or synthetic avatars) sources every sign that's taught, and progress is tracked as a mastery state per word rather than a single "lesson complete" checkbox — so the app reflects what a learner actually retains over time, not just what they clicked through once. It's built to be useful both as a communication aid (Interpretation) and as a genuine learning tool (Learn), while being explicit about where the underlying ML does and doesn't reach — see [Known limitations](#known-limitations).

## Demo — See SignBridge in Action

Real screen recordings of the running app — not mockups, not staged renders.

### Learning — Learn & Practice ASL

The project's main differentiator: a mastery-based, gamified curriculum (Learn → Recognize → Produce → Recall → Master, Sign Quests, XP/streaks/hearts) rather than a single demo model. See [Gamified Learning](#gamified-learning) below for the full mechanics.

<video controls poster="docs/demos/posters/learning.jpg" src="docs/demos/learning.mp4" width="760">
Your browser doesn't support embedded video — <a href="docs/demos/learning.mp4">download the recording</a> directly.
</video>

### Recognition — Sign → Text

Live webcam A-Z fingerspelling recognition. See [Known limitations](#known-limitations) for what the accuracy numbers do and don't cover.

<video controls poster="docs/demos/posters/recognition.jpg" src="docs/demos/recognition.mp4" width="480">
Your browser doesn't support embedded video — <a href="docs/demos/recognition.mp4">download the recording</a> directly.
</video>

### Interpretation — Text → Sign

Typed English playing back as sign video for supported vocabulary, fingerspelling as the fallback — a communication aid, not full grammatical ASL translation.

<video controls poster="docs/demos/posters/interpretation.jpg" src="docs/demos/interpretation.mp4" width="480">
Your browser doesn't support embedded video — <a href="docs/demos/interpretation.mp4">download the recording</a> directly.
</video>

## The three modules

1. **Recognition** — real webcam ASL fingerspelling recognition (A-Z), backed by a landmark-based classifier trained on real data (see `ml/`). See `ml/MODEL_CARD.md` for the actual, honestly-measured accuracy (not invented).
2. **Interpretation** — a *communication* tool: type English, see it play back immediately as a short looping ASL sign clip (real video of an actual signer), with A-Z fingerspelling as the fallback for anything without a clean dedicated clip. This is supported-vocabulary communication, **not** full grammatical ASL translation. Full sourcing detail and the 18/114-word distinction are in [Data & media sourcing](#data--media-sourcing).
3. **Learn** — a gamified, mastery-based curriculum with two independently-unlocking tracks: the A-Z alphabet, and 10 vocabulary categories covering all 114 verified words. This is the heart of the project — see the next section.

See `ARCHITECTURE.md` for how the pieces fit together, and `ml/DATA_CARD.md` for training-data provenance.

## Gamified Learning

Learning in SignBridge isn't "watch a video once, mark it done." Every vocabulary word moves through its own mastery state machine, reinforced through short quests and situational scenarios, all wrapped in shared XP/streak/hearts/achievement systems.

### The mastery loop: Learn → Recognize → Produce → Recall → Master

Each vocabulary word (`backend/app/services/mastery_service.py`, `UserSignMastery` table) progresses through:

```
New -> Learning -> Practicing -> Mastered
```

- **Learn**: real verified video + description (`vocab_video_card`)
- **Recognize**: a real graded multiple-choice quiz — "which sign means X?" (`vocab_comprehension_mcq`) — objectively scored, feeds mastery for real
- **Produce**: "your turn" — camera opens, the learner signs it (`vocab_produce_selfcheck`)
- **Recall**: on a later visit, once a word reaches Practicing, the same lesson presents it recall-only — no demo shown first, testing memory rather than imitation (`vocab_recall_selfcheck`)
- **Master**: requires a successful Recall self-check occurring on a *different calendar day* than earlier interactions with that word — a single sitting cannot master a word by itself, however many times you click through it. Mastered is sticky (never downgrades).

This is deliberate: a word "seen once" and a word actually *retained* are different things, and only the latter should count as mastered.

### Model-graded vs. self-checked — and why

**A-Z camera challenges in the alphabet track are graded by the trained recognition model** (the same classifier described in Recognition, above). **Produce, Recall, quest, and scenario camera steps for vocabulary are self-checked** — the learner's own camera feed, with the learner (not the model) marking whether they got it right, always visibly labeled as a self-check (`SelfCheckCamera.tsx`). This isn't a UI shortcut: the trained model only classifies static A-Z fingerspelling handshapes from a single frame and was never trained on, and cannot validate, dynamic multi-frame word-level signs like HELLO. Full detail is in [Known limitations](#known-limitations). Self-checked XP is deliberately smaller than graded XP (Recognize quiz, lesson completion, mastery milestones, quest completion) — see `xp_per_selfcheck` vs. `xp_per_correct_answer` in `backend/app/config.py`.

### Sign Quests & scenarios

**Sign Quests** (`backend/app/quests.py`, `Quest`/`UserQuestProgress` tables) are short reinforcement missions over vocabulary already taught elsewhere — not a new teaching unit, so they're a separate architecture from `Lesson`. Two quest types share one system:
- **mission** — a checklist (e.g. Greetings Quest: HELLO ✓ / PLEASE ✓ / THANK YOU ☐), one camera self-check per word.
- **scenario** — a short situational prompt expecting one concept (e.g. "You meet someone for the first time — how would you greet them?" → HELLO).

New quests are added as data in `QUEST_DEFS`, not new screens — the API and UI are entirely generic over the list.

### XP, streaks, hearts, achievements

Both tracks (alphabet and vocabulary) and quests share one gamification layer: XP and levels, daily streaks, hearts, and achievements. **Streaks stay separate from mastery on purpose**: missing a day resets `current_streak` but never touches `UserSignMastery` — mastery progress only ever accumulates, so a broken streak doesn't erase what's actually been learned. A visual **ASL Journey** map shows real progress across Alphabet → Greetings → Family → ... (the actual unlocked/locked/complete state from lesson data, not a simulated progress bar).

## Architecture & stack

| Layer | Choice |
|---|---|
| Frontend | React 19 + TypeScript + Vite 5 + Tailwind CSS 4 |
| Backend | FastAPI (Python) |
| Database | SQLite (dev, zero-setup) / PostgreSQL (via `docker-compose.yml`), SQLAlchemy + Alembic migrations |
| Auth | JWT (python-jose) + bcrypt |
| ML | MediaPipe HandLandmarker (pretrained hand-pose detector) + a scikit-learn classifier trained from scratch on real data |

Why this stack is explained in-line in `ARCHITECTURE.md`.

### Repository layout

```
backend/    FastAPI app, SQLAlchemy models, Alembic migrations, tests
frontend/   React + TypeScript + Vite app
ml/         Dataset download, preprocessing, training, evaluation, model artifacts
docker-compose.yml, backend/Dockerfile, frontend/Dockerfile
```

## Setup, testing & reproducibility

### Prerequisites

- Python 3.13 (a virtualenv is used; see below)
- Node.js 20+
- No GPU required — the ML pipeline runs on CPU by design (see `ml/MODEL_CARD.md`)

### 1. ML pipeline — train the recognition model first

The backend won't have a working `/api/recognition/predict` until this has been run once (it degrades gracefully otherwise — see Known limitations).

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

### Tests

```bash
cd backend
python -m pytest tests/ -v
```

49 tests covering auth (including a bcrypt-72-byte-limit regression test), lesson progression/unlocking/XP/achievements for both tracks (including a regression test that vocabulary completions don't accidentally trigger the alphabet-specific achievement), the mastery state machine (including "can't master a word in one sitting" as an explicit test), Sign Quests, interpretation's communication-mode restriction (dedicated-video words play, compilation-video words fingerspell), and the landmark normalization math shared between training and inference.

### Docker (best-effort — see Known limitations)

```bash
docker compose up --build
```

Opens the app at `http://localhost:8080` with Postgres instead of SQLite. **This was written but could not be build-tested** in the environment this repo was created in, because Docker Desktop's engine wasn't running there (only the CLI was available). Review the Dockerfiles before relying on this path.

## Data & media sourcing

### The 114-word vocabulary manifest — one dataset, two playback modes

`ml/word_signs_verified.json` holds 114 words, each with a real YouTube video of an actual signer performing that sign. Every entry was individually verified via YouTube's oEmbed endpoint (not guessed) — full sourcing rationale, per-channel breakdown, and the list of words considered but left out (rather than padded with a lower-confidence guess) is in `ml/word_signs_research_report.md`. Lifeprint/ASL University was deliberately excluded: their site explicitly prohibits embedding their material.

This single manifest (`backend/app/asl_signs.py`, not duplicated) backs both:
- **Learning's vocabulary lessons** — all 114 words, full context (description, source attribution, replay controls), grouped into 10 thematic categories.
- **Interpretation's communication mode** — only the 18 words whose video is dedicated to just that one sign (`is_dedicated_video`, computed at load time from how many words share a `video_id`). The other 96 are backed by compilation videos (e.g. one "Colors" video covers all 10 colors) that can't be cleanly looped to show a single sign without showing its neighbors too — wrong for a communication tool, fine for a teaching one. Those 96 words fingerspell in Interpretation but still have full video in Learning.

### Interpretation's media-source limitation (researched, not assumed)

Before redesigning Interpretation as a "type it, watch it play instantly" communication tool, we looked for a source of short, cleanly-licensed single-sign clips that could cover more than 18 words — specifically one whose license permits redistribution or looped derivative use (not just linking/embedding, which the 114-word YouTube manifest already has). We checked:
- **Wikimedia Commons**: has ASL alphabet/fingerspelling charts under CC/PD licenses, but no individual word-level sign videos with real license metadata.
- **Government sources**: the FCC's ASL Video Library exists but covers FCC-service topics, not general vocabulary — no applicable federal ASL dictionary found.
- **Commercial ASL dictionaries** (SigningSavvy, SignASL.org, etc.): broad word coverage, but no license grant permitting redistribution or app use — same restriction category as Lifeprint.

**No redistributable source with meaningful coverage was found.** This is a real, researched gap, not an assumption. Given that, Interpretation uses the existing legitimately-embedded YouTube manifest, restricted to the subset (18/114 words) where looping doesn't show extraneous signs, rather than using a lower-quality or license-uncertain asset just to raise the count.

A word only gets a video in either module if it has a verified entry — nothing is shown on a guess. `backend/tests/test_word_signs_data.py` validates the manifest's structure on every test run (no live network calls in CI; the actual video links were verified manually — see the research report).

## Known limitations

(see also `ml/MODEL_CARD.md`)

- **Recognition accuracy is measured, not assumed**: 85.7% on a held-out test set of 77 images from the *same* source dataset (95% CI: 76.2%-91.8%). Real-world webcam accuracy on a different camera/lighting/hand has not been measured and is likely lower — treat live recognition as a genuine, working demonstration, not a validated production recognizer.
- Interpretation's communication mode covers 18/114 words with clean single-sign video; the rest fingerspell there (see above) even though all 114 have full video in Learning.
- Neither module produces grammatical ASL (see the in-app disclaimer, sourced from `backend/app/api/interpretation.py`) — this is a fingerspelling/vocabulary aid, not a translator.
- **Vocabulary/quest/scenario camera steps have no recognition-graded validation** (unlike the alphabet track). The trained recognition model only classifies static A-Z fingerspelling handshapes from a single frame (confirmed by directly inspecting the trained model file — its label encoder has exactly 26 classes, `A`-`Z`) — it was never trained on, and structurally cannot validate, dynamic multi-frame word-level signs like HELLO. Every Produce/Recall/quest/scenario camera step is instead **self-checked**: the learner's own camera feed, and the learner (not the model) marks whether they got it right, always visibly labeled as a self-check (`SelfCheckCamera.tsx`) rather than fabricating a validation capability the model doesn't have. See `backend/app/services/mastery_service.py`'s module docstring.
- Mastery state is per-word and never downgrades once Mastered — an honest self-report of "need more practice" after mastery doesn't revoke it. This is a deliberate simplicity trade-off (documented in `mastery_service.py`), not an oversight.
- A few Learning-module source videos are compilations reused across several related words (e.g. one "Colors" video backs all 10 color entries) — noted per-entry in `ml/word_signs_verified.json`'s `notes` field, and flagged as a maintenance risk (single point of failure if a compilation video is taken down) in `ml/word_signs_research_report.md`.
- Sign cards / fingerspelling visuals are SVG hand-skeletons rendered from real per-letter landmark data computed by the training pipeline (`ml/models/reference_landmarks.json`) — not stock photos or hand-drawn art, because the training dataset's license doesn't permit redistributing its images.
- Docker Compose is untested end-to-end (see above).
- UI was verified via the built production bundle, TypeScript compilation, and direct HTTP testing of every endpoint the frontend calls (through the same dev-server proxy path the browser uses) — not via an interactive browser session, since no browser automation tool was available in the development environment.
