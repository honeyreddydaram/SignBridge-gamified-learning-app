// Standard MediaPipe Hands 21-point connection topology.
const HAND_CONNECTIONS: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4],
  [0, 5], [5, 6], [6, 7], [7, 8],
  [5, 9], [9, 10], [10, 11], [11, 12],
  [9, 13], [13, 14], [14, 15], [15, 16],
  [13, 17], [17, 18], [18, 19], [19, 20],
  [0, 17],
]

interface HandSkeletonProps {
  feature: number[] // 63 values: 21 x (x, y, z), wrist-origin + scale normalized
  className?: string
  strokeColor?: string
  jointColor?: string
}

/**
 * Renders a real, trained-data-derived hand pose as an SVG skeleton — used
 * for lesson sign cards and the fingerspelling animation. The `feature`
 * vector comes straight from ml/models/reference_landmarks.json (computed
 * from actual training images), not a stock photo or hand-drawn asset.
 */
export function HandSkeleton({
  feature,
  className,
  strokeColor = 'currentColor',
  jointColor = '#2f8f7d',
}: HandSkeletonProps) {
  if (!feature || feature.length < 63) return null

  const points: [number, number][] = []
  for (let i = 0; i < 21; i++) {
    points.push([feature[i * 3], feature[i * 3 + 1]])
  }

  // Normalized coords are wrist-origin, hand-size-scaled (~[-2, 2] range).
  // Map to a fixed viewBox with some padding.
  const scale = 40
  const cx = 100
  const cy = 100
  const project = ([x, y]: [number, number]): [number, number] => [cx + x * scale, cy + y * scale]

  return (
    <svg viewBox="0 0 200 200" className={className} aria-hidden="true">
      {HAND_CONNECTIONS.map(([a, b], i) => {
        const [x1, y1] = project(points[a])
        const [x2, y2] = project(points[b])
        return (
          <line
            key={i}
            x1={x1}
            y1={y1}
            x2={x2}
            y2={y2}
            stroke={strokeColor}
            strokeWidth={4}
            strokeLinecap="round"
          />
        )
      })}
      {points.map((p, i) => {
        const [x, y] = project(p)
        return <circle key={i} cx={x} cy={y} r={i === 0 ? 6 : 4.5} fill={jointColor} />
      })}
    </svg>
  )
}
