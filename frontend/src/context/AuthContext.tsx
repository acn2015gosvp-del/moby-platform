/**
 * 인증 Context
 */

import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import type { User, LoginRequest, RegisterRequest } from '@/types/auth'
import * as authService from '@/services/auth/authService'
import apiClient from '@/services/api/client'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (data: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // 저장된 사용자 정보로 즉시 초기화하여 UI 블로킹 방지
  const [user, setUser] = useState<User | null>(() => {
    // 초기 렌더링 시 한 번만 실행
    const storedUser = authService.getStoredUser()
    const token = authService.getToken()
    if (token && storedUser) {
      // 토큰이 있으면 API 클라이언트에 즉시 설정
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
    return storedUser
  })
  
  // 즉시 false로 설정하여 로딩 화면 방지
  const [isLoading] = useState(false)

  // 초기화: 사용자 정보 재확인 (백그라운드에서만)
  useEffect(() => {
    const token = authService.getToken()
    const storedUser = authService.getStoredUser()
    
    if (token && storedUser) {
      // 사용자 정보 재확인은 백그라운드에서 수행
      // 실패해도 UI는 이미 표시되었으므로 사용자 경험에 영향 없음
      let isCancelled = false
      
      const timeoutId = setTimeout(() => {
        authService.getCurrentUser()
          .then((currentUser) => {
            if (!isCancelled) {
              setUser(currentUser)
              authService.saveUser(currentUser)
            }
          })
          .catch((error) => {
            // 토큰이 유효하지 않으면 조용히 로그아웃
            if (!isCancelled) {
              console.warn('[AuthContext] 사용자 정보 재확인 실패:', error)
              authService.logout()
              setUser(null)
              delete apiClient.defaults.headers.common['Authorization']
            }
          })
      }, 100) // 100ms 후 백그라운드에서 실행
      
      return () => {
        isCancelled = true
        clearTimeout(timeoutId)
      }
    }
  }, [])

  // 로그인
  const handleLogin = async (data: LoginRequest) => {
    const token = await authService.login(data)
    authService.saveToken(token.access_token)
    
    // API 클라이언트에 토큰 설정
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token.access_token}`
    
    // 사용자 정보 조회
    const currentUser = await authService.getCurrentUser()
    setUser(currentUser)
    authService.saveUser(currentUser)
  }

  // 회원가입
  const handleRegister = async (data: RegisterRequest) => {
    await authService.register(data)
    // 회원가입 후 자동 로그인
    await handleLogin({ email: data.email, password: data.password })
  }

  // 로그아웃
  const handleLogout = () => {
    authService.logout()
    setUser(null)
    delete apiClient.defaults.headers.common['Authorization']
  }

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// Fast refresh 경고: hook과 컴포넌트를 같은 파일에서 export하는 것은 허용됨
// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

