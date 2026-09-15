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
- `lessons` — two independently-unlocking tracks share this table: `lesson_type` (`alphabet` | `vocabulary`) discriminates them, `order_index` is unique only *within* a lesson_type (`uq_lesson_type_order`, not globally) so each track numbers its own lessons starting at 1 and unlocks independently — finishing the alphabet is not a prerequisite for starting vocabulary. Alphabet rows use `letter`; vocabulary rows use `concept_key` (a category slug, e.g. `greetings_courtesy`) instead.
- `user_lesson_progress` — per-user status (locked/unlocked/completed), best score, attempts. Same shape for both tracks.
- `xp_transactions` — append-only ledger of XP awards (auditable; `xp_total` is derivable from summing this).
- `achievements` / `user_achievements` — static badge catalog + per-user earned join table. Achievement checks that count "completed lessons" are scoped by `lesson_type` where it matters (e.g. `alphabet_complete` requires 26 completed *alphabet* lessons specifically, not 26 completed lessons of any mix — see `gamification_service.check_and_grant_achievements`, which had exactly this bug during development and was caught by `test_alphabet_complete_achievement_not_triggered_by_vocabulary_completions`).
- `practice_attempts` — logs directed camera-challenge recognition attempts (alphabet track only — see below for why vocabulary lessons don't have these).

Migrations: `backend/alembic/` — applied with `alembic upgrade head`. The vocabulary-track migration (`6ff7d2d89b6b`) uses SQLite batch-recreate mode with an explicit `copy_from` table definition rather than autogenerate's raw output, because SQLite can't drop an unnamed UNIQUE constraint in place (the original `order_index unique=True`) any other way — worth knowing if you add another schema change to this table.

## Curriculum & exercise generation (backend/app/curriculum.py)

Two independent exercise generators, one per track, both imported by the lessons API and dispatched on `lesson.lesson_type`:
- `generate_lesson_exercises` (alphabet): 26 hand-authored handshape descriptions; MCQ distractors seeded deterministically per letter. Ends with a recognition-model-graded `camera_challenge`.
- `generate_vocabulary_exercises` (vocabulary): built from `VOCABULARY_CATEGORIES` (10 thematic groups covering all 114 words in `ml/word_signs_verified.json`, validated at call time by `get_vocabulary_categories()` — it raises loudly if a category references a word missing from the manifest, rather than silently generating a broken lesson). **State-aware per word**, branched on the caller-supplied `mastery_by_word` map (populated by `lessons.py` from `UserSignMastery`): a word at `new`/`learning` gets the full `vocab_video_card` (Learn) -> `vocab_comprehension_mcq` (Recognize) -> `vocab_produce_selfcheck` (Produce) sequence; a word already at `practicing` gets `vocab_recall_selfcheck` only — no demo re-shown, since Recall specifically tests memory, not imitation; a word at `mastered` is skipped (falls back to a full Recall pass if literally every word in the category is already mastered, so a lesson is never empty).

**Why Produce/Recall aren't recognition-graded**: the trained recognition model (`ml/models/asl_landmark_classifier.joblib`) only classifies static A-Z fingerspelling handshapes from a single frame — confirmed by directly inspecting the trained model file (`label_encoder.classes_` is exactly `['A'..'Z']`) rather than assumed. It was never trained on, and structurally cannot validate, dynamic multi-frame word-level signs like HELLO or THANK YOU. Claiming to auto-grade those would be exactly the fabricated-working-feature this project rules out elsewhere. `vocab_produce_selfcheck`/`vocab_recall_selfcheck` (rendered by `frontend/src/components/SelfCheckCamera.tsx`) instead give the learner their own camera feed and let THEM mark whether they got it right — always visibly labeled as a self-check, never presented as model output. Sign Quests and scenarios (below) follow the identical rule.

## Vocabulary mastery loop (backend/app/services/mastery_service.py, models/mastery.py)

`UserSignMastery` (one row per user per word) tracks a simple, documented state machine: `new -> learning -> practicing -> mastered`, driven by `record_sign_interaction(db, user, word, interaction_type, correct=None)` — called from `api/vocabulary.py`'s `/interaction` endpoint (Learn/Recognize/Produce) and from `api/quests.py` (quest/scenario steps feed it as `recall_selfcheck`, since a quest is blind reinforcement of already-taught vocabulary, not a first teaching pass).

State thresholds (all in `mastery_service.py`, kept deliberately simple):
- `learning`: any first interaction
- `practicing`: `recognize_correct_count >= 2` AND `produce_selfcheck_count >= 1`
- `mastered`: a successful `recall_selfcheck` AND `distinct_days_interacted >= 2` — the distinct-day requirement is what stops a learner from mastering a word by clicking through Learn->Recognize->Produce->Recall in one sitting; a real return visit is required. `mastered` is sticky (never downgrades) once reached, a deliberate simplicity trade-off.

XP is asymmetric by design (per-request): `recognize` (a real graded MCQ answer) earns full `xp_per_correct_answer`; `produce_selfcheck`/`recall_selfcheck` (self-reports) earn the smaller `xp_per_selfcheck`; reaching `mastered` earns a one-time `xp_per_sign_mastered` bonus. Streaks (`User.current_streak`) are untouched by mastery logic in the other direction too — missing a day resets the streak counter but never touches `UserSignMastery`, so mastery progress only accumulates.

## Sign Quests (backend/app/quests.py, models/mastery.py's Quest/UserQuestProgress)

Deliberately a separate architecture from `Lesson`, not a third `lesson_type` — a quest is a reinforcement mission over vocabulary already taught elsewhere, not a new teaching unit. `QUEST_DEFS` (a plain Python list, same data-driven pattern as `VOCABULARY_CATEGORIES`) defines each quest's `type` (`mission`: a word checklist, e.g. Greetings Quest; or `scenario`: a situational prompt expecting one concept, e.g. "you meet someone for the first time" -> HELLO), `words` (validated against `SUPPORTED_SIGNS` at call time, same fail-loudly pattern as vocabulary categories), and for scenarios a `prompt` string. `Quest.words_json` stores the word list as JSON rather than a join table — quests are small, static, ordered lists, not a relation needing independent querying. `quest_service.record_quest_step` only advances the checklist on a correct self-report (an honest "need more practice" doesn't fake progress) and awards the one-time quest-completion XP bonus separately from the per-word mastery XP awarded by the `/interaction`-equivalent call in `api/quests.py` (these were originally double-counted during development — the fix and reasoning are left as a comment in `quest_service.py`).

