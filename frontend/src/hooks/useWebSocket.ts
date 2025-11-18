/**
 * WebSocket 연결 관리를 위한 커스텀 훅
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import { WS_BASE_URL } from '@/utils/constants'
import type { Alert } from '@/types/alert'

export interface UseWebSocketOptions {
  url?: string
  reconnectInterval?: number
  maxReconnectAttempts?: number
  onMessage?: (data: Alert) => void
  onError?: (error: Event) => void
  onConnect?: () => void
  onDisconnect?: () => void
  enabled?: boolean
}

export interface WebSocketState {
  isConnected: boolean
  isConnecting: boolean
  error: Event | null
  reconnectAttempts: number
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    url = WS_BASE_URL,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onMessage,
    onError,
    onConnect,
    onDisconnect,
    enabled = true,
  } = options

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    reconnectAttempts: 0,
  })

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)

  const connect = useCallback(() => {
    if (!enabled || wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      setState((prev) => ({ ...prev, isConnecting: true, error: null }))

      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setState({
          isConnected: true,
          isConnecting: false,
          error: null,
          reconnectAttempts: 0,
        })
        reconnectAttemptsRef.current = 0
        onConnect?.()
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as Alert
          onMessage?.(data)
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      ws.onerror = (error) => {
        setState((prev) => ({ ...prev, error, isConnecting: false }))
        onError?.(error)
      }

      ws.onclose = () => {
        setState((prev) => ({ ...prev, isConnected: false, isConnecting: false }))
        onDisconnect?.()

        // 자동 재연결 시도
        if (enabled && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1
          setState((prev) => ({
            ...prev,
            reconnectAttempts: reconnectAttemptsRef.current,
          }))

          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        }
      }
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error: error as Event,
        isConnecting: false,
      }))
      onError?.(error as Event)
    }
  }, [url, reconnectInterval, maxReconnectAttempts, onMessage, onError, onConnect, onDisconnect, enabled])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    setState({
      isConnected: false,
      isConnecting: false,
      error: null,
      reconnectAttempts: 0,
    })
    reconnectAttemptsRef.current = 0
  }, [])

  const send = useCallback((data: string | object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const message = typeof data === 'string' ? data : JSON.stringify(data)
      wsRef.current.send(message)
      return true
    }
    return false
  }, [])

  useEffect(() => {
    if (enabled) {
      connect()
    } else {
      disconnect()
    }

    return () => {
      disconnect()
    }
  }, [enabled, connect, disconnect])

  return {
    ...state,
    connect,
    disconnect,
    send,
  }
}

