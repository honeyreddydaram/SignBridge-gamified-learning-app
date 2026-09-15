import { useCallback, useEffect, useRef, useState } from 'react'
import { recognitionApi } from '../api/endpoints'
import { useCamera } from '../hooks/useCamera'
import { useStablePrediction } from '../hooks/useStablePrediction'

interface CameraChallengeProps {
  targetLetter: string
  lessonId: number
  onResult: (correct: boolean) => void
}

/**
 * "Show the sign for X" — camera practice validated by the SAME shared
 * recognition model/service used by the standalone Recognition module
 * (both call POST /api/recognition/predict, backed by
 * app/services/recognition_service.py).
 */
export function CameraChallenge({ targetLetter, lessonId, onResult }: CameraChallengeProps) {
  const { videoRef, permission, error, start, stop, captureFrameBase64 } = useCamera()
  const [status, setStatus] = useState<'waiting' | 'graded'>('waiting')
  const [wasCorrect, setWasCorrect] = useState<boolean | null>(null)
  const gradedRef = useRef(false)

  useEffect(() => {
    start()
    return () => stop()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetLetter])

  const predictFn = useCallback(async () => {
    const frame = captureFrameBase64()
    if (!frame) return null
    try {
      const { data } = await recognitionApi.predict(frame, targetLetter, lessonId)
      return data
    } catch {
      return null
    }
  }, [captureFrameBase64, targetLetter, lessonId])

  const { liveResult } = useStablePrediction(
    permission === 'granted' && status === 'waiting',
    predictFn,
    (letter) => {
      if (gradedRef.current) return
      gradedRef.current = true
      const correct = letter === targetLetter
      setWasCorrect(correct)
      setStatus('graded')
      onResult(correct)
    },
  )

  return (
    <div className="flex flex-col items-center gap-3">
      <p className="text-lg font-semibold text-brand-800">Show the sign for "{targetLetter}"</p>

      <div className="relative aspect-video w-full max-w-md overflow-hidden rounded-xl bg-black">
        <video ref={videoRef} autoPlay playsInline muted className="h-full w-full -scale-x-100 object-cover" />
        {status === 'graded' && (
          <div
            className={`absolute inset-0 flex items-center justify-center text-4xl font-bold ${
              wasCorrect ? 'bg-green-500/70 text-white' : 'bg-red-500/70 text-white'
            }`}
          >
            {wasCorrect ? '✅ Correct!' : `❌ That looked like "${liveResult?.predicted_letter ?? '?'}"`}
          </div>
        )}
      </div>

      {permission === 'denied' && (
        <p className="max-w-sm text-center text-sm text-red-600">
          {error} You can skip this challenge below.
        </p>
      )}
      {permission === 'unavailable' && (
        <p className="max-w-sm text-center text-sm text-red-600">{error}</p>
      )}

      {permission === 'granted' && status === 'waiting' && (
        <p className="text-sm text-gray-500">
          {liveResult?.hand_detected
            ? liveResult.is_confident
              ? `Detecting "${liveResult.predicted_letter}" (${Math.round(liveResult.confidence * 100)}%)... hold steady`
              : 'Hand detected, low confidence — adjust lighting/angle'
            : 'Show your hand to the camera'}
        </p>
      )}

      {status === 'waiting' && (
        <button
          onClick={() => {
            if (gradedRef.current) return
            gradedRef.current = true
            setWasCorrect(false)
            setStatus('graded')
            onResult(false)
          }}
          className="text-sm text-gray-400 underline hover:text-gray-600"
        >
          Skip this challenge
        </button>
      )}
    </div>
  )
}
