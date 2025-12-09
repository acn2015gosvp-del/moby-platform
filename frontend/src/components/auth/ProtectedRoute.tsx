/**
 * Protected Route 컴포넌트
 */

import { Navigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { useEffect, useState } from 'react'

interface ProtectedRouteProps {
  children: React.ReactElement
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth()
  const [timeoutReached, setTimeoutReached] = useState(false)

  // 타임아웃 설정 (5초 후 강제 진행)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (isLoading) {
        console.warn('[ProtectedRoute] 로딩 타임아웃 - 강제 진행')
        setTimeoutReached(true)
      }
    }, 5000)

    return () => clearTimeout(timer)
  }, [isLoading])

  // 로딩 중이면 최소한의 로딩 UI만 표시 (전체 블로킹 방지)
  // 타임아웃에 도달하면 강제로 진행
  if (isLoading && !timeoutReached) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
          <div className="text-gray-600">로딩 중...</div>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return children
}

export default ProtectedRoute

