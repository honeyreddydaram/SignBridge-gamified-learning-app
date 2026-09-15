export interface UserProfile {
  id: number
  email: string
  username: string
  created_at: string
  xp_total: number
  level: number
  hearts: number
  current_streak: number
  longest_streak: number
  last_activity_date: string | null
}

export type LessonStatus = 'locked' | 'unlocked' | 'completed'

export interface Lesson {
  id: number
  letter: string
  order_index: number
  title: string
  description: string
  status: LessonStatus
  best_score_pct: number
  attempts: number
  completed_at: string | null
}

export interface LearnCardExercise {
  type: 'learn_card'
  letter: string
  description: string
}

export interface SignIdentificationExercise {
  type: 'sign_identification_mcq'
  prompt: string
  shown_sign_letter: string
  options: string[]
  correct_option: string
}

export interface LetterToSignExercise {
  type: 'letter_to_sign_mcq'
  prompt: string
  shown_letter: string
  options: string[]
  correct_option: string
}

export interface CameraChallengeExercise {
  type: 'camera_challenge'
  prompt: string
  target_letter: string
}

export type Exercise =
  | LearnCardExercise
  | SignIdentificationExercise
  | LetterToSignExercise
  | CameraChallengeExercise

export interface LessonExercisesResponse {
  lesson: Lesson
  exercises: Exercise[]
}

export interface LessonCompletionResult {
  lesson: Lesson
  xp_awarded: number
  newly_unlocked_lesson_ids: number[]
  new_achievements: string[]
  leveled_up: boolean
  level: number
  xp_total: number
}

export interface Achievement {
  code: string
  title: string
  description: string
  icon: string
  earned_at: string
}

export interface RecognitionResult {
  hand_detected: boolean
  predicted_letter: string | null
  confidence: number
  is_confident: boolean
  correct: boolean | null
}

export interface ReferenceLandmark {
  source_path: string
  feature: number[] // 63 values: 21 landmarks x (x,y,z), wrist-origin + scale normalized
}

export type ReferenceLandmarks = Record<string, ReferenceLandmark>

export type InterpretSegmentKind = 'sign' | 'fingerspell' | 'space'

export interface SignVideo {
  provider: string
  video_id: string
  watch_url: string
  embed_url: string
  source_title: string
  source_channel: string
}

export interface InterpretSegment {
  kind: InterpretSegmentKind
  word: string
  description?: string | null
  video?: SignVideo | null
  letters?: string[] | null
}

export interface SupportedSignEntry {
  word: string
  description: string
  source_channel: string
}

export interface InterpretResponse {
  segments: InterpretSegment[]
  is_full_grammatical_asl: boolean
  disclaimer: string
}
