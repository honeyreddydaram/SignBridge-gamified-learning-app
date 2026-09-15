import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { lessonsApi } from '../api/endpoints'
import type { Lesson } from '../types'

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

  const completedCount = lessons.filter((l) => l.status === 'completed').length

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-1 text-2xl font-bold text-brand-800">Learn the ASL Alphabet</h1>
      <p className="mb-6 text-sm text-gray-600">{completedCount} / {lessons.length} letters completed</p>

      <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-6">
        {lessons.map((lesson) => (
          <LessonNode key={lesson.id} lesson={lesson} />
        ))}
      </div>
    </div>
  )
}

function LessonNode({ lesson }: { lesson: Lesson }) {
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
