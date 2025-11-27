import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { WebSocketProvider } from './context/WebSocketContext'
import { WebSocketToast } from './components/alerts/WebSocketToast'
import './index.css'
import { router } from './router'

// ⚠️ 중요: WebSocketProvider는 RouterProvider 안의 모든 컴포넌트가 접근할 수 있도록
// RouterProvider보다 상위에 위치해야 합니다.
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <WebSocketProvider enabled={true}>
        <WebSocketToast />
        <RouterProvider router={router} />
      </WebSocketProvider>
    </AuthProvider>
  </StrictMode>,
)
