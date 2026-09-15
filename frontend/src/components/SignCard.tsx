import { HandSkeleton } from './HandSkeleton'
import { useReferenceSigns } from '../hooks/useReferenceSigns'

interface SignCardProps {
  letter: string
  onClick?: () => void
  selected?: boolean
  correct?: boolean | null // null = not yet revealed
  size?: 'sm' | 'lg'
}

export function SignCard({ letter, onClick, selected, correct, size = 'sm' }: SignCardProps) {
  const { referenceSigns } = useReferenceSigns()
  const feature = referenceSigns?.[letter]?.feature

  const dims = size === 'lg' ? 'h-40 w-40' : 'h-20 w-20'
  let ring = 'border-brand-100'
  if (selected && correct === true) ring = 'border-green-500 bg-green-50'
  else if (selected && correct === false) ring = 'border-red-500 bg-red-50'
  else if (selected) ring = 'border-brand-500 bg-brand-50'

  const Wrapper = onClick ? 'button' : 'div'

  return (
    <Wrapper
      onClick={onClick}
      className={`flex flex-col items-center gap-1 rounded-xl border-2 ${ring} bg-white p-2 transition-colors ${
        onClick ? 'hover:border-brand-400' : ''
      }`}
    >
      <div className={dims}>
        {feature ? (
          <HandSkeleton feature={feature} className="h-full w-full text-brand-700" />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-xs text-gray-400">…</div>
        )}
      </div>
      {size === 'lg' && <span className="text-sm font-semibold text-brand-800">Letter {letter}</span>}
    </Wrapper>
  )
}
