import { useEffect, useState } from 'react'
import { usersApi, vocabularyApi } from '../api/endpoints'
import type { Achievement, MasterySummary } from '../types'
import { useAuth } from '../store/AuthContext'

export function Dashboard() {
  const { user, refreshUser } = useAuth()
  const [achievements, setAchievements] = useState<Achievement[]>([])
  const [mastery, setMastery] = useState<MasterySummary | null>(null)

  useEffect(() => {
    refreshUser()
    usersApi.achievements().then((res) => setAchievements(res.data))
    vocabularyApi.masterySummary().then((res) => setMastery(res.data))
  }, [refreshUser])

  if (!user) return null

  const xpIntoLevel = user.xp_total - levelFloor(user.level)
  const xpForNextLevel = 100 * user.level
  const progressPct = Math.min(100, Math.round((100 * xpIntoLevel) / xpForNextLevel))

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-brand-800">Hi, {user.username} 👋</h1>

      <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Level" value={user.level} icon="⭐" />
        <StatCard label="Streak" value={`${user.current_streak}d`} icon="🔥" sub={`best ${user.longest_streak}d`} />
        <StatCard label="Hearts" value={user.hearts} icon="❤️" />
        <StatCard label="Total XP" value={user.xp_total} icon="✨" />
      </div>

      <div className="mb-8 rounded-xl border border-brand-100 bg-white p-4">
        <div className="mb-1 flex justify-between text-sm text-gray-600">
          <span>Level {user.level}</span>
          <span>{xpIntoLevel} / {xpForNextLevel} XP</span>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-brand-50">
          <div className="h-full bg-brand-500 transition-all" style={{ width: `${progressPct}%` }} />
        </div>
      </div>

      <h2 className="mb-3 text-lg font-semibold text-brand-800">Vocabulary Mastery</h2>
      {mastery && (
        <>
          <p className="mb-3 text-xs text-gray-500">
            Progress isn't lost if you miss a day — mastery only ever moves forward, streaks are separate.
          </p>
          <div className="mb-4 grid grid-cols-3 gap-4">
            <StatCard label="Learned" value={mastery.learning} icon="📖" />
            <StatCard label="Practicing" value={mastery.practicing} icon="💪" />
            <StatCard label="Mastered" value={mastery.mastered} icon="🏅" />
          </div>
          {mastery.needs_practice.length > 0 && (
            <div className="mb-8 rounded-xl border border-brand-100 bg-white p-4">
              <p className="mb-2 text-sm font-semibold text-brand-800">Needs practice</p>
              <div className="flex flex-wrap gap-2">
                {mastery.needs_practice.map((w) => (
                  <span key={w} className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
                    {w}
                  </span>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      <h2 className="mb-3 text-lg font-semibold text-brand-800">Achievements</h2>
      {achievements.length === 0 ? (
        <p className="text-sm text-gray-500">Complete lessons to earn your first badge.</p>
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {achievements.map((a) => (
            <div key={a.code} className="flex items-center gap-3 rounded-xl border border-brand-100 bg-white p-3">
              <span className="text-2xl">{a.icon}</span>
              <div>
                <p className="text-sm font-semibold text-brand-800">{a.title}</p>
                <p className="text-xs text-gray-500">{a.description}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function levelFloor(level: number): number {
  // Inverse of the backend's _level_for_xp: cumulative XP needed to REACH `level`.
  let total = 0
  for (let l = 1; l < level; l++) total += 100 * l
  return total
}

function StatCard({ label, value, icon, sub }: { label: string; value: string | number; icon: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-brand-100 bg-white p-4 text-center">
      <div className="text-2xl">{icon}</div>
      <div className="text-xl font-bold text-brand-800">{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
      {sub && <div className="text-[11px] text-gray-400">{sub}</div>}
    </div>
  )
}
