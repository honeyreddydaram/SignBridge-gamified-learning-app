import { useEffect, useState } from 'react'
import { recognitionApi } from '../api/endpoints'
import type { ReferenceLandmarks } from '../types'

let cache: ReferenceLandmarks | null = null
let inflight: Promise<ReferenceLandmarks> | null = null

export function useReferenceSigns() {
  const [data, setData] = useState<ReferenceLandmarks | null>(cache)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (cache) {
      setData(cache)
      return
    }
    if (!inflight) {
      inflight = recognitionApi
        .referenceSigns()
        .then((res) => {
          cache = res.data
          return cache
        })
        .finally(() => {
          inflight = null
        })
    }
    inflight
      .then((res) => setData(res))
      .catch(() => setError('Sign reference images are unavailable (train the ML model first).'))
  }, [])

  return { referenceSigns: data, error }
}
