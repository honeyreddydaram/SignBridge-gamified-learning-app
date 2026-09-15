import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { questsApi } from '../api/endpoints'
import type { Quest } from '../types'

const TYPE_ICON: Record<string, string> = { mission: '🗺️', scenario: '🎭' }

export function Quests() {
  const [quests, setQuests] = useState<Quest[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    questsApi
      .list()
      .then((res) => setQuests(res.data))
      .catch(() => setError('Could not load quests.'))
  }, [])

  if (error) return <p className="mx-auto max-w-3xl px-4 py-8 text-red-600">{error}</p>
  if (!quests) return <p className="mx-auto max-w-3xl px-4 py-8 text-gray-500">Loading quests...</p>

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-1 text-2xl font-bold text-brand-800">Sign Quests</h1>
      <p className="mb-6 text-sm text-gray-600">
        Short missions that put vocabulary you've already learned to use — one camera self-check at a
        time.
      </p>

      <div className="flex flex-col gap-3">
        {quests.map((q) => {
          const doneCount = q.words.filter((w) => w.completed).length
          return (
            <Link
              key={q.key}
              to={`/quests/${q.key}`}
              className={`flex items-center gap-4 rounded-2xl border-2 p-4 transition-transform hover:scale-[1.01] ${
                q.status === 'completed' ? 'border-brand-400 bg-brand-50' : 'border-brand-100 bg-white'
              }`}
            >
              <span className="text-3xl">{TYPE_ICON[q.quest_type] ?? '📖'}</span>
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-brand-800">
                  {q.title} {q.status === 'completed' && <span className="text-green-600">✓</span>}
                </p>
                <p className="truncate text-sm text-gray-500">{q.description}</p>
                <div className="mt-2 flex flex-wrap gap-1">
                  {q.words.map((w) => (
                    <span
                      key={w.word}
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        w.completed ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      {w.word} {w.completed ? '✓' : '☐'}
                    </span>
                  ))}
                </div>
                <p className="mt-1 text-xs text-gray-400">
                  {doneCount} / {q.words.length} complete
                </p>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
