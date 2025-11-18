/**
 * WebSocket Context를 통한 전역 WebSocket 상태 관리
 */

import { createContext, useContext, useCallback, useState, type ReactNode } from 'react'
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

  const handleMessage = useCallback((alert: Alert) => {
    subscribers.forEach((callback) => callback(alert))
  }, [subscribers])

  const ws = useWebSocket({
    enabled,
    onMessage: handleMessage,
  })

  const subscribe = useCallback((callback: (alert: Alert) => void) => {
    setSubscribers((prev) => {
      const next = new Set(prev)
      next.add(callback)
      return next
    })

    // 구독 해제 함수 반환
    return () => {
      setSubscribers((prev) => {
        const next = new Set(prev)
        next.delete(callback)
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
    throw new Error('useWebSocketContext must be used within WebSocketProvider')
  }
  return context
}

