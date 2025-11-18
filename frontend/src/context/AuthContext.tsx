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
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // 초기화: 저장된 토큰과 사용자 정보 확인
  useEffect(() => {
    const initAuth = async () => {
      const token = authService.getToken()
      const storedUser = authService.getStoredUser()

      if (token && storedUser) {
        // 토큰이 있으면 API 클라이언트에 설정
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
        
        // 사용자 정보 재확인
        try {
          const currentUser = await authService.getCurrentUser()
          setUser(currentUser)
          authService.saveUser(currentUser)
        } catch (error) {
          // 토큰이 유효하지 않으면 로그아웃
          authService.logout()
          delete apiClient.defaults.headers.common['Authorization']
        }
      }
      
      setIsLoading(false)
    }

    initAuth()
  }, [])

  // 로그인
  const handleLogin = async (data: LoginRequest) => {
    try {
      const token = await authService.login(data)
      authService.saveToken(token.access_token)
      
      // API 클라이언트에 토큰 설정
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token.access_token}`
      
      // 사용자 정보 조회
      const currentUser = await authService.getCurrentUser()
      setUser(currentUser)
      authService.saveUser(currentUser)
    } catch (error) {
      throw error
    }
  }

  // 회원가입
  const handleRegister = async (data: RegisterRequest) => {
    try {
      await authService.register(data)
      // 회원가입 후 자동 로그인
      await handleLogin({ email: data.email, password: data.password })
    } catch (error) {
      throw error
    }
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

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