## Sign visuals (frontend/src/components/HandSkeleton.tsx)

The alphabet training dataset's license doesn't permit redistributing its images, so A-Z sign cards and fingerspelling can't use dataset photos, and hand-drawing 26 illustrations was out of scope. Instead, `ml/scripts/train.py::compute_reference_landmarks` picks a representative real photo per letter (closest to that letter's feature centroid) and stores its **landmark coordinates** (not the image) in `reference_landmarks.json`. The frontend renders these as an SVG hand-skeleton using MediaPipe's standard 21-point connection topology — real, derived-from-data visuals with no licensing issue and no fabrication. (Whole-word vocabulary signs use real video instead — see below — since they're dynamic, multi-frame signs a static landmark pose can't represent.)

## Word-level sign video: one manifest, two playback modes (backend/app/asl_signs.py)

`ml/word_signs_verified.json` holds 114 entries, each individually verified by calling YouTube's oEmbed endpoint and confirming a real, embeddable video exists and matches the word — see `ml/word_signs_research_report.md` for the full sourcing methodology, including why Lifeprint/ASL University was excluded (their site explicitly prohibits embedding their material) in favor of YouTube's own embed mechanism against reputable ASL-education channels. `backend/app/asl_signs.py` loads this file once into a `WordSign` record per word and is the single source of truth both consumers below import from — the manifest is not duplicated anywhere.

This one dataset serves two different UX needs with different constraints:

- **Learning module (curriculum.py)**: uses all 114 words with full context — description, source attribution, replay controls. A shared/compilation video (e.g. one video covering all 10 colors) is fine here; seeing neighboring vocabulary is a teaching feature, not a bug.
- **Interpretation module (interpretation.py)**: redesigned as a communication tool — type English, watch it play immediately as a short looping clip, no teaching chrome. This is where compilation videos become a real problem: looping the *whole* video to "say" one word would visibly show unrelated signs too. So `_is_communication_ready()` restricts Interpretation's "sign" segments to words where `WordSign.is_dedicated_video` is True — computed at load time by counting how many words share each `video_id`; only words whose video belongs to them alone qualify. That's 18 of the 114 words today; the other 96 fingerspell in Interpretation specifically, while remaining fully supported (with video) in Learning. `SignVideo.loop_embed_url` adds YouTube's `loop=1&playlist=<same id>&autoplay=1&mute=1&controls=0` params (a real quirk: `loop=1` alone doesn't loop a single video without the matching `playlist` param) for the clean, chrome-free autoplay Interpretation needs; Learning's `ReplayableVideo` component uses the plain `embed_url` with visible controls and an explicit Replay button instead, since deliberate pacing is a teaching feature there.

Before settling on this 18-word restriction as the final answer, a research pass specifically looked for a legitimately redistributable source of short single-sign clips (to avoid the compilation-video problem entirely) — checked Wikimedia Commons, U.S. government sources, and commercial ASL dictionaries. None offered meaningful word-level coverage under a license that actually permits redistribution or looped derivative use (commercial dictionaries have broad coverage but no such license — the same restriction category Lifeprint was already excluded for). See `README.md`'s "Interpretation's media-source limitation" for the full writeup — this is a documented, researched gap, not a shortcut.

A word only gets a video in either module if it has a verified manifest entry — nothing is shown on a guess. `backend/tests/test_word_signs_data.py` validates the manifest's structure (no duplicate words, all required fields present, consistent URL shape) on every test run.

## What's NOT implemented (by design, and disclosed to the user in-app)

- Full grammatical ASL translation (ASL grammar, non-manual markers, classifiers) — explicitly out of scope and disclaimed in the Interpretation module's UI and API response (`is_full_grammatical_asl: false` + a visible disclaimer banner).
- ASL vocabulary beyond the curated 114-word manifest — anything else fingerspells.
- Recognition-graded camera practice for word-level vocabulary signs (only alphabet letters are model-validated — see "Word-level sign video" above).
