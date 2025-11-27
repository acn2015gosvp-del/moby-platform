/**
 * WebSocket Context를 통한 전역 WebSocket 상태 관리
 */

import { createContext, useContext, useCallback, useState, useEffect, useRef, type ReactNode } from 'react'
import { useWebSocket } from '@/hooks/useWebSocket'
import type { Alert } from '@/types/alert'

interface WebSocketContextValue {
  isConnected: boolean
  isConnecting: boolean
  error: Event | null
  reconnectAttempts: number
  send: (data: string | object) => boolean
  connect: () => void
  disconnect: () => void
  subscribe: (callback: (alert: Alert) => void) => () => void
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null)

interface WebSocketProviderProps {
  children: ReactNode
  enabled?: boolean
}

export function WebSocketProvider({
  children,
  enabled = true,
}: WebSocketProviderProps) {
  const [subscribers, setSubscribers] = useState<Set<(alert: Alert) => void>>(new Set())
  
  // ⚠️ 중요: subscribers를 useRef로 관리하여 항상 최신 값을 참조하도록 함
  // useCallback의 dependency에 subscribers를 넣으면 구독자가 추가될 때마다
  // handleMessage가 재생성되어 useWebSocket의 onMessage가 업데이트되지 않을 수 있음
  const subscribersRef = useRef<Set<(alert: Alert) => void>>(new Set())
  
  // subscribers가 변경될 때마다 ref 업데이트
  useEffect(() => {
    subscribersRef.current = subscribers
    console.log('[WebSocketContext] 구독자 목록 업데이트:', subscribers.size)
  }, [subscribers])

    const handleMessage = useCallback((alert: Alert) => {
      // 항상 최신 구독자 목록을 참조
      const currentSubscribers = subscribersRef.current
      console.log('[WebSocketContext] 메시지 수신, 구독자에게 전달:', {
        alertId: alert.id,
        alertType: alert.level,
        subscriberCount: currentSubscribers.size,
      })
    
    if (currentSubscribers.size === 0) {
      console.warn('[WebSocketContext] ⚠️ 구독자가 없습니다! WebSocketToast가 구독하지 않았을 수 있습니다.')
    }
    
    currentSubscribers.forEach((callback) => {
      try {
        callback(alert)
      } catch (error) {
        console.error('[WebSocketContext] 구독자 콜백 실행 중 오류:', error)
      }
    })
  }, []) // dependency 없음 - 항상 최신 subscribersRef를 참조

  const ws = useWebSocket({
    enabled,
    onMessage: handleMessage,
    onConnect: () => {
      console.log('[WebSocketContext] ✅ WebSocket 연결됨')
    },
    onDisconnect: () => {
      console.log('[WebSocketContext] ❌ WebSocket 연결 해제됨')
    },
    onError: (error) => {
      console.error('[WebSocketContext] ❌ WebSocket 에러:', error)
    },
  })
  
  // 연결 상태 변경 시 로그
  useEffect(() => {
    console.log('[WebSocketContext] 연결 상태 변경:', {
      isConnected: ws.isConnected,
      isConnecting: ws.isConnecting,
      reconnectAttempts: ws.reconnectAttempts,
      error: ws.error ? '에러 발생' : '없음',
    })
  }, [ws.isConnected, ws.isConnecting, ws.reconnectAttempts, ws.error])

  const subscribe = useCallback((callback: (alert: Alert) => void) => {
    console.log('[WebSocketContext] 구독자 등록 요청:', typeof callback)
    
    setSubscribers((prev) => {
      const next = new Set(prev)
      next.add(callback)
      console.log('[WebSocketContext] 구독자 등록 완료. 총 구독자 수:', next.size)
      return next
    })

    // 구독 해제 함수 반환
    return () => {
      console.log('[WebSocketContext] 구독자 해제 요청')
      setSubscribers((prev) => {
        const next = new Set(prev)
        next.delete(callback)
        console.log('[WebSocketContext] 구독자 해제 완료. 총 구독자 수:', next.size)
        return next
      })
    }
  }, [])

  const contextValue: WebSocketContextValue = {
    isConnected: ws.isConnected,
    isConnecting: ws.isConnecting,
    error: ws.error,
    reconnectAttempts: ws.reconnectAttempts,
    send: ws.send,
    connect: ws.connect,
    disconnect: ws.disconnect,
    subscribe,
  }

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  )
}

export function useWebSocketContext() {
  const context = useContext(WebSocketContext)
  if (!context) {
    // 개발 환경에서 더 자세한 에러 메시지 제공
    const errorMessage = 'useWebSocketContext must be used within WebSocketProvider'
    console.error(
      `[WebSocketContext] ${errorMessage}\n` +
      `컴포넌트 트리 구조를 확인하세요:\n` +
      `- WebSocketProvider가 RouterProvider보다 상위에 있어야 합니다.\n` +
      `- main.tsx에서 구조: <WebSocketProvider><RouterProvider /></WebSocketProvider>`
    )
    throw new Error(errorMessage)
  }
  return context
}

