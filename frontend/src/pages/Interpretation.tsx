import { useState, type FormEvent } from 'react'
import { interpretationApi } from '../api/endpoints'
import { AslSentencePlayer } from '../components/AslSentencePlayer'
import type { InterpretResponse } from '../types'

/**
 * Communication tool, not a teaching interface: type English, watch it play
 * as one large sign at a time — real video for the 18 words with a
 * dedicated clip, sequential static letters (same player) for everything
 * else. See AslSentencePlayer.tsx for the player itself and
 * ARCHITECTURE.md's "Word-level sign video" section for why only 18/114
 * words qualify for clean single-sign playback.
 */
export function Interpretation() {
  const [text, setText] = useState('')
  const [result, setResult] = useState<InterpretResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [showAbout, setShowAbout] = useState(false)

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
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-brand-800">Text → ASL</h1>

      <form onSubmit={handleSubmit} className="mb-8 flex gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type English text..."
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:outline-none"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-brand-600 px-6 py-2 font-medium text-white hover:bg-brand-700 disabled:opacity-50"
        >
          {loading ? '...' : 'Play'}
        </button>
      </form>

      {result && (
        <div className="flex flex-col items-center gap-6">
          <AslSentencePlayer segments={result.segments} />

          <div className="w-full max-w-sm text-center">
            <button
              onClick={() => setShowAbout((s) => !s)}
              className="text-xs text-gray-400 underline hover:text-gray-600"
            >
              About this translation
            </button>
            {showAbout && <p className="mt-2 text-xs leading-relaxed text-gray-500">{result.disclaimer}</p>}
          </div>
        </div>
      )}
    </div>
  )
}
