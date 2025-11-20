/**
 * 라우터 설정
 * 코드 스플리팅 및 레이지 로딩 적용
 */

import { lazy, Suspense, type ReactNode } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import App from './App'
import Loading from './components/common/Loading'
import ProtectedRoute from './components/auth/ProtectedRoute'

// 레이지 로딩을 위한 컴포넌트
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Alerts = lazy(() => import('./pages/Alerts'))
const Sensors = lazy(() => import('./pages/Sensors'))
const Reports = lazy(() => import('./pages/Reports'))
const EquipmentList = lazy(() => import('./pages/EquipmentList'))
const Monitoring = lazy(() => import('./pages/Monitoring'))
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))

// 로딩 래퍼 컴포넌트
const LazyWrapper = ({ children }: { children: ReactNode }) => (
  <Suspense fallback={<Loading message="페이지를 불러오는 중..." />}>
    {children}
  </Suspense>
)

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
      {
        index: true,
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
        path: 'sensors',
        element: (
          <LazyWrapper>
            <Sensors />
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
        path: 'equipment',
        element: (
          <LazyWrapper>
            <EquipmentList />
          </LazyWrapper>
        ),
      },
      {
        path: 'monitoring/:deviceId?',
        element: (
          <LazyWrapper>
            <Monitoring />
          </LazyWrapper>
        ),
      },
    ],
  },
])

