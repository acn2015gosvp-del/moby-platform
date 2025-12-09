/**
 * 공통 타입 정의
 */

export type LoadingState = 'idle' | 'loading' | 'success' | 'error'

export interface ApiError {
  code: string
  message: string
  field?: string
}

