import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { WebSocketProvider } from './context/WebSocketContext'
import { AlertMuteProvider } from './context/AlertMuteContext'
import { WebSocketToast } from './components/alerts/WebSocketToast'
import { ThemeProvider } from './context/ThemeContext'
import './index.css'
import { router } from './router'

// ⚠️ 중요: WebSocketProvider는 RouterProvider 안의 모든 컴포넌트가 접근할 수 있도록
// RouterProvider보다 상위에 위치해야 합니다.

console.log('[main.tsx] ========== 앱 시작 ==========')
console.log('[main.tsx] 현재 URL:', window.location.href)
console.log('[main.tsx] document.readyState:', document.readyState)

const rootElement = document.getElementById('root')

if (!rootElement) {
  console.error('[main.tsx] ❌ root 엘리먼트를 찾을 수 없습니다!')
  console.error('[main.tsx] document.body:', document.body)
  console.error('[main.tsx] document.documentElement:', document.documentElement)
  throw new Error('root 엘리먼트를 찾을 수 없습니다!')
}

console.log('[main.tsx] ✅ root 엘리먼트 찾음:', rootElement)
console.log('[main.tsx] root 엘리먼트 내용:', rootElement.innerHTML.substring(0, 100))

// 개발 모드에서만 StrictMode 사용 (프로덕션 성능 최적화)
const AppRoot = (
  <ThemeProvider>
    <AuthProvider>
      <AlertMuteProvider>
        <WebSocketProvider enabled={true}>
          <WebSocketToast />
          <RouterProvider router={router} />
        </WebSocketProvider>
      </AlertMuteProvider>
    </AuthProvider>
  </ThemeProvider>
)

console.log('[main.tsx] React 앱 렌더링 시작...')

try {
  const root = createRoot(rootElement)
  
  root.render(
    import.meta.env.DEV ? (
      <StrictMode>{AppRoot}</StrictMode>
    ) : (
      AppRoot
    )
  )
  
  console.log('[main.tsx] ✅ React 앱 렌더링 완료')
} catch (error) {
  console.error('[main.tsx] ❌ React 앱 렌더링 실패:', error)
  console.error('[main.tsx] 오류 상세:', error instanceof Error ? error.stack : error)
  
  // 오류 발생 시 사용자에게 표시
  rootElement.innerHTML = `
    <div style="padding: 20px; font-family: sans-serif;">
      <h1 style="color: red;">앱 로딩 오류</h1>
      <p>React 앱을 렌더링하는 중 오류가 발생했습니다.</p>
      <p style="color: #666; font-size: 12px;">${error instanceof Error ? error.message : String(error)}</p>
      <button onclick="window.location.reload()" style="margin-top: 20px; padding: 10px 20px; background: #007AFF; color: white; border: none; border-radius: 5px; cursor: pointer;">
        페이지 새로고침
      </button>
    </div>
  `
  throw error
}
