import { Link } from 'react-router-dom'
import type { Lesson } from '../types'

const CATEGORY_ICONS: Record<string, string> = {
  greetings_courtesy: '👋',
  family_people: '👪',
  needs_requests: '🙏',
  feelings_emotions: '😊',
  question_words: '❓',
  everyday_actions: '🏃',
  descriptions_opposites: '⚖️',
  colors: '🎨',
  time_words: '⏰',
  home_things: '🏠',
}

interface JourneyNode {
  key: string
  title: string
  icon: string
  status: 'locked' | 'unlocked' | 'completed'
  linkTo: string | null
}

/**
 * Visual path across real vocabulary areas already supported by the
 * 114-word manifest (no invented "Food"/"School" categories with no real
 * content behind them) — Alphabet first, then each vocabulary category in
 * its existing, already-pedagogically-ordered order_index. Lock/unlock/
 * completed status is read directly from the same lesson data LessonPath
 * already fetches (categories unlock sequentially on completing the
 * previous one — this reflects real backend state, not a fake progression).
 */
export function AslJourney({ lessons }: { lessons: Lesson[] }) {
  const alphabet = lessons.filter((l) => l.lesson_type === 'alphabet')
  const vocabulary = lessons
    .filter((l) => l.lesson_type === 'vocabulary')
    .sort((a, b) => a.order_index - b.order_index)

  const alphabetCompleted = alphabet.length > 0 && alphabet.every((l) => l.status === 'completed')
  const alphabetStarted = alphabet.some((l) => l.status !== 'locked')

  const nodes: JourneyNode[] = [
    {
      key: 'alphabet',
      title: 'Alphabet',
      icon: '🔤',
      status: alphabetCompleted ? 'completed' : alphabetStarted ? 'unlocked' : 'locked',
      linkTo: alphabet.length > 0 ? `/learn/${alphabet.find((l) => l.status !== 'locked')?.id ?? alphabet[0].id}` : null,
    },
    ...vocabulary.map((lesson) => ({
      key: lesson.concept_key ?? String(lesson.id),
      title: lesson.title,
      icon: (lesson.concept_key && CATEGORY_ICONS[lesson.concept_key]) || '📖',
      status: lesson.status,
      linkTo: lesson.status !== 'locked' ? `/learn/${lesson.id}` : null,
    })),
  ]

  return (
    <div className="mb-10">
      <h2 className="mb-3 text-lg font-semibold text-brand-800">Your ASL Journey</h2>
      <div className="flex gap-2 overflow-x-auto pb-2">
        {nodes.map((node, i) => (
          <div key={node.key} className="flex items-center">
            <JourneyNodeView node={node} />
            {i < nodes.length - 1 && (
              <div className={`mx-1 h-0.5 w-6 shrink-0 ${node.status === 'completed' ? 'bg-brand-400' : 'bg-gray-200'}`} />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function JourneyNodeView({ node }: { node: JourneyNode }) {
  const base =
    'flex w-20 shrink-0 flex-col items-center gap-1 rounded-2xl border-2 p-2 text-center transition-transform'
  const style =
    node.status === 'locked'
      ? 'border-gray-200 bg-gray-100 text-gray-400'
      : node.status === 'completed'
        ? 'border-brand-400 bg-brand-500 text-white hover:scale-105'
        : 'border-brand-300 bg-white text-brand-700 hover:scale-105'

  const content = (
    <>
      <span className="text-2xl">{node.status === 'locked' ? '🔒' : node.icon}</span>
      <span className="line-clamp-2 text-[10px] font-medium leading-tight">{node.title}</span>
      {node.status === 'completed' && <span className="text-xs">✓</span>}
    </>
  )

  if (!node.linkTo) return <div className={`${base} ${style}`}>{content}</div>
  return (
    <Link to={node.linkTo} className={`${base} ${style}`}>
      {content}
    </Link>
  )
}
