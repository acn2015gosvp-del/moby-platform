/**
 * 라우터 설정
 * 설비 중심(Device-Centric) 구조로 중첩 라우팅 적용
 */

import { lazy, Suspense, type ReactNode } from 'react'
import { createBrowserRouter, Navigate } from 'react-router-dom'
import App from './App'
import Loading from './components/common/Loading'
import ProtectedRoute from './components/auth/ProtectedRoute'

// 레이지 로딩을 위한 컴포넌트
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Alerts = lazy(() => import('./pages/Alerts'))
const Reports = lazy(() => import('./pages/Reports'))
const EquipmentList = lazy(() => import('./pages/EquipmentList'))
const Monitoring = lazy(() => import('./pages/Monitoring'))
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))

// 로딩 래퍼 컴포넌트를 별도 파일로 분리하여 Fast Refresh 경고 해결
// eslint-disable-next-line react-refresh/only-export-components
function LazyWrapper({ children }: { children: ReactNode }) {
  return (
    <Suspense fallback={<Loading message="페이지를 불러오는 중..." />}>
      {children}
    </Suspense>
  )
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: (
      <LazyWrapper>
        <Login />
      </LazyWrapper>
    ),
  },
  {
    path: '/register',
    element: (
      <LazyWrapper>
        <Register />
      </LazyWrapper>
    ),
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <App />
      </ProtectedRoute>
    ),
    children: [
      // 설비 목록 페이지 (진입점)
      {
        index: true,
        element: (
          <LazyWrapper>
            <EquipmentList />
          </LazyWrapper>
        ),
      },
      {
        path: 'devices',
        element: (
          <LazyWrapper>
            <EquipmentList />
          </LazyWrapper>
        ),
      },
      // 설비별 중첩 라우팅
      {
        path: 'devices/:deviceId',
        children: [
          {
            index: true,
            element: <Navigate to="dashboard" replace />,
          },
          {
            path: 'dashboard',
            element: (
              <LazyWrapper>
                <Dashboard />
              </LazyWrapper>
            ),
          },
          {
            path: 'alerts',
            element: (
              <LazyWrapper>
                <Alerts />
              </LazyWrapper>
            ),
          },
          {
            path: 'reports',
            element: (
              <LazyWrapper>
                <Reports />
              </LazyWrapper>
            ),
          },
          {
            path: 'monitoring',
            element: (
              <LazyWrapper>
                <Monitoring />
              </LazyWrapper>
            ),
          },
        ],
      },
      // 기존 경로 호환성 (리다이렉트)
      {
        path: 'alerts',
        element: <Navigate to="/devices" replace />,
      },
      {
        path: 'reports',
        element: <Navigate to="/devices" replace />,
      },
      {
        path: 'monitoring/:deviceId?',
        element: <Navigate to="/devices" replace />,
      },
    ],
  },
])

