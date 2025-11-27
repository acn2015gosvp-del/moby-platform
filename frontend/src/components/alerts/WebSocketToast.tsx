/**
 * WebSocket Toast 알림 컴포넌트
 * 
 * 백엔드에서 전송한 WebSocket 메시지를 react-toastify로 표시합니다.
 * type에 따라 색상과 유지 시간이 다르게 설정됩니다.
 * 
 * 지원 형식:
 * - 신규 형식: { type: "CRITICAL" | "WARNING" | "NOTICE" | "RESOLVED", message: "...", color: "..." }
 * - 기존 형식: { level: "critical" | "warning" | "info", message: "..." }
 */

import { useEffect } from 'react'
import { toast, ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import { useWebSocketContext } from '@/context/WebSocketContext'

interface WebSocketAlert {
  type?: 'CRITICAL' | 'WARNING' | 'NOTICE' | 'RESOLVED'
  message: string
  color?: string
  device_id?: string
  timestamp?: string
  // 기존 형식 지원
  level?: 'critical' | 'warning' | 'info'
}

export function WebSocketToast() {
  const { subscribe, isConnected } = useWebSocketContext()

  useEffect(() => {
    console.log('[WebSocketToast] ========== WebSocketToast 초기화 ==========')
    console.log('[WebSocketToast] 연결 상태:', isConnected)
    console.log('[WebSocketToast] subscribe 함수:', typeof subscribe)
    
    // ⚠️ 중요: isConnected와 관계없이 구독을 먼저 등록해야 함
    // isConnected가 false일 때 early return하면 구독이 등록되지 않음
    console.log('[WebSocketToast] 구독자 등록 시작...')

    // WebSocket 메시지 구독 (연결 상태와 관계없이 등록)
    const unsubscribe = subscribe((alert: any) => {
      console.log('[WebSocketToast] ✅ 구독 콜백 호출됨! 알림 수신:', alert)
      console.log('[WebSocketToast] 알림 수신:', alert)
      try {
        const wsAlert = alert as WebSocketAlert

        // CONNECTED 메시지는 무시 (연결 확인용)
        if (wsAlert.type === 'CONNECTED') {
          console.log('[WebSocketToast] CONNECTED 메시지 무시:', wsAlert.message)
          return
        }

        // 신규 형식 (type 필드 사용) - CRITICAL, WARNING, NOTICE, RESOLVED 처리
        if (wsAlert.type && ['CRITICAL', 'WARNING', 'NOTICE', 'RESOLVED'].includes(wsAlert.type)) {
          switch (wsAlert.type) {
            case 'CRITICAL':
              console.log('[WebSocketToast] CRITICAL 알림 표시:', wsAlert.message)
              toast.error(wsAlert.message, {
                position: 'top-right',
                autoClose: 10000, // 10초
                hideProgressBar: false,
                closeOnClick: true,
                pauseOnHover: true,
                draggable: true,
                style: {
                  backgroundColor: '#fee2e2',
                  color: '#991b1b',
                  borderLeft: '4px solid #dc2626',
                },
              })
              break

            case 'WARNING':
              console.log('[WebSocketToast] WARNING 알림 표시:', wsAlert.message)
              toast.warning(wsAlert.message, {
                position: 'top-right',
                autoClose: 5000, // 5초 (AI 예지보전 알림용)
                hideProgressBar: false,
                closeOnClick: true,
                pauseOnHover: true,
                draggable: true,
                style: {
                  backgroundColor: '#fef3c7', // 노란색 배경
                  color: '#92400e', // 진한 갈색 텍스트
                  borderLeft: '4px solid #f59e0b', // 주황색 테두리
                },
              })
              break

            case 'NOTICE':
              console.log('[WebSocketToast] NOTICE 알림 표시:', wsAlert.message)
              // NOTICE는 파란색으로 표시 (#2196F3)
              toast.info(wsAlert.message, {
                position: 'top-right',
                autoClose: 5000, // 5초
                hideProgressBar: false,
                closeOnClick: true,
                pauseOnHover: true,
                draggable: true,
                style: {
                  backgroundColor: '#e3f2fd', // 연한 파란색 배경
                  color: '#1565c0', // 진한 파란색 텍스트
                  borderLeft: '4px solid #2196F3', // 파란색 테두리
                },
              })
              break

            case 'RESOLVED':
              console.log('[WebSocketToast] RESOLVED 알림 표시:', wsAlert.message)
              toast.success(wsAlert.message, {
                position: 'top-right',
                autoClose: 5000, // 5초
                hideProgressBar: false,
                closeOnClick: true,
                pauseOnHover: true,
                draggable: true,
                style: {
                  backgroundColor: '#d1fae5',
                  color: '#065f46',
                  borderLeft: '4px solid #10b981',
                },
              })
              break
          }
        }
        // 기존 형식 지원 (하위 호환성 - level 필드 사용)
        else if (wsAlert.level) {
          const level = wsAlert.level.toLowerCase()
          if (level === 'critical') {
            toast.error(wsAlert.message || 'Critical 알림', {
              position: 'top-right',
              autoClose: 10000,
              hideProgressBar: false,
              closeOnClick: true,
              pauseOnHover: true,
              draggable: true,
              style: {
                backgroundColor: '#fee2e2',
                color: '#991b1b',
                borderLeft: '4px solid #dc2626',
              },
            })
          } else if (level === 'warning') {
            toast.warning(wsAlert.message || 'Warning 알림', {
              position: 'top-right',
              autoClose: 5000, // 5초 (AI 예지보전 알림용)
              hideProgressBar: false,
              closeOnClick: true,
              pauseOnHover: true,
              draggable: true,
              style: {
                backgroundColor: '#fef3c7', // 노란색 배경
                color: '#92400e', // 진한 갈색 텍스트
                borderLeft: '4px solid #f59e0b', // 주황색 테두리
              },
            })
          } else {
            toast.info(wsAlert.message || '알림', {
              position: 'top-right',
              autoClose: 5000,
              hideProgressBar: false,
              closeOnClick: true,
              pauseOnHover: true,
              draggable: true,
            })
          }
        }
      } catch (error) {
        console.error('WebSocket Toast 처리 실패:', error, alert)
      }
    })

    console.log('[WebSocketToast] ✅ 구독자 등록 완료')
    
    // cleanup 함수 반환
    return () => {
      console.log('[WebSocketToast] 구독 해제 중...')
      unsubscribe()
    }
  }, [subscribe]) // isConnected를 dependency에서 제거하여 구독이 항상 유지되도록 함

  return (
    <ToastContainer
      position="top-right"
      autoClose={5000}
      newestOnTop={false}
      closeOnClick
      rtl={false}
      pauseOnFocusLoss
      draggable
      pauseOnHover
      theme="light"
    />
  )
}

