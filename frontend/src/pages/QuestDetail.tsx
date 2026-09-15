import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { questsApi } from '../api/endpoints'
import { SelfCheckCamera } from '../components/SelfCheckCamera'
import { useAuth } from '../store/AuthContext'
import type { Quest } from '../types'

type Phase = 'loading' | 'active' | 'complete' | 'error'

export function QuestDetail() {
  const { questKey } = useParams<{ questKey: string }>()
  const navigate = useNavigate()
  const { refreshUser } = useAuth()

  const [phase, setPhase] = useState<Phase>('loading')
  const [quest, setQuest] = useState<Quest | null>(null)
  const [lastXp, setLastXp] = useState(0)
  const [newAchievements, setNewAchievements] = useState<string[]>([])
  const [showResult, setShowResult] = useState<boolean | null>(null)

  useEffect(() => {
    if (!questKey) return
    questsApi
      .get(questKey)
      .then((res) => {
        setQuest(res.data)
        setPhase(res.data.status === 'completed' ? 'complete' : 'active')
      })
      .catch(() => setPhase('error'))
  }, [questKey])

  if (phase === 'loading') return <p className="mx-auto max-w-xl px-4 py-8 text-gray-500">Loading quest...</p>
  if (phase === 'error' || !quest) return <p className="mx-auto max-w-xl px-4 py-8 text-red-600">Quest not found.</p>

  if (phase === 'complete') {
    return (
      <div className="mx-auto max-w-md px-4 py-12 text-center">
        <div className="mb-4 text-6xl">🎉</div>
        <h1 className="mb-2 text-2xl font-bold text-brand-800">{quest.title} complete!</h1>
        <div className="mb-2 flex flex-wrap justify-center gap-2">
          {quest.words.map((w) => (
            <span key={w.word} className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-700">
              {w.word} ✓
            </span>
          ))}
        </div>
        {lastXp > 0 && <p className="mt-4 text-lg font-semibold text-brand-700">+{lastXp} XP</p>}
        {newAchievements.length > 0 && (
          <p className="mt-2 text-sm text-gray-600">New badges: {newAchievements.join(', ')}</p>
        )}
        <button
          onClick={() => navigate('/quests')}
          className="mt-6 rounded-lg bg-brand-600 px-6 py-2 font-medium text-white hover:bg-brand-700"
        >
          Back to Quests
        </button>
      </div>
    )
  }

  const currentWord = quest.words.find((w) => !w.completed)
  if (!currentWord) return null // shouldn't happen while phase === 'active'

  async function handleResult(selfCorrect: boolean) {
    setShowResult(selfCorrect)
    setTimeout(async () => {
      setShowResult(null)
      try {
        const { data } = await questsApi.submitStep(questKey!, currentWord!.word, selfCorrect)
        setQuest(data.quest)
        setLastXp((xp) => xp + data.xp_awarded)
        setNewAchievements((a) => [...a, ...data.new_achievements])
        if (data.quest_completed) {
          setPhase('complete')
        }
        refreshUser()
      } catch {
        setPhase('error')
      }
    }, 900)
  }

  return (
    <div className="mx-auto max-w-xl px-4 py-8">
      <button onClick={() => navigate('/quests')} className="mb-4 text-sm text-gray-400 hover:text-gray-600">
        ← All quests
      </button>

      <h1 className="mb-1 text-xl font-bold text-brand-800">{quest.title}</h1>

      {/* Checklist progress */}
      <div className="mb-6 flex flex-wrap gap-2">
        {quest.words.map((w) => (
          <span
            key={w.word}
            className={`rounded-full px-3 py-1 text-sm font-medium ${
              w.completed
                ? 'bg-green-100 text-green-700'
                : w.word === currentWord.word
                  ? 'bg-brand-100 text-brand-700'
                  : 'bg-gray-100 text-gray-400'
            }`}
          >
            {w.word} {w.completed ? '✓' : '☐'}
          </span>
        ))}
      </div>

      {quest.quest_type === 'scenario' && quest.prompt && (
        <div className="mb-4 rounded-xl border border-brand-100 bg-white p-4 text-center">
          <p className="text-sm text-gray-500">Scenario</p>
          <p className="text-lg font-semibold text-brand-800">{quest.prompt}</p>
        </div>
      )}

      {showResult !== null ? (
        <div
          className={`flex h-64 items-center justify-center rounded-xl text-2xl font-bold ${
            showResult ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
          }`}
        >
          {showResult ? '✅ Nice!' : '🔁 Keep practicing'}
        </div>
      ) : (
        <SelfCheckCamera
          prompt={
            quest.quest_type === 'scenario'
              ? 'Show your sign to the camera.'
              : `Show the sign for "${currentWord.word}".`
          }
          onResult={handleResult}
        />
      )}
    </div>
  )
}
