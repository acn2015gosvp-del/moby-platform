/**
 * 알림 페이지
 * WebSocket을 통한 실시간 알림 수신 및 AlertsPanel 컴포넌트 사용
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useParams, Navigate } from 'react-router-dom'
import { getLatestAlerts, deleteAllAlerts } from '@/services/alerts/alertService'
import type { Alert } from '@/types/alert'
import { AlertsPanel } from '@/components/alerts/AlertsPanel'
import { AlertToastContainer } from '@/components/alerts/AlertToast'
import { useWebSocketContext } from '@/context/WebSocketContext'
import { getDismissedAlerts, dismissAlert, clearDismissedAlerts } from '@/utils/localStorage'

function Alerts() {
  const { deviceId } = useParams<{ deviceId?: string }>()

  // deviceId가 없으면 설비 목록으로 리다이렉트
  if (!deviceId) {
    return <Navigate to="/devices" replace />
  }
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [toastAlerts, setToastAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { isConnected } = useWebSocketContext()

  // 삭제된 알림 ID 목록 (localStorage에서 로드)
  const [dismissedAlertIds, setDismissedAlertIds] = useState<Set<string>>(() =>
    getDismissedAlerts()
  )

  // 삭제되지 않은 알림만 필터링
  const visibleAlerts = useMemo(() => {
    return alerts.filter((alert) => !dismissedAlertIds.has(alert.id))
  }, [alerts, dismissedAlertIds])

  const fetchAlerts = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await getLatestAlerts({ limit: 100 })
      if (response.success && response.data) {
        setAlerts(response.data)
      } else {
        setError('알림 데이터를 불러올 수 없습니다.')
      }
    } catch (err: any) {
      const errorMessage = err.message || err.response?.data?.message || '알림을 불러오는데 실패했습니다.'
      setError(errorMessage)
      console.error('Failed to fetch alerts:', err)
      console.error('Error details:', {
        message: err.message,
        code: err.code,
        response: err.response,
        config: err.config,
      })
    } finally {
      setLoading(false)
    }
  }, [])

  const { subscribe } = useWebSocketContext()

  // WebSocket을 통한 실시간 알림 수신
  useEffect(() => {
    if (!isConnected) return

    const handleAlert = (alert: Alert) => {
      // 알림 목록에 추가 (중복 제거)
      setAlerts((prev) => {
        const exists = prev.some((a) => a.id === alert.id)
        if (exists) return prev
        return [alert, ...prev].slice(0, 100) // 최대 100개 유지
      })

      // 토스트 알림에 추가
      setToastAlerts((prev) => {
        const exists = prev.some((a) => a.id === alert.id)
        if (exists) return prev
        return [alert, ...prev]
      })
    }

    const unsubscribe = subscribe(handleAlert)
    return unsubscribe
  }, [isConnected, subscribe])

  useEffect(() => {
    // 초기 로드
    fetchAlerts()
    
    // 30초마다 자동 갱신 (WebSocket이 연결되지 않은 경우)
    const interval = setInterval(() => {
      if (!isConnected) {
        fetchAlerts()
      }
    }, 30000)
    return () => clearInterval(interval)
  }, [fetchAlerts, isConnected])

  // 에러 발생 시 재시도 로직 (최대 3회)
  useEffect(() => {
    if (error && (error.includes('서버') || error.includes('네트워크'))) {
      const retryCount = parseInt(sessionStorage.getItem('alertRetryCount') || '0', 10)
      if (retryCount < 3) {
        const retryTimer = setTimeout(() => {
          sessionStorage.setItem('alertRetryCount', String(retryCount + 1))
          fetchAlerts()
        }, 5000) // 5초 후 재시도
        
        return () => {
          clearTimeout(retryTimer)
          if (retryCount >= 2) {
            sessionStorage.removeItem('alertRetryCount')
          }
        }
      } else {
        sessionStorage.removeItem('alertRetryCount')
      }
    } else {
      sessionStorage.removeItem('alertRetryCount')
    }
  }, [error, fetchAlerts])

  const handleRemoveToast = useCallback((id: string) => {
    setToastAlerts((prev) => prev.filter((alert) => alert.id !== id))
  }, [])

  // 개별 알림 삭제 핸들러
  const handleDismissAlert = useCallback((alertId: string) => {
    dismissAlert(alertId)
    setDismissedAlertIds((prev) => {
      const next = new Set(prev)
      next.add(alertId)
      return next
    })
  }, [])

  // 전체 알림 삭제 핸들러
  const handleDeleteAll = useCallback(async () => {
    if (!window.confirm('모든 알림을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
      return
    }

    try {
      setLoading(true)
      setError(null)
      const response = await deleteAllAlerts()
      if (response.success) {
        // 알림 목록 초기화
        setAlerts([])
        setToastAlerts([])
        // localStorage의 삭제된 알림 목록도 초기화
        clearDismissedAlerts()
        setDismissedAlertIds(new Set())
        // 새로고침
        await fetchAlerts()
      }
    } catch (err: any) {
      setError(err.response?.data?.message || '전체 알림 삭제에 실패했습니다.')
      console.error('Failed to delete all alerts:', err)
    } finally {
      setLoading(false)
    }
  }, [fetchAlerts])

  return (
    <div className="min-h-screen bg-background-main p-6 space-y-6">
      {/* 페이지 헤더 */}
      <div>
        <h1 className="text-3xl font-bold text-text-primary mb-2">알림 이력</h1>
      </div>

      {error && (
        <div className="p-4 bg-danger/10 border border-danger rounded-xl text-danger">
          {error}
        </div>
      )}

      {/* 토스트 알림 */}
      <AlertToastContainer
        alerts={toastAlerts}
        onRemove={handleRemoveToast}
        maxAlerts={5}
      />

      {/* 알림 패널 */}
      <AlertsPanel
        alerts={visibleAlerts}
        loading={loading}
        onRefresh={fetchAlerts}
        onDismissAlert={handleDismissAlert}
        onDeleteAll={handleDeleteAll}
      />
    </div>
  )
}

export default Alerts
