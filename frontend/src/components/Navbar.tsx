import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../store/AuthContext'

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
    isActive ? 'bg-brand-600 text-white' : 'text-brand-800 hover:bg-brand-100'
  }`

export function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  if (!user) return null

  return (
    <nav className="sticky top-0 z-10 border-b border-brand-100 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-2 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-lg font-bold text-brand-700">SignBridge</span>
          <div className="ml-2 flex flex-wrap gap-1">
            <NavLink to="/learn" className={linkClass}>Learn</NavLink>
            <NavLink to="/recognize" className={linkClass}>Recognize</NavLink>
            <NavLink to="/interpret" className={linkClass}>Interpret</NavLink>
            <NavLink to="/dashboard" className={linkClass}>Dashboard</NavLink>
          </div>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className="hidden sm:inline text-brand-700">
            🔥 {user.current_streak} · ❤️ {user.hearts} · Lv.{user.level} · {user.xp_total} XP
          </span>
          <button
            onClick={() => {
              logout()
              navigate('/login')
            }}
            className="rounded-lg px-3 py-1.5 text-brand-700 hover:bg-brand-100"
          >
            Log out
          </button>
        </div>
      </div>
    </nav>
  )
}
