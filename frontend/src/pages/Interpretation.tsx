import { useState, type FormEvent } from 'react'
import { interpretationApi } from '../api/endpoints'
import { HandSkeleton } from '../components/HandSkeleton'
import { useReferenceSigns } from '../hooks/useReferenceSigns'
import type { InterpretResponse } from '../types'

/**
 * Communication tool, not a teaching interface: type English, see the
 * supported signs play back immediately as small looping clips. No
 * descriptions, no "how to form this sign" instructions, no prominent
 * lesson framing — that's the Learning module's job (see LessonDetail.tsx's
 * vocab_video_card, which uses the SAME underlying video manifest with full
 * teaching context). Only words backed by a video dedicated to just that
 * one sign are shown here (backend: asl_signs.is_dedicated_video) — a
 * shared/compilation video can't be cleanly looped to show one sign alone,
 * so those words fingerspell here even though they're Learning-eligible.
 */
export function Interpretation() {
  const [text, setText] = useState('')
  const [result, setResult] = useState<InterpretResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const { referenceSigns } = useReferenceSigns()

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!text.trim()) return
    setLoading(true)
    try {
      const { data } = await interpretationApi.interpret(text)
      setResult(data)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-1 text-2xl font-bold text-brand-800">Text → ASL</h1>
      <p className="mb-6 text-sm text-gray-600">
        Type English text — the recipient sees it play as ASL signs immediately. For words without a
        clean sign clip, it fingerspells instead.
      </p>

      <form onSubmit={handleSubmit} className="mb-6 flex gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="e.g. hello friend"
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:outline-none"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-brand-600 px-5 py-2 font-medium text-white hover:bg-brand-700 disabled:opacity-50"
        >
          {loading ? '...' : 'Play'}
        </button>
      </form>

      {result && (
        <>
          <p className="mb-4 text-xs text-gray-400">{result.disclaimer}</p>

          <div className="flex flex-wrap gap-3">
            {result.segments
              .filter((s) => s.kind !== 'space')
              .map((seg, i) =>
                seg.kind === 'sign' && seg.video ? (
                  <div key={i} className="flex w-28 flex-col items-center gap-1">
                    <div className="aspect-square w-28 overflow-hidden rounded-xl bg-black">
                      <iframe
                        src={seg.video.loop_embed_url}
                        title={seg.word}
                        className="h-full w-full"
                        allow="autoplay; encrypted-media"
                      />
                    </div>
                    <span className="text-xs font-semibold text-brand-800">{seg.word}</span>
                  </div>
                ) : (
                  <div key={i} className="flex w-28 flex-col items-center gap-1 rounded-xl bg-white p-2">
                    <div className="flex flex-wrap justify-center gap-1">
                      {seg.letters?.map((letter, j) => {
                        const feature = referenceSigns?.[letter]?.feature
                        return (
                          <div key={j} className="h-8 w-8">
                            {feature ? (
                              <HandSkeleton feature={feature} className="h-full w-full text-brand-700" />
                            ) : null}
                          </div>
                        )
                      })}
                    </div>
                    <span className="text-xs font-medium text-gray-500">{seg.word}</span>
                  </div>
                ),
              )}
          </div>
        </>
      )}
    </div>
  )
}
