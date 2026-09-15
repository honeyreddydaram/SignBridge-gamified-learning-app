import { useEffect } from 'react'
import { useCamera } from '../hooks/useCamera'

interface VocabMirrorPracticeProps {
  words: string[]
  onDone: () => void
}

/**
 * Ungraded self-practice: the learner's own camera feed, side by side with a
 * reminder of the words just covered. Deliberately NOT recognition-graded —
 * the trained model only classifies static A-Z fingerspelling handshapes
 * from a single frame; it was never trained on dynamic word-level signs and
 * cannot validate them. Pretending otherwise would be exactly the kind of
 * fabricated-working-feature this project rules out. See
 * curriculum.py's generate_vocabulary_exercises docstring for the same note
 * on the backend side.
 */
export function VocabMirrorPractice({ words, onDone }: VocabMirrorPracticeProps) {
  const { videoRef, permission, error, start, stop } = useCamera()

  useEffect(() => {
    start()
    return () => stop()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="flex flex-col items-center gap-4 text-center">
      <h2 className="text-xl font-bold text-brand-800">Practice time</h2>
      <p className="max-w-sm text-sm text-gray-600">
        Turn on your camera and try signing each word below from memory. This isn't graded — it's just to
        build muscle memory before moving on.
      </p>

      <div className="flex flex-wrap justify-center gap-2">
        {words.map((w) => (
          <span key={w} className="rounded-full bg-brand-50 px-3 py-1 text-sm font-medium text-brand-700">
            {w}
          </span>
        ))}
      </div>

      <div className="aspect-video w-full max-w-sm overflow-hidden rounded-xl bg-black">
        <video ref={videoRef} autoPlay playsInline muted className="h-full w-full -scale-x-100 object-cover" />
      </div>
      {permission === 'denied' && <p className="text-sm text-red-600">{error} You can still mark this as done.</p>}
      {permission === 'unavailable' && <p className="text-sm text-red-600">{error}</p>}

      <button
        onClick={onDone}
        className="rounded-lg bg-brand-600 px-6 py-2 font-medium text-white hover:bg-brand-700"
      >
        I practiced these — continue
      </button>
    </div>
  )
}
