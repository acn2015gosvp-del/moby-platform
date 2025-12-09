/**
 * API 응답 타입 정의
 */

export interface SuccessResponse<T> {
  success: boolean
  data: T
  message?: string
}

export interface ErrorResponse {
  success: false
  error: {
    code: string
    message: string
    field?: string
  }
  timestamp?: string
}

export interface PaginatedResponse<T> {
  success: boolean
  data: T[]
  total: number
  page: number
  page_size: number
  has_next: boolean
  has_prev: boolean
}

