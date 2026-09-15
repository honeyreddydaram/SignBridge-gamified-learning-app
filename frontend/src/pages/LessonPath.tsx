import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { lessonsApi } from '../api/endpoints'
import { AslJourney } from '../components/AslJourney'
import type { Lesson } from '../types'

const CATEGORY_ICONS: Record<string, string> = {
  greetings_courtesy: '👋',
  family_people: '👪',
  needs_requests: '🙏',
  feelings_emotions: '😊',
  question_words: '❓',
  everyday_actions: '🏃',
  descriptions_opposites: '⚖️',
  colors: '🎨',
  time_words: '⏰',
  home_things: '🏠',
}

export function LessonPath() {
  const [lessons, setLessons] = useState<Lesson[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    lessonsApi
      .list()
      .then((res) => setLessons(res.data))
      .catch(() => setError('Could not load lessons.'))
  }, [])

  if (error) return <p className="mx-auto max-w-3xl px-4 py-8 text-red-600">{error}</p>
  if (!lessons) return <p className="mx-auto max-w-3xl px-4 py-8 text-gray-500">Loading curriculum...</p>

  const alphabet = lessons.filter((l) => l.lesson_type === 'alphabet')
  const vocabulary = lessons.filter((l) => l.lesson_type === 'vocabulary')
  const alphabetCompleted = alphabet.filter((l) => l.status === 'completed').length
  const vocabularyCompleted = vocabulary.filter((l) => l.status === 'completed').length

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-brand-800">Learn ASL</h1>

      <AslJourney lessons={lessons} />

      <section className="mb-10">
        <h2 className="mb-1 text-lg font-semibold text-brand-800">Alphabet</h2>
        <p className="mb-4 text-sm text-gray-600">{alphabetCompleted} / {alphabet.length} letters completed</p>
        <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-6">
          {alphabet.map((lesson) => (
            <AlphabetNode key={lesson.id} lesson={lesson} />
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-1 text-lg font-semibold text-brand-800">Vocabulary</h2>
        <p className="mb-4 text-sm text-gray-600">
          {vocabularyCompleted} / {vocabulary.length} categories completed — real video of a signer for
          each word
        </p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {vocabulary.map((lesson) => (
            <VocabularyNode key={lesson.id} lesson={lesson} />
          ))}
        </div>
      </section>
    </div>
  )
}

function AlphabetNode({ lesson }: { lesson: Lesson }) {
  const locked = lesson.status === 'locked'
  const completed = lesson.status === 'completed'

  const base =
    'flex flex-col items-center justify-center gap-1 rounded-2xl border-2 p-3 aspect-square text-center transition-transform'
  const style = locked
    ? 'border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed'
    : completed
      ? 'border-brand-400 bg-brand-500 text-white hover:scale-105'
      : 'border-brand-300 bg-white text-brand-700 hover:scale-105 hover:border-brand-500'

  const content = (
    <>
      <span className="text-2xl font-bold">{lesson.letter}</span>
      <span className="text-lg">{locked ? '🔒' : completed ? '✅' : '▶️'}</span>
      {lesson.best_score_pct > 0 && <span className="text-[10px] opacity-80">{lesson.best_score_pct}%</span>}
    </>
  )

  if (locked) {
    return <div className={`${base} ${style}`}>{content}</div>
  }
  return (
    <Link to={`/learn/${lesson.id}`} className={`${base} ${style}`}>
      {content}
    </Link>
  )
}

function VocabularyNode({ lesson }: { lesson: Lesson }) {
  const locked = lesson.status === 'locked'
  const completed = lesson.status === 'completed'
  const icon = (lesson.concept_key && CATEGORY_ICONS[lesson.concept_key]) || '📖'

  const base = 'flex items-center gap-3 rounded-2xl border-2 p-3 text-left transition-transform'
  const style = locked
    ? 'border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed'
    : completed
      ? 'border-brand-400 bg-brand-500 text-white hover:scale-[1.02]'
      : 'border-brand-300 bg-white text-brand-700 hover:scale-[1.02] hover:border-brand-500'

  const content = (
    <>
      <span className="text-2xl">{locked ? '🔒' : icon}</span>
      <div className="min-w-0">
        <p className="truncate text-sm font-semibold">{lesson.title}</p>
        {lesson.best_score_pct > 0 && <p className="text-[11px] opacity-80">{lesson.best_score_pct}%</p>}
      </div>
    </>
  )

  if (locked) {
    return <div className={`${base} ${style}`}>{content}</div>
  }
  return (
    <Link to={`/learn/${lesson.id}`} className={`${base} ${style}`}>
      {content}
    </Link>
  )
}
