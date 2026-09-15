# Architecture

## Why this stack

- **FastAPI backend in Python**: the ML pipeline (MediaPipe + scikit-learn) is Python. Putting the API in Python too means the trained model loads once, in-process, as a singleton service (`backend/app/services/recognition_service.py`) — and that exact same service backs both the standalone Recognition module and the camera-based Learning challenges, satisfying the "one shared recognition model, not two systems" requirement directly rather than via a second inference service or a network hop to a separate ML microservice.
- **React + TypeScript + Vite frontend**: component model suits a gamified lesson UI (cards, quizzes, progress bars); `getUserMedia` + `<canvas>` gives direct webcam frame access; Vite's dev proxy makes local dev trivial (see `frontend/vite.config.ts`).
- **SQLite for local dev, Postgres via docker-compose**: the development environment this was built in had Docker Desktop's CLI but not its running engine — SQLite keeps the app fully runnable today without depending on that, while the SQLAlchemy models and Alembic migrations are dialect-agnostic and already used unmodified against Postgres in `docker-compose.yml`.
- **MediaPipe HandLandmarker + a from-scratch classifier, not a raw-pixel CNN**: real-time ASL fingerspelling systems commonly use hand-landmark features rather than pixel CNNs because (a) it's CPU-trainable in minutes instead of hours, (b) it's more robust to background/lighting than raw pixels, and (c) landmark features are naturally translation/scale invariant with simple normalization. This machine has no GPU, which made this the practical as well as the technically sound choice. See `ml/MODEL_CARD.md` for the actual accuracy this achieved.

## Request flow

```
Browser (React)
  │  getUserMedia → <canvas> → base64 JPEG frame, every ~350ms
  ▼
POST /api/recognition/predict  { image_base64, target_letter? }
  │
  ▼
FastAPI (backend/app/api/recognition.py)
  │  decode image → RecognitionService.predict()
  ▼
RecognitionService (backend/app/services/recognition_service.py)
  │  1. MediaPipe HandLandmarker → 21 (x,y,z) landmarks
  │  2. landmark_utils.landmarks_to_feature_vector() → 63-dim normalized vector
  │     (SAME function imported from ml/scripts/landmark_utils.py — not reimplemented)
  │  3. trained sklearn classifier .predict_proba() → letter + confidence
  ▼
Response { hand_detected, predicted_letter, confidence, is_confident, correct? }
  │
  ▼
Frontend: useStablePrediction hook (frontend/src/hooks/useStablePrediction.ts)
  │  rolling 6-frame majority vote, confidence gating, "release before repeat" debounce
  ▼
Confirmed letter → appended to Recognition module's text, or graded against
a Learning-module camera challenge's target letter (same hook, same endpoint).
```

## Why feature extraction is shared, not duplicated

`ml/scripts/landmark_utils.py` contains one function, `landmarks_to_feature_vector`, imported directly (via `sys.path` insertion) by BOTH:
- `ml/scripts/extract_landmarks.py` / `train.py` at training time, and
- `backend/app/services/recognition_service.py` at inference time.

If these two normalization steps ever drifted apart, the model would silently see differently-shaped features at inference than it was trained on — a classic, hard-to-detect ML bug. Importing the same module instead of reimplementing the math twice makes that class of bug structurally impossible rather than something to remember to keep in sync.

## Temporal smoothing (frontend/src/hooks/useStablePrediction.ts)

The backend's `/predict` endpoint is deliberately **stateless per call** — it scores one frame and returns. All temporal logic (the spec's "smooth across frames", "reject uncertain predictions", "don't repeat a held sign") lives in one frontend hook, shared by both the Recognition page and `CameraChallenge` component, rather than duplicated per screen or pushed into stateful backend session tracking (which would need per-user server-side state for no real benefit — the frontend already knows its own frame cadence).

State machine per poll tick:
1. Capture a frame, call `/predict`.
2. Push the result into a 6-frame rolling buffer (`null` if the backend didn't mark it confident).
3. If a letter has a majority (≥4/6) in the buffer AND it's not the same letter already "held": fire `onConfirmed(letter)`, remember it as held.
4. If the current frame doesn't match the held letter for 3 consecutive polls (hand removed, or sign changed away), release the hold — the same letter can fire again.

## Database schema (backend/app/models/)

- `users` — auth + all gamification state that's naturally 1:1 with a user (xp_total, level, hearts, streak) rather than split into a separate table joined on every request.
- `lessons` — static, seeded curriculum (26 rows, one per letter).
- `user_lesson_progress` — per-user status (locked/unlocked/completed), best score, attempts.
- `xp_transactions` — append-only ledger of XP awards (auditable; `xp_total` is derivable from summing this).
- `achievements` / `user_achievements` — static badge catalog + per-user earned join table.
- `practice_attempts` — logs directed camera-challenge recognition attempts (both the standalone module's free practice doesn't log every idle frame, only graded challenge attempts, to avoid flooding this table).

Migrations: `backend/alembic/` — one initial migration generated via `alembic revision --autogenerate` against these models, applied with `alembic upgrade head`.

## Curriculum & exercise generation (backend/app/curriculum.py)

Lesson content (26 hand-authored handshape descriptions) and exercise generation (MCQ distractor selection, seeded deterministically per letter so the exercise set is stable across requests) live in one module, imported by the lessons API. Quiz "sign cards" are rendered client-side from `ml/models/reference_landmarks.json` (see below) rather than authored as separate quiz assets, so there's one source of truth for what each letter's sign looks like.

## Sign visuals (frontend/src/components/HandSkeleton.tsx)

The training dataset's license doesn't permit redistributing its images, so sign cards and the fingerspelling animation in the Interpretation module can't use dataset photos, and hand-drawing 26 illustrations was out of scope. Instead, `ml/scripts/train.py::compute_reference_landmarks` picks a representative real photo per letter (closest to that letter's feature centroid) and stores its **landmark coordinates** (not the image) in `reference_landmarks.json`. The frontend renders these as an SVG hand-skeleton using MediaPipe's standard 21-point connection topology — real, derived-from-data visuals with no licensing issue and no fabrication.

## What's NOT implemented (by design, and disclosed to the user in-app)

- Full grammatical ASL translation (ASL grammar, non-manual markers, classifiers) — explicitly out of scope and disclaimed in the Interpretation module's UI and API response (`is_full_grammatical_asl: false` + a visible disclaimer banner).
- Two-handed signs, facial expression, or non-alphabet ASL vocabulary beyond the curated 30-word dictionary.
