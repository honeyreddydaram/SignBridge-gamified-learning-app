import { useEffect } from 'react'
import { useCamera } from '../hooks/useCamera'

interface SelfCheckCameraProps {
  prompt: string
  onResult: (selfCorrect: boolean) => void
  peekVideo?: React.ReactNode // optional "need a reminder?" reveal, e.g. for scenarios
}

/**
 * Shared camera step for every vocabulary Produce/Recall/Quest/Scenario
 * interaction. ALWAYS self-checked — the learner watches their own camera
 * feed and honestly marks whether they signed it correctly. This is
 * deliberate, not a shortcut: the trained recognition model
 * (ml/models/asl_landmark_classifier.joblib) only classifies static A-Z
 * fingerspelling handshapes from a single frame and has no way to validate
 * dynamic word-level signs like HELLO. Showing a model-generated "Correct!"
 * here would be fabricating a capability that doesn't exist — see
 * backend/app/services/mastery_service.py's module docstring for the full
 * rationale. A-Z camera challenges (CameraChallenge.tsx) are unaffected and
 * keep using real model-graded recognition.
 */
export function SelfCheckCamera({ prompt, onResult, peekVideo }: SelfCheckCameraProps) {
  const { videoRef, permission, error, start, stop } = useCamera()

  useEffect(() => {
    start()
    return () => stop()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="flex flex-col items-center gap-3 text-center">
      <p className="text-lg font-semibold text-brand-800">{prompt}</p>

      <div className="relative aspect-video w-full max-w-sm overflow-hidden rounded-xl bg-black">
        <video ref={videoRef} autoPlay playsInline muted className="h-full w-full -scale-x-100 object-cover" />
      </div>

      {permission === 'denied' && <p className="max-w-sm text-sm text-red-600">{error}</p>}
      {permission === 'unavailable' && <p className="max-w-sm text-sm text-red-600">{error}</p>}

      {peekVideo}

      <div className="rounded-lg bg-amber-50 px-3 py-1.5 text-xs text-amber-700">
        Self-check — you mark this yourself. Our camera recognition doesn't yet support full-word signs.
      </div>

      <div className="flex gap-3">
        <button
          onClick={() => onResult(true)}
          className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
        >
          ✅ I signed it correctly
        </button>
        <button
          onClick={() => onResult(false)}
          className="rounded-lg bg-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-300"
        >
          🔁 Need more practice
        </button>
      </div>
    </div>
  )
}
