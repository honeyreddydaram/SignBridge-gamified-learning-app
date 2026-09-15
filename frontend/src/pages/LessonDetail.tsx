import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { lessonsApi } from '../api/endpoints'
import { CameraChallenge } from '../components/CameraChallenge'
import { SignCard } from '../components/SignCard'
import { HandSkeleton } from '../components/HandSkeleton'
import { VocabMirrorPractice } from '../components/VocabMirrorPractice'
import { useReferenceSigns } from '../hooks/useReferenceSigns'
import { useAuth } from '../store/AuthContext'
import type { Exercise, LessonCompletionResult, SignVideo } from '../types'

type Phase = 'loading' | 'active' | 'summary' | 'error'

export function LessonDetail() {
  const { lessonId } = useParams<{ lessonId: string }>()
  const navigate = useNavigate()
  const { refreshUser } = useAuth()
  const id = Number(lessonId)

  const [phase, setPhase] = useState<Phase>('loading')
  const [exercises, setExercises] = useState<Exercise[]>([])
  const [index, setIndex] = useState(0)
  const [correctCount, setCorrectCount] = useState(0)
  const [gradedCount, setGradedCount] = useState(0)
  const [result, setResult] = useState<LessonCompletionResult | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    lessonsApi
      .exercises(id)
      .then((res) => {
        setExercises(res.data.exercises)
        setPhase('active')
      })
      .catch(() => setPhase('error'))
  }, [id])

  function isGraded(ex: Exercise) {
    return ex.type !== 'learn_card' && ex.type !== 'vocab_video_card' && ex.type !== 'vocab_mirror_practice'
  }

  async function handleAnswer(correct: boolean) {
    const current = exercises[index]
    const graded = isGraded(current)
    const newCorrect = correctCount + (graded && correct ? 1 : 0)
    const newGraded = gradedCount + (graded ? 1 : 0)
    if (graded) {
      setCorrectCount(newCorrect)
      setGradedCount(newGraded)
    }

    if (index + 1 < exercises.length) {
      setTimeout(() => setIndex(index + 1), graded ? 900 : 200)
    } else {
      const finalCorrect = graded ? newCorrect : correctCount
      const finalTotal = graded ? newGraded : gradedCount
      try {
        const { data } = await lessonsApi.complete(id, finalCorrect, Math.max(1, finalTotal))
        setResult(data)
        setPhase('summary')
        refreshUser()
      } catch {
        setErrorMsg('Could not save lesson progress.')
        setPhase('error')
      }
    }
  }

  if (phase === 'loading') return <p className="mx-auto max-w-2xl px-4 py-8 text-gray-500">Loading lesson...</p>
  if (phase === 'error')
    return <p className="mx-auto max-w-2xl px-4 py-8 text-red-600">{errorMsg ?? 'Lesson not found or locked.'}</p>

  if (phase === 'summary' && result) {
    return (
      <div className="mx-auto max-w-md px-4 py-12 text-center">
        <div className="mb-4 text-6xl">{result.lesson.best_score_pct === 100 ? '🌟' : '🎉'}</div>
        <h1 className="mb-2 text-2xl font-bold text-brand-800">Lesson Complete!</h1>
        <p className="mb-6 text-gray-600">Score: {result.lesson.best_score_pct}%</p>

        <div className="mb-6 rounded-xl border border-brand-100 bg-white p-4">
          <p className="text-lg font-semibold text-brand-700">+{result.xp_awarded} XP</p>
          {result.leveled_up && <p className="mt-1 text-sm text-amber-600">🎉 Leveled up to level {result.level}!</p>}
          {result.new_achievements.length > 0 && (
            <div className="mt-3 text-sm text-gray-600">
              New badges: {result.new_achievements.join(', ')}
            </div>
          )}
        </div>

        <button
          onClick={() => navigate('/learn')}
          className="rounded-lg bg-brand-600 px-6 py-2 font-medium text-white hover:bg-brand-700"
        >
          Continue
        </button>
      </div>
    )
  }

  const current = exercises[index]
  if (!current) return null

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <div className="mb-4 h-2 w-full overflow-hidden rounded-full bg-brand-50">
        <div
          className="h-full bg-brand-500 transition-all"
          style={{ width: `${(100 * (index + 1)) / exercises.length}%` }}
        />
      </div>

      <ExerciseView key={index} exercise={current} lessonId={id} onAnswer={handleAnswer} />
    </div>
  )
}

