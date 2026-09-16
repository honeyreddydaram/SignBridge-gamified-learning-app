import { useEffect, useState, type ReactNode } from 'react'
import { healthApi } from '../api/endpoints'

// Render's free tier spins the backend down after ~15 min idle; the first
// request after that can take up to ~a minute to get a live response while
// migrations/seed/model imports run. This gate polls /api/health so the app
// (and Sign In/Sign Up) only mounts once the backend is actually reachable,
// instead of a user's first action surfacing a raw 502.
const REQUEST_TIMEOUT_MS = 4000
const BACKOFF_MS = [1000, 2000, 4000, 5000]
const MAX_WAIT_MS = 60000

type Phase = 'checking' | 'waking' | 'timedOut' | 'ready'

export function BackendGate({ children }: { children: ReactNode }) {
  const [phase, setPhase] = useState<Phase>('checking')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false
    const startedAt = Date.now()

    async function poll(attemptIndex: number) {
      try {
        await healthApi.check(REQUEST_TIMEOUT_MS)
        if (!cancelled) setPhase('ready')
      } catch {
        if (cancelled) return
        if (Date.now() - startedAt >= MAX_WAIT_MS) {
          setPhase('timedOut')
          return
        }
        setPhase('waking')
        const delay = BACKOFF_MS[Math.min(attemptIndex, BACKOFF_MS.length - 1)]
        setTimeout(() => {
          if (!cancelled) poll(attemptIndex + 1)
        }, delay)
      }
    }

    setPhase('checking')
    poll(0)

    return () => {
      cancelled = true
    }
  }, [attempt])

  if (phase === 'ready') return <>{children}</>

  return (
    <div className="mx-auto flex min-h-screen max-w-sm flex-col items-center justify-center px-4 text-center">
      {phase === 'timedOut' ? (
        <>
          <h1 className="mb-2 text-xl font-bold text-brand-800">Taking longer than expected</h1>
          <p className="mb-6 text-sm text-gray-600">
            The demo server is still starting up. This can happen after a period of inactivity.
          </p>
          <button
            type="button"
            onClick={() => setAttempt((n) => n + 1)}
            className="rounded-lg bg-brand-600 px-4 py-2 font-medium text-white hover:bg-brand-700"
          >
            Retry
          </button>
        </>
      ) : phase === 'waking' ? (
        <>
          <div className="mb-4 h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600" />
          <h1 className="mb-2 text-xl font-bold text-brand-800">Starting the SignBridge demo server…</h1>
          <p className="text-sm text-gray-600">This may take up to a minute after inactivity.</p>
        </>
      ) : (
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600" />
      )}
    </div>
  )
}
