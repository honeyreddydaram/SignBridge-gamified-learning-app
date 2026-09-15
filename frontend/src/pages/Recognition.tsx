import { useCallback, useEffect, useState } from 'react'
import { recognitionApi } from '../api/endpoints'
import { useCamera } from '../hooks/useCamera'
import { useStablePrediction } from '../hooks/useStablePrediction'

export function Recognition() {
  const { videoRef, permission, error, start, stop, captureFrameBase64 } = useCamera()
  const [text, setText] = useState('')
  const [modelReady, setModelReady] = useState<boolean | null>(null)
  const [modelError, setModelError] = useState<string | null>(null)
  const [active, setActive] = useState(false)

  useEffect(() => {
    recognitionApi
      .status()
      .then((res) => {
        setModelReady(res.data.ready)
        setModelError(res.data.error)
      })
      .catch(() => setModelReady(false))
  }, [])

  const predictFn = useCallback(async () => {
    const frame = captureFrameBase64()
    if (!frame) return null
    try {
      const { data } = await recognitionApi.predict(frame)
      return data
    } catch {
      return null
    }
  }, [captureFrameBase64])

  const { liveResult } = useStablePrediction(active && permission === 'granted', predictFn, (letter) => {
    setText((t) => t + letter)
  })

  async function handleStart() {
    setActive(true)
    await start()
  }

  function handleStop() {
    setActive(false)
    stop()
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-1 text-2xl font-bold text-brand-800">ASL Recognition</h1>
      <p className="mb-6 text-sm text-gray-600">
        Fingerspell letters A-Z to your webcam. Hold each sign steady — the app waits for a stable, confident
        reading before adding a letter, and won't repeat the same letter until you change your hand shape.
      </p>

      {modelReady === false && (
        <div className="mb-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800">
          Recognition model isn't loaded on the server ({modelError ?? 'unknown error'}). Run the ML training
          pipeline (see ml/README.md) then restart the backend.
        </div>
      )}

      <div className="relative mx-auto mb-4 aspect-video w-full overflow-hidden rounded-xl bg-black">
        <video ref={videoRef} autoPlay playsInline muted className="h-full w-full -scale-x-100 object-cover" />
        {!active && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/60 text-white">
            <button
              onClick={handleStart}
              disabled={modelReady === false}
              className="rounded-lg bg-brand-600 px-5 py-2 font-medium hover:bg-brand-700 disabled:opacity-50"
            >
              Start Camera
            </button>
          </div>
        )}
        {active && liveResult && (
          <div className="absolute bottom-2 left-2 rounded-lg bg-black/60 px-3 py-1 text-sm text-white">
            {liveResult.hand_detected
              ? `${liveResult.predicted_letter ?? '?'} (${Math.round(liveResult.confidence * 100)}%)${
                  liveResult.is_confident ? '' : ' — low confidence'
                }`
              : 'No hand detected'}
          </div>
        )}
      </div>

      {permission === 'denied' && <p className="mb-4 text-sm text-red-600">{error}</p>}
      {permission === 'unavailable' && <p className="mb-4 text-sm text-red-600">{error}</p>}

      {active && (
        <button onClick={handleStop} className="mb-4 text-sm text-gray-400 underline hover:text-gray-600">
          Stop camera
        </button>
      )}

      <div className="rounded-xl border border-brand-100 bg-white p-4">
        <p className="mb-2 text-xs uppercase tracking-wide text-gray-400">Recognized text</p>
        <p className="min-h-12 break-words text-2xl font-semibold text-brand-800">{text || ' '}</p>
        <div className="mt-3 flex gap-2">
          <button
            onClick={() => setText((t) => t + ' ')}
            className="rounded-lg border border-brand-200 px-3 py-1.5 text-sm text-brand-700 hover:bg-brand-50"
          >
            Space
          </button>
          <button
            onClick={() => setText((t) => t.slice(0, -1))}
            className="rounded-lg border border-brand-200 px-3 py-1.5 text-sm text-brand-700 hover:bg-brand-50"
          >
            Delete
          </button>
          <button
            onClick={() => setText('')}
            className="rounded-lg border border-red-200 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50"
          >
            Clear
          </button>
        </div>
      </div>
    </div>
  )
}
