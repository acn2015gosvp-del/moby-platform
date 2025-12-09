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
    reconnectInterval = 5000,  // 재연결 간격을 5초로 증가 (서버 부하 방지)
    maxReconnectAttempts = 3,  // 최대 재연결 시도 횟수를 3회로 감소
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
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const isConnectingRef = useRef(false)  // 연결 시도 중인지 추적

  const connect = useCallback(() => {
    // WebSocket 연결 시작 로그 (항상 표시)
    console.log('[useWebSocket] ========== WebSocket 연결 시도 ==========')
    console.log('[useWebSocket] URL:', url)
    console.log('[useWebSocket] Enabled:', enabled)
    console.log('[useWebSocket] 현재 연결 상태:', {
      readyState: wsRef.current?.readyState,
      isConnecting: isConnectingRef.current,
    })
    
    // 이미 연결되어 있거나 연결 시도 중이면 중복 연결 방지
    if (!enabled || wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[useWebSocket] 이미 연결되어 있음. 연결 시도 중단.')
      return
    }
    
    // 이미 연결 시도 중이면 중복 시도 방지
    if (isConnectingRef.current) {
      console.log('[useWebSocket] 이미 연결 시도 중입니다. 중복 연결 방지.')
      return
    }

    try {
      isConnectingRef.current = true
      setState((prev) => ({ ...prev, isConnecting: true, error: null }))
      
      console.log('[useWebSocket] WebSocket 인스턴스 생성 중...')

      const ws = new WebSocket(url)
      wsRef.current = ws
      
      console.log('[useWebSocket] WebSocket 인스턴스 생성 완료. 이벤트 리스너 등록 중...')

      ws.onopen = () => {
        isConnectingRef.current = false
        setState({
          isConnected: true,
          isConnecting: false,
          error: null,
          reconnectAttempts: 0,
        })
        reconnectAttemptsRef.current = 0
        console.log('[useWebSocket] ✅ ========== WebSocket 연결 성공 ==========')
        console.log('[useWebSocket] 연결 URL:', url)
        console.log('[useWebSocket] ReadyState:', ws.readyState)
        console.log('[useWebSocket] 프로토콜:', ws.protocol || '없음')
        onConnect?.()
      }

      ws.onmessage = (event) => {
        try {
          console.log('[useWebSocket] 원본 메시지 수신:', event.data)
          const rawData = JSON.parse(event.data)
          console.log('[useWebSocket] 파싱된 원본 데이터:', rawData)
          
          // CONNECTED 메시지는 연결 확인용이므로 무시 (실제 알림만 처리)
          if (rawData.type === 'CONNECTED') {
            console.log('[useWebSocket] 연결 확인 메시지 수신 (무시):', rawData.message)
            return
          }
          
          // 알림 타입 확인 (type 필드 또는 level 필드 모두 지원)
          const rawType = rawData.type?.toUpperCase()
          const rawLevel = rawData.level?.toLowerCase()
          
          // type 또는 level 필드에서 알림 타입 추출
          let alertType: string | null = null
          let alertLevel: string = 'info'
          
          if (rawType && ['CRITICAL', 'WARNING', 'NOTICE', 'RESOLVED', 'RUL_ALERT'].includes(rawType)) {
            // type 필드가 있고 유효한 경우
            alertType = rawType
            // RUL_ALERT는 warning 레벨로 매핑
            alertLevel = rawType === 'RUL_ALERT' ? 'warning' : rawType.toLowerCase()
          } else if (rawLevel && ['critical', 'warning', 'info', 'notice', 'resolved'].includes(rawLevel)) {
            // level 필드가 있고 유효한 경우
            alertLevel = rawLevel
            alertType = rawLevel.toUpperCase()
          } else if (rawType) {
            // type 필드가 있지만 알 수 없는 타입인 경우
            console.log('[useWebSocket] 알 수 없는 type 필드 (무시):', rawType)
            return
          } else if (rawLevel) {
            // level 필드가 있지만 알 수 없는 레벨인 경우
            console.log('[useWebSocket] 알 수 없는 level 필드 (무시):', rawLevel)
            return
          } else {
            // type과 level 필드가 모두 없는 경우 (메시지가 있으면 info로 처리)
            if (!rawData.message) {
              console.log('[useWebSocket] 알림 타입과 메시지가 모두 없음 (무시):', rawData)
              return
            }
            // 메시지만 있고 타입이 없으면 info로 처리
            alertType = 'NOTICE'
            alertLevel = 'info'
          }
          
          // 백엔드가 보내는 형식: { type, message, color, device_id, timestamp } 또는 { level, message, ... }
          // 프론트엔드 Alert 형식으로 변환
          const alertData: Alert & { type?: string; color?: string; device_id?: string } = {
            id: rawData.id || `ws-${Date.now()}-${Math.random()}`,
            level: (alertLevel as 'info' | 'warning' | 'critical'),
            message: rawData.message || '알림 없음',
            sensor_id: rawData.device_id || rawData.sensor_id || rawData.sensor || 'unknown',
            source: rawData.source || 'websocket',
            ts: rawData.timestamp || new Date().toISOString(),
            details: rawData.details || {},
            // 추가 필드 (백엔드 형식 지원) - WebSocketToast에서 type 필드를 확인하므로 반드시 포함
            type: alertType as 'CRITICAL' | 'WARNING' | 'NOTICE' | 'RESOLVED' | undefined,
            color: rawData.color,
            device_id: rawData.device_id || rawData.sensor_id || rawData.sensor,
          } as Alert
          
          console.log('[useWebSocket] 알림 타입 변환:', { 
            rawType, 
            rawLevel, 
            alertType, 
            alertLevel,
            message: alertData.message,
            finalType: alertData.type
          })
          
          console.log('[useWebSocket] 실제 알림 데이터 변환 완료:', alertData)
          console.log('[useWebSocket] WebSocketToast로 전달할 데이터:', JSON.stringify(alertData, null, 2))
          onMessage?.(alertData)
        } catch (err) {
          console.error('[useWebSocket] 메시지 파싱 실패:', err, event.data)
        }
      }

      ws.onerror = (error) => {
        isConnectingRef.current = false
        const errorMessage = (error instanceof Error ? error.message : (error as { message?: string })?.message) || 'Unknown error'
        console.error('[useWebSocket] WebSocket 에러:', errorMessage, error)
        
        // "Insufficient resources" 에러는 서버가 실행되지 않았거나 리소스 부족을 의미
        if (errorMessage.includes('Insufficient resources') || errorMessage.includes('failed')) {
          console.warn('[useWebSocket] 서버 연결 실패. 백엔드 서버가 실행 중인지 확인하세요.')
        }
        
        setState((prev) => ({ ...prev, error, isConnecting: false }))
        onError?.(error)
      }

      ws.onclose = (event) => {
        isConnectingRef.current = false
        console.log('[useWebSocket] WebSocket 연결 종료:', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        })
        setState((prev) => ({ ...prev, isConnected: false, isConnecting: false }))
        onDisconnect?.()

        // code 1006은 비정상 종료 (서버 미실행, 네트워크 오류 등)
        if (event.code === 1006) {
          console.warn('[useWebSocket] 비정상 종료 (code 1006). 백엔드 서버 상태를 확인하세요.')
        }

        // 정상 종료가 아니고 enabled 상태면 자동 재연결 시도
        // 단, code 1006이면 재연결 간격을 더 늘림 (서버 부하 방지)
        if (enabled && !event.wasClean && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1
          setState((prev) => ({
            ...prev,
            reconnectAttempts: reconnectAttemptsRef.current,
          }))

          // code 1006이면 재연결 간격을 3배로 증가 (서버 부하 방지)
          // "Insufficient resources" 에러는 서버가 준비되지 않았을 때 발생
          const retryInterval = event.code === 1006 ? reconnectInterval * 3 : reconnectInterval
          console.log(`[useWebSocket] ${retryInterval}ms 후 재연결 시도 (${reconnectAttemptsRef.current}/${maxReconnectAttempts})`)
          console.warn('[useWebSocket] 백엔드 서버가 실행 중인지 확인하세요. 서버를 재시작한 후 다시 시도하세요.')
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, retryInterval)
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          console.error('[useWebSocket] 최대 재연결 시도 횟수 초과. 백엔드 서버를 재시작하고 페이지를 새로고침하세요.')
          // 재연결 시도 중단
          isConnectingRef.current = false
        }
      }
    } catch (error) {
      isConnectingRef.current = false
      console.error('[useWebSocket] WebSocket 생성 실패:', error)
      setState((prev) => ({
        ...prev,
        error: error as Event,
        isConnecting: false,
      }))
      onError?.(error as Event)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, reconnectInterval, maxReconnectAttempts, enabled])  // callback 함수들을 dependency에서 제거하여 불필요한 재생성 방지

  const disconnect = useCallback(() => {
    isConnectingRef.current = false
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      // 연결 상태 확인 후 안전하게 닫기
      const ws = wsRef.current
      if (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN) {
        console.log('[useWebSocket] WebSocket 연결 해제 중...')
        ws.close(1000, 'Client disconnect')  // 정상 종료 코드
      }
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
    // enabled가 변경될 때만 연결/해제
    let timer: ReturnType<typeof setTimeout> | null = null
    
    if (enabled) {
      // WebSocket 연결을 약간 지연시켜 초기 로딩에 영향 없도록 함
      timer = setTimeout(() => {
        connect()
      }, 500) // 500ms 지연 (초기 로딩 최적화)
    } else {
      disconnect()
    }

    return () => {
      // 타이머 정리
      if (timer) {
        clearTimeout(timer)
      }
      // ⚠️ 중요: cleanup은 실제 컴포넌트 언마운트 시에만 실행되어야 함
      // React StrictMode에서는 개발 모드에서 useEffect가 두 번 실행되지만,
      // cleanup은 실제 언마운트 시에만 실행됨
      
      // enabled가 false로 변경된 경우에만 cleanup 실행
      // enabled가 true인 상태에서 cleanup이 호출되는 것은 React StrictMode의 더블 마운트일 수 있음
      if (!enabled) {
        console.log('[useWebSocket] Cleanup: enabled=false로 변경되어 연결 해제')
        disconnect()
        return
      }
      
      // enabled가 true인데 cleanup이 호출되는 경우
      // React StrictMode의 더블 마운트일 가능성이 높으므로, 연결을 유지
      // 실제 언마운트인지 확인하기 위해 짧은 지연 후 확인
      const currentWs = wsRef.current
      const currentReadyState = currentWs?.readyState
      
      console.log('[useWebSocket] Cleanup 호출됨 (enabled=true). 연결 상태 확인:', {
        readyState: currentReadyState,
        isConnecting: isConnectingRef.current,
        isConnected: currentReadyState === WebSocket.OPEN
      })
      
      // React StrictMode에서 cleanup이 두 번 호출되는 것을 방지
      // enabled가 true인 상태에서 cleanup이 호출되면, React StrictMode의 더블 마운트일 가능성이 높음
      // 실제 언마운트인지 확인하기 위해 짧은 지연 후 확인
      if (currentReadyState === WebSocket.OPEN || currentReadyState === WebSocket.CONNECTING) {
        console.log('[useWebSocket] Cleanup: 연결 상태 확인 중... (React StrictMode 대응)')
        
        // React StrictMode는 매우 빠르게 재마운트하므로, 
        // cleanup을 실행하지 않고 연결을 유지하는 것이 더 안전함
        // 실제 언마운트는 enabled가 false로 변경될 때만 발생함
        console.log('[useWebSocket] Cleanup: React StrictMode 더블 마운트로 판단, 연결 유지')
        
        // 재연결 타이머만 정리 (연결은 유지)
        // cleanup을 실행하지 않음
        return
      } else {
        // 이미 닫혀있거나 없으면 정리만
        console.log('[useWebSocket] Cleanup: WebSocket이 이미 닫혀있음, 정리만 수행')
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current)
          reconnectTimeoutRef.current = null
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled])  // enabled만 dependency로 사용 (connect, disconnect는 ref로 관리)

  return {
    ...state,
    connect,
    disconnect,
    send,
  }
}

