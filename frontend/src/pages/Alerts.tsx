/**
 * 알림 페이지
 * WebSocket을 통한 실시간 알림 수신 및 AlertsPanel 컴포넌트 사용
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useParams, Navigate } from 'react-router-dom'
import { getLatestAlerts } from '@/services/alerts/alertService'
import type { Alert } from '@/types/alert'
import { AlertsPanel } from '@/components/alerts/AlertsPanel'
import { AlertToastContainer } from '@/components/alerts/AlertToast'
import { useWebSocketContext } from '@/context/WebSocketContext'
import { getDismissedAlerts, dismissAlert } from '@/utils/localStorage'

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
      }
    } catch (err: any) {
      setError(err.response?.data?.message || '알림을 불러오는데 실패했습니다.')
      console.error('Failed to fetch alerts:', err)
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
    fetchAlerts()
    // 30초마다 자동 갱신 (WebSocket이 연결되지 않은 경우)
    const interval = setInterval(() => {
      if (!isConnected) {
        fetchAlerts()
      }
    }, 30000)
    return () => clearInterval(interval)
  }, [fetchAlerts, isConnected])

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

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">알림 관리</h1>
        <div className="flex items-center gap-3">
          {isConnected && (
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
              실시간 연결됨
            </span>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
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
      />
    </div>
  )
}

export default Alerts
