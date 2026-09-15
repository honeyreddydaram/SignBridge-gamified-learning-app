import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../store/AuthContext'

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-brand-600">
        Loading...
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}
