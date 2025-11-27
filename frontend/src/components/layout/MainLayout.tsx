/**
 * 메인 레이아웃 컴포넌트
 */

import { useState, useEffect, useMemo } from 'react'
import type { ReactNode } from 'react'
import Header from './Header'
import Sidebar from './Sidebar'
import { AlertTicker } from '../alerts/AlertTicker'
import { useWebSocketContext } from '@/context/WebSocketContext'
import type { Alert } from '@/types/alert'

interface MainLayoutProps {
  children: ReactNode
}

function MainLayout({ children }: MainLayoutProps) {
  const [alerts, setAlerts] = useState<Alert[]>([])
  
  // WebSocketContext 사용 (WebSocketProvider 안에서만 호출되어야 함)
  const { subscribe } = useWebSocketContext()

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

  // critical 알림 확인
  const hasCriticalAlerts = useMemo(
    () => alerts.some((alert) => alert.level === 'critical'),
    [alerts]
  )

  return (
    <div className={`min-h-screen bg-gray-50 ${hasCriticalAlerts ? 'critical-flash' : ''}`}>
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6 pb-20">
          {children}
        </main>
      </div>
      {/* 하단 알림 티커 */}
      <AlertTicker alerts={alerts} />
    </div>
  )
}

export default MainLayout

