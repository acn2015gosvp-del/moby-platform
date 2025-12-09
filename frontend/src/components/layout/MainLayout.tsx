/**
 * 메인 레이아웃 컴포넌트
 */

import { useState, useEffect, useMemo } from 'react'
import type { ReactNode } from 'react'
import Header from './Header'
import Sidebar from './Sidebar'
import { AlertTicker } from '../alerts/AlertTicker'
import { useWebSocketContext } from '@/context/WebSocketContext'
import { useAlertMute } from '@/context/AlertMuteContext'
import type { Alert } from '@/types/alert'

interface MainLayoutProps {
  children: ReactNode
}

function MainLayout({ children }: MainLayoutProps) {
  const [alerts, setAlerts] = useState<Alert[]>([])
  
  // WebSocketContext 사용 (WebSocketProvider 안에서만 호출되어야 함)
  const { subscribe } = useWebSocketContext()
  
  // 알림 음소거 상태
  const { isMuted } = useAlertMute()

  // WebSocket에서 알림 수신
  useEffect(() => {
    console.log('[MainLayout] WebSocket 구독 시작...')
    const unsubscribe = subscribe((alert: Alert) => {
      console.log('[MainLayout] 알림 수신:', alert)
      setAlerts((prev) => {
        // 최신 알림을 앞에 추가하고, 최대 20개만 유지
        const updated = [alert, ...prev].slice(0, 20)
        return updated
      })
    })

    console.log('[MainLayout] WebSocket 구독 완료')
    return unsubscribe
  }, [subscribe])

  // critical 알림 확인 (level과 type 모두 확인)
  const hasCriticalAlerts = useMemo(
    () => alerts.some((alert) => {
      // level 필드 확인 (기존 형식)
      if (alert.level === 'critical') {
        return true
      }
      // type 필드 확인 (신규 형식: CRITICAL)
      if ((alert as any).type === 'CRITICAL') {
        return true
      }
      return false
    }),
    [alerts]
  )

  return (
    <>
      {/* Critical 알림 오버레이 (화면 전체를 덮는 빨간색 효과) - 음소거 상태가 아닐 때만 표시 */}
      {hasCriticalAlerts && !isMuted && (
        <div className="fixed inset-0 pointer-events-none z-[9999] critical-overlay" />
      )}
      <div className={`min-h-screen bg-background-main text-text-primary ${hasCriticalAlerts && !isMuted ? 'critical-flash' : ''}`}>
        <Header />
        <div className="flex w-full h-[calc(100vh-64px)]">
          <Sidebar />
          <main className="flex-1 w-full max-w-full overflow-hidden">
            {children}
          </main>
        </div>
        {/* 하단 알림 티커 */}
        <AlertTicker alerts={alerts} />
      </div>
    </>
  )
}

export default MainLayout

