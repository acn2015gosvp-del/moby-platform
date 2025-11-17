/**
 * Axios API 클라이언트 설정
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ErrorResponse } from '@/types/api'

// 환경 변수에서 API URL 가져오기
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Axios 인스턴스 생성
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

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
    } else {
      // 요청 설정 중 에러 발생
      console.error('Error:', error.message)
    }
    
    return Promise.reject(error)
  }
)

export default apiClient