function ExerciseView({
  exercise,
  lessonId,
  onAnswer,
}: {
  exercise: Exercise
  lessonId: number
  onAnswer: (correct: boolean) => void
}) {
  const { referenceSigns } = useReferenceSigns()

  if (exercise.type === 'learn_card') {
    const feature = referenceSigns?.[exercise.letter]?.feature
    return (
      <div className="flex flex-col items-center gap-4 text-center">
        <h2 className="text-xl font-bold text-brand-800">Letter "{exercise.letter}"</h2>
        <div className="h-56 w-56">
          {feature ? (
            <HandSkeleton feature={feature} className="h-full w-full text-brand-700" />
          ) : (
            <p className="text-sm text-gray-400">Reference sign unavailable</p>
          )}
        </div>
        <p className="max-w-sm text-gray-600">{exercise.description}</p>
        <button
          onClick={() => onAnswer(true)}
          className="rounded-lg bg-brand-600 px-6 py-2 font-medium text-white hover:bg-brand-700"
        >
          Got it
        </button>
      </div>
    )
  }

  if (exercise.type === 'sign_identification_mcq') {
    return (
      <MCQ
        prompt={exercise.prompt}
        top={
          <div className="h-40 w-40">
            {referenceSigns?.[exercise.shown_sign_letter]?.feature ? (
              <HandSkeleton
                feature={referenceSigns![exercise.shown_sign_letter].feature}
                className="h-full w-full text-brand-700"
              />
            ) : null}
          </div>
        }
        options={exercise.options}
        correctOption={exercise.correct_option}
        renderOption={(opt) => <span className="text-2xl font-bold">{opt}</span>}
        onAnswer={onAnswer}
      />
    )
  }

  if (exercise.type === 'letter_to_sign_mcq') {
    return (
      <MCQ
        prompt={exercise.prompt}
        top={<span className="text-5xl font-bold text-brand-800">{exercise.shown_letter}</span>}
        options={exercise.options}
        correctOption={exercise.correct_option}
        renderOption={(opt) => <SignCard letter={opt} />}
        onAnswer={onAnswer}
      />
    )
  }

  if (exercise.type === 'vocab_video_card') {
    return (
      <div className="flex flex-col items-center gap-4 text-center">
        <h2 className="text-xl font-bold text-brand-800">{exercise.word}</h2>
        <ReplayableVideo video={exercise.video} className="aspect-video w-full max-w-sm" />
        <p className="max-w-sm text-gray-600">{exercise.description}</p>
        <p className="text-xs text-gray-400">
          Source:{' '}
          <a href={exercise.video.watch_url} target="_blank" rel="noreferrer" className="underline hover:text-gray-600">
            {exercise.source_channel}
          </a>
        </p>
        <button
          onClick={() => onAnswer(true)}
          className="rounded-lg bg-brand-600 px-6 py-2 font-medium text-white hover:bg-brand-700"
        >
          Got it
        </button>
      </div>
    )
  }

  if (exercise.type === 'vocab_comprehension_mcq') {
    return (
      <MCQ
        prompt={exercise.prompt}
        top={<ReplayableVideo video={exercise.video} className="aspect-video w-64" />}
        options={exercise.options}
        correctOption={exercise.correct_option}
        renderOption={(opt) => <span className="font-semibold">{opt}</span>}
        onAnswer={onAnswer}
      />
    )
  }

  if (exercise.type === 'vocab_mirror_practice') {
    return <VocabMirrorPractice words={exercise.words} onDone={() => onAnswer(true)} />
  }

  // camera_challenge
  return (
    <CameraChallenge targetLetter={exercise.target_letter} lessonId={lessonId} onResult={onAnswer} />
  )
}

function ReplayableVideo({ video, className }: { video: SignVideo; className?: string }) {
  const [playKey, setPlayKey] = useState(0)

  return (
    <div className="flex flex-col items-center gap-2">
      <div className={`overflow-hidden rounded-xl bg-black ${className ?? ''}`}>
        <iframe
          key={playKey}
          src={`${video.embed_url}?autoplay=1&rel=0`}
          title={video.source_title}
          className="h-full w-full"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      </div>
      <button
        onClick={() => setPlayKey((k) => k + 1)}
        className="rounded-lg border border-brand-200 px-3 py-1 text-xs text-brand-700 hover:bg-brand-50"
      >
        ↻ Replay
      </button>
    </div>
  )
}

function MCQ({
  prompt,
  top,
  options,
  correctOption,
  renderOption,
  onAnswer,
}: {
  prompt: string
  top: React.ReactNode
  options: string[]
  correctOption: string
  renderOption: (opt: string) => React.ReactNode
  onAnswer: (correct: boolean) => void
}) {
  const [selected, setSelected] = useState<string | null>(null)

  function pick(opt: string) {
    if (selected) return
    setSelected(opt)
    setTimeout(() => onAnswer(opt === correctOption), 700)
  }

  return (
    <div className="flex flex-col items-center gap-5 text-center">
      <p className="text-lg font-semibold text-brand-800">{prompt}</p>
      <div className="flex items-center justify-center">{top}</div>
      <div className="grid grid-cols-2 gap-3">
        {options.map((opt) => (
          <button
            key={opt}
            onClick={() => pick(opt)}
            disabled={!!selected}
            className={`flex items-center justify-center rounded-xl border-2 p-3 transition-colors ${
              selected === opt
                ? opt === correctOption
                  ? 'border-green-500 bg-green-50'
                  : 'border-red-500 bg-red-50'
                : selected && opt === correctOption
                  ? 'border-green-500 bg-green-50'
                  : 'border-brand-100 bg-white hover:border-brand-400'
            }`}
          >
            {renderOption(opt)}
          </button>
        ))}
      </div>
    </div>
  )
}
