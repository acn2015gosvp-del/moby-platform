/**
 * 인증 서비스
 */

import apiClient from '../api/client'
import type { LoginRequest, RegisterRequest, Token, User } from '@/types/auth'
import type { SuccessResponse } from '@/types/api'

const AUTH_ENDPOINTS = {
  REGISTER: '/auth/register',
  LOGIN: '/auth/login',
  ME: '/auth/me',
}

/**
 * 회원가입
 */
export const register = async (data: RegisterRequest): Promise<User> => {
  const response = await apiClient.post<SuccessResponse<User>>(
    AUTH_ENDPOINTS.REGISTER,
    data
  )
  return response.data.data
}

/**
 * 로그인
 */
export const login = async (data: LoginRequest): Promise<Token> => {
  const response = await apiClient.post<SuccessResponse<Token>>(
    AUTH_ENDPOINTS.LOGIN,
    data,
    {
      timeout: 60000, // 60초 타임아웃 (로그인 지연 문제 해결)
    }
  )
  return response.data.data
}

/**
 * 현재 사용자 정보 조회
 */
export const getCurrentUser = async (): Promise<User> => {
  const response = await apiClient.get<SuccessResponse<User>>(
    AUTH_ENDPOINTS.ME,
    {
      timeout: 5000, // 5초 타임아웃 (서버 응답 대기)
    }
  )
  return response.data.data
}

/**
 * 로그아웃 (클라이언트 측에서만 처리)
 */
export const logout = (): void => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

/**
 * 토큰 저장
 */
export const saveToken = (token: string): void => {
  localStorage.setItem('token', token)
}

/**
 * 토큰 가져오기
 */
export const getToken = (): string | null => {
  return localStorage.getItem('token')
}

/**
 * 사용자 정보 저장
 */
export const saveUser = (user: User): void => {
  localStorage.setItem('user', JSON.stringify(user))
}

/**
 * 저장된 사용자 정보 가져오기
 */
export const getStoredUser = (): User | null => {
  const userStr = localStorage.getItem('user')
  if (!userStr) return null
  try {
    return JSON.parse(userStr) as User
  } catch {
    return null
  }
}

