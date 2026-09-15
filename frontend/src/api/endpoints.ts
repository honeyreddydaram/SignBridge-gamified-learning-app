import { apiClient } from './client'
import type {
  Achievement,
  InterpretResponse,
  Lesson,
  LessonCompletionResult,
  LessonExercisesResponse,
  ReferenceLandmarks,
  RecognitionResult,
  SupportedSignEntry,
  UserProfile,
} from '../types'

export const authApi = {
  signup: (email: string, username: string, password: string) =>
    apiClient.post<{ access_token: string }>('/auth/signup', { email, username, password }),
  login: (email: string, password: string) =>
    apiClient.post<{ access_token: string }>('/auth/login', { email, password }),
}

export const usersApi = {
  me: () => apiClient.get<UserProfile>('/users/me'),
  achievements: () => apiClient.get<Achievement[]>('/users/me/achievements'),
}

export const lessonsApi = {
  list: () => apiClient.get<Lesson[]>('/lessons'),
  exercises: (lessonId: number) => apiClient.get<LessonExercisesResponse>(`/lessons/${lessonId}/exercises`),
  complete: (lessonId: number, correctCount: number, totalCount: number) =>
    apiClient.post<LessonCompletionResult>(`/lessons/${lessonId}/complete`, {
      correct_count: correctCount,
      total_count: totalCount,
    }),
}

export const recognitionApi = {
  status: () => apiClient.get<{ ready: boolean; error: string | null }>('/recognition/status'),
  predict: (imageBase64: string, targetLetter?: string, lessonId?: number) =>
    apiClient.post<RecognitionResult>('/recognition/predict', {
      image_base64: imageBase64,
      target_letter: targetLetter ?? null,
      lesson_id: lessonId ?? null,
    }),
  referenceSigns: () => apiClient.get<ReferenceLandmarks>('/recognition/reference-signs'),
}

export const interpretationApi = {
  interpret: (text: string) => apiClient.post<InterpretResponse>('/interpretation/interpret', { text }),
  supportedSigns: () =>
    apiClient.get<{ count: number; total_vocabulary_count: number; words: SupportedSignEntry[] }>(
      '/interpretation/supported-signs',
    ),
}
