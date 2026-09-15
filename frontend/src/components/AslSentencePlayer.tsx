import { useEffect, useMemo, useState } from 'react'
import { HandSkeleton } from './HandSkeleton'
import { useReferenceSigns } from '../hooks/useReferenceSigns'
import type { InterpretSegment } from '../types'

const SIGN_MS = { normal: 2500, slow: 4500 }
const LETTER_MS = { normal: 900, slow: 1700 }

interface WordUnit {
  word: string
  kind: 'sign' | 'fingerspell'
  videoId?: string
  loopEmbedUrl?: string
  letters?: string[]
}

/**
 * Large, single-focus ASL sentence player for a recipient who already knows
 * ASL — one sign (or one fingerspelled letter) at a time, large enough to
 * actually read, auto-advancing through the message. Real video for the 18
 * words that have a dedicated clip; the SAME player steps through
 * fingerspelled letters sequentially for everything else (static hand-pose
 * diagrams, not video — see AslSentencePlayer's letter branch below, and
 * README.md "Known limitations" for why fingerspelling has no motion).
 */
export function AslSentencePlayer({ segments }: { segments: InterpretSegment[] }) {
  const { referenceSigns } = useReferenceSigns()

  const words: WordUnit[] = useMemo(
    () =>
      segments
        .filter((s) => s.kind !== 'space')
        .map((s) =>
          s.kind === 'sign' && s.video
            ? { word: s.word, kind: 'sign' as const, videoId: s.video.video_id, loopEmbedUrl: s.video.loop_embed_url }
            : { word: s.word, kind: 'fingerspell' as const, letters: s.letters ?? [] },
        ),
    [segments],
  )

  const [wordIndex, setWordIndex] = useState(0)
  const [letterIndex, setLetterIndex] = useState(0)
  const [playing, setPlaying] = useState(true)
  const [slow, setSlow] = useState(false)
  const [replayKey, setReplayKey] = useState(0)

  // New message -> start from the top, autoplay.
  useEffect(() => {
    setWordIndex(0)
    setLetterIndex(0)
    setPlaying(true)
    setReplayKey((k) => k + 1)
  }, [words])

  const current = words[wordIndex]
  const atLastStep =
    wordIndex === words.length - 1 &&
    (current?.kind !== 'fingerspell' || letterIndex === (current.letters?.length ?? 1) - 1)
  const atFirstStep = wordIndex === 0 && letterIndex === 0

  function stepForward() {
    if (!current) return
    if (current.kind === 'fingerspell' && letterIndex + 1 < (current.letters?.length ?? 0)) {
      setLetterIndex((i) => i + 1)
    } else if (wordIndex + 1 < words.length) {
      setWordIndex((i) => i + 1)
      setLetterIndex(0)
    } else {
      setPlaying(false)
    }
  }

  function stepBackward() {
    if (letterIndex > 0) {
      setLetterIndex((i) => i - 1)
    } else if (wordIndex > 0) {
      const prevWord = words[wordIndex - 1]
      setWordIndex((i) => i - 1)
      setLetterIndex(prevWord.kind === 'fingerspell' ? (prevWord.letters?.length ?? 1) - 1 : 0)
    }
  }

  function replayCurrent() {
    setReplayKey((k) => k + 1)
  }

  function replayMessage() {
    setWordIndex(0)
    setLetterIndex(0)
    setPlaying(true)
    setReplayKey((k) => k + 1)
  }

  // Autoplay timer: advances one step after a fixed hold time. Not synced to
  // the real video's actual length (YouTube's basic embed doesn't expose
  // that without loading its separate JS player API) — "Slower" widens this
  // hold time rather than literally slowing the video's own playback rate.
  useEffect(() => {
    if (!playing || !current) return
    const duration = current.kind === 'sign' ? SIGN_MS[slow ? 'slow' : 'normal'] : LETTER_MS[slow ? 'slow' : 'normal']
    const t = setTimeout(stepForward, duration)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playing, wordIndex, letterIndex, slow, current])

  if (words.length === 0) {
    return <p className="text-sm text-gray-500">Nothing to play yet — type a message above.</p>
  }

  const currentLetter = current.kind === 'fingerspell' ? current.letters?.[letterIndex] : undefined
  const letterFeature = currentLetter ? referenceSigns?.[currentLetter]?.feature : undefined

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Sentence progress */}
      <div className="flex flex-wrap justify-center gap-x-1 gap-y-1 text-sm">
        {words.map((w, i) => (
          <span key={i} className={i === wordIndex ? 'font-bold text-brand-700' : 'text-gray-400'}>
            {w.word}
            {i < words.length - 1 && <span className="mx-1 text-gray-300">•</span>}
          </span>
        ))}
      </div>

      {/* Letter sub-progress, only while fingerspelling the current word */}
      {current.kind === 'fingerspell' && (
        <div className="text-xs text-gray-500">
          {current.letters?.map((l, i) => (
            <span key={i} className={i === letterIndex ? 'font-bold text-brand-600' : ''}>
              {l}
              {i < (current.letters?.length ?? 0) - 1 && <span className="mx-1">→</span>}
            </span>
          ))}
        </div>
      )}

      {/* Big viewer */}
      <div className="flex h-[340px] w-[340px] items-center justify-center overflow-hidden rounded-2xl bg-black sm:h-[400px] sm:w-[400px]">
        {current.kind === 'sign' ? (
          <iframe
            key={`${wordIndex}-${replayKey}`}
            src={current.loopEmbedUrl}
            title={current.word}
            className="h-full w-full"
            allow="autoplay; encrypted-media"
          />
        ) : letterFeature ? (
          <HandSkeleton key={`${wordIndex}-${letterIndex}-${replayKey}`} feature={letterFeature} className="h-4/5 w-4/5 text-white" />
        ) : null}
      </div>

      {/* Current word label + kind */}
      <div className="text-center">
        <p className="text-2xl font-bold text-brand-800">{current.word}</p>
        <p className="text-xs uppercase tracking-wide text-gray-400">
          {current.kind === 'sign' ? 'ASL sign' : 'Fingerspelled'}
        </p>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center justify-center gap-2">
        <button
          onClick={replayMessage}
          title="Play entire message again"
          className="rounded-lg border border-brand-200 px-3 py-1.5 text-sm text-brand-700 hover:bg-brand-50"
        >
          ⏮ Replay message
        </button>
        <button
          onClick={stepBackward}
          disabled={atFirstStep}
          className="rounded-lg border border-brand-200 px-3 py-1.5 text-sm text-brand-700 hover:bg-brand-50 disabled:opacity-30"
        >
          ◀ Previous
        </button>
        <button
          onClick={() => setPlaying((p) => !p)}
          className="rounded-lg bg-brand-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
        >
          {playing ? '⏸ Pause' : '▶ Play'}
        </button>
        <button
          onClick={stepForward}
          disabled={atLastStep && !playing}
          className="rounded-lg border border-brand-200 px-3 py-1.5 text-sm text-brand-700 hover:bg-brand-50 disabled:opacity-30"
        >
          Next ▶
        </button>
        <button
          onClick={replayCurrent}
          title="Replay current sign"
          className="rounded-lg border border-brand-200 px-3 py-1.5 text-sm text-brand-700 hover:bg-brand-50"
        >
          ↻ Replay sign
        </button>
        <button
          onClick={() => setSlow((s) => !s)}
          className={`rounded-lg border px-3 py-1.5 text-sm ${
            slow ? 'border-brand-600 bg-brand-50 text-brand-700' : 'border-brand-200 text-brand-700 hover:bg-brand-50'
          }`}
        >
          {slow ? '🐢 Slower: on' : 'Slower pace'}
        </button>
      </div>
    </div>
  )
}
