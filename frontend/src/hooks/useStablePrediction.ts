import { useEffect, useRef, useState } from 'react'
import type { RecognitionResult } from '../types'

const POLL_INTERVAL_MS = 350
const BUFFER_SIZE = 6
const CONFIRM_THRESHOLD = 4 // majority-of-6 confident reads must agree before a letter "counts"
const RELEASE_FRAMES = 3 // consecutive non-matching/no-hand frames required before the same letter can fire again

/**
 * Temporal smoothing state machine shared by the Recognition module and
 * camera-based Learning challenges (both call this on top of useCamera +
 * recognitionApi.predict). Implements the spec's four behavioral
 * requirements in one place instead of duplicating them per screen:
 *   - smooths predictions across multiple frames (majority vote over a
 *     rolling buffer, not a single noisy frame)
 *   - rejects uncertain predictions (only frames the backend itself marked
 *     `is_confident` — i.e. above RECOGNITION_CONFIDENCE_THRESHOLD — count)
 *   - prevents one held sign from repeatedly re-firing the same letter
 *     (a letter must be "released" — hand removed or sign changed — for
 *     RELEASE_FRAMES straight polls before it can confirm again)
 */
export function useStablePrediction(
  active: boolean,
  predictFn: () => Promise<RecognitionResult | null>,
  onConfirmed: (letter: string) => void,
) {
  const [liveResult, setLiveResult] = useState<RecognitionResult | null>(null)
  const bufferRef = useRef<(string | null)[]>([])
  const lastEmittedRef = useRef<string | null>(null)
  const framesSinceMatchRef = useRef(0)
  const onConfirmedRef = useRef(onConfirmed)
  onConfirmedRef.current = onConfirmed

  useEffect(() => {
    if (!active) {
      bufferRef.current = []
      lastEmittedRef.current = null
      framesSinceMatchRef.current = 0
      return
    }

    let cancelled = false
    let inFlight = false

    const tick = async () => {
      if (cancelled || inFlight) return
      inFlight = true
      try {
        const result = await predictFn()
        if (cancelled || !result) return
        setLiveResult(result)

        const reading = result.is_confident ? result.predicted_letter : null
        const buffer = bufferRef.current
        buffer.push(reading)
        if (buffer.length > BUFFER_SIZE) buffer.shift()

        const counts = new Map<string, number>()
        for (const r of buffer) {
          if (!r) continue
          counts.set(r, (counts.get(r) ?? 0) + 1)
        }
        let majorityLetter: string | null = null
        let majorityCount = 0
        for (const [letter, count] of counts) {
          if (count > majorityCount) {
            majorityLetter = letter
            majorityCount = count
          }
        }

        if (majorityLetter && majorityCount >= CONFIRM_THRESHOLD) {
          if (majorityLetter !== lastEmittedRef.current) {
            lastEmittedRef.current = majorityLetter
            framesSinceMatchRef.current = 0
            onConfirmedRef.current(majorityLetter)
          } else {
            framesSinceMatchRef.current = 0
          }
        } else {
          framesSinceMatchRef.current += 1
          if (framesSinceMatchRef.current >= RELEASE_FRAMES) {
            lastEmittedRef.current = null
          }
        }
      } finally {
        inFlight = false
      }
    }

    const interval = setInterval(tick, POLL_INTERVAL_MS)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [active, predictFn])

  return { liveResult }
}
