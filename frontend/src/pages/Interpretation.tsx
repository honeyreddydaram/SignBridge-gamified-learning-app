import { useState, type FormEvent } from 'react'
import { interpretationApi } from '../api/endpoints'
import { HandSkeleton } from '../components/HandSkeleton'
import { useReferenceSigns } from '../hooks/useReferenceSigns'
import type { InterpretResponse } from '../types'

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
        Type English text to see it fingerspelled letter-by-letter, or as a recognized whole-word ASL sign
        where one is supported.
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
          {loading ? '...' : 'Translate'}
        </button>
      </form>

      {result && (
        <>
          <div className="mb-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800">
            ⚠️ {result.disclaimer}
          </div>

          <div className="flex flex-col gap-6">
            {result.segments
              .filter((s) => s.kind !== 'space')
              .map((seg, i) => (
                <div key={i} className="rounded-xl border border-brand-100 bg-white p-4">
                  <div className="mb-2 flex items-center gap-2">
                    <span className="text-lg font-bold text-brand-800">{seg.word}</span>
                    {seg.kind === 'sign' ? (
                      <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                        Supported ASL sign
                      </span>
                    ) : (
                      <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                        Fingerspelled
                      </span>
                    )}
                  </div>

                  {seg.kind === 'sign' && <p className="text-sm text-gray-600">{seg.description}</p>}

                  {seg.kind === 'fingerspell' && seg.letters && (
                    <div className="flex flex-wrap gap-3">
                      {seg.letters.map((letter, j) => {
                        const feature = referenceSigns?.[letter]?.feature
                        return (
                          <div key={j} className="flex flex-col items-center gap-1">
                            <div className="h-16 w-16">
                              {feature ? (
                                <HandSkeleton feature={feature} className="h-full w-full text-brand-700" />
                              ) : null}
                            </div>
                            <span className="text-xs font-medium text-gray-500">{letter}</span>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              ))}
          </div>
        </>
      )}
    </div>
  )
}
