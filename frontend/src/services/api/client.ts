/**
 * Axios API 클라이언트 설정
 */

import axios, { type AxiosResponse } from 'axios'
import type { ErrorResponse } from '@/types/api'

// 환경 변수에서 API URL 가져오기
// 프록시를 사용하므로 /api로 설정 (vite.config.ts의 proxy 설정 사용)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

/**
 * Axios 인스턴스 생성
 */
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60초로 증가 (로그인 지연 문제 해결)
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * CSRF 토큰 가져오기
 */
function getCsrfToken(): string | null {
  // 쿠키에서 CSRF 토큰 읽기
  const cookies = document.cookie.split(';')
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=')
    if (name === 'csrf_token') {
      return decodeURIComponent(value)
    }
  }
  return null
}

/**
 * 요청 인터셉터
 */
apiClient.interceptors.request.use(
  (config) => {
    // 인증 토큰 추가
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // CSRF 토큰 추가 (GET 요청이 아닌 경우)
    if (config.method && !['get', 'head', 'options'].includes(config.method.toLowerCase())) {
      const csrfToken = getCsrfToken()
      if (csrfToken) {
        config.headers['X-CSRF-Token'] = csrfToken
      }
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

/**
 * 응답 인터셉터
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error) => {
    // 에러 처리
    if (error.response) {
      // 서버에서 응답이 온 경우
      const errorResponse: ErrorResponse = error.response.data
      console.error('API Error:', errorResponse)
      
      // 401 Unauthorized - 인증 실패
      if (error.response.status === 401) {
        // 토큰 제거 및 로그인 페이지로 리다이렉트
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        delete apiClient.defaults.headers.common['Authorization']
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
      
      // 500 Internal Server Error
      if (error.response.status === 500) {
        console.error('Internal Server Error')
      }
    } else if (error.request) {
      // 요청은 보냈지만 응답을 받지 못한 경우
      console.error('Network Error:', error.request)
      
      // 타임아웃 오류 처리
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        console.error('Request timeout - 서버 응답이 너무 느립니다.')
      } else if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
        console.error('Network connection failed - 백엔드 서버가 실행 중인지 확인하세요.')
      }
    } else {
      // 요청 설정 중 에러 발생
      console.error('Error:', error.message)
    }
    
    return Promise.reject(error)
  }
)

export default apiClient

