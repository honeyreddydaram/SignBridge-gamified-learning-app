import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { TOKEN_STORAGE_KEY } from '../api/client'
import { authApi, usersApi } from '../api/endpoints'
import type { UserProfile } from '../types'

interface AuthContextValue {
  user: UserProfile | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, username: string, password: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY)
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      const { data } = await usersApi.me()
      setUser(data)
    } catch {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshUser()
  }, [refreshUser])

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await authApi.login(email, password)
    localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token)
    await refreshUser()
  }, [refreshUser])

  const signup = useCallback(async (email: string, username: string, password: string) => {
    const { data } = await authApi.signup(email, username, password)
    localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token)
    await refreshUser()
  }, [refreshUser])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
