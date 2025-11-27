/**
 * 운영관리 대시보드 페이지
 * 
 * Grafana 대시보드를 임베딩하여 표시합니다.
 */

import { useState, useMemo } from 'react'
import { useParams, Navigate } from 'react-router-dom'
import { useDeviceContext } from '@/context/DeviceContext'
import Loading from '@/components/common/Loading'

// 운영관리 대시보드 전용 Grafana 설정
const OPERATION_DASHBOARD_CONFIG = {
  BASE_URL: 'http://192.168.80.229:8080',
  DASHBOARD_UID: 'adrvc2v',
  DASHBOARD_SLUG: 'repair',
  ORG_ID: 1,
}

function Dashboard() {
  const { deviceId } = useParams<{ deviceId?: string }>()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [iframeLoaded, setIframeLoaded] = useState(false)

  // deviceId가 없으면 설비 목록으로 리다이렉트
  if (!deviceId) {
    return <Navigate to="/devices" replace />
  }

  // 운영관리 대시보드 URL 생성 (직접 URL 사용)
  const grafanaDashboardUrl = useMemo(() => {
    const { BASE_URL, DASHBOARD_UID, DASHBOARD_SLUG, ORG_ID } = OPERATION_DASHBOARD_CONFIG
    
    // 현재 시간 기준으로 시간 범위 설정 (최근 1시간)
    const now = new Date()
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000)
    
    const params = new URLSearchParams({
      orgId: ORG_ID.toString(),
      from: oneHourAgo.toISOString(),
      to: now.toISOString(),
      timezone: 'browser',
      refresh: '5s', // 5초마다 자동 새로고침
    })

    // kiosk 파라미터 추가 (값 없이) - iframe 임베딩 시 UI 단순화
    params.append('kiosk', '')

    const url = `${BASE_URL}/d/${DASHBOARD_UID}/${DASHBOARD_SLUG}?${params.toString()}`
    
    if (import.meta.env.DEV) {
      console.log('[Dashboard] 운영관리 대시보드 URL:', url)
    }
    
    return url
  }, [refreshKey])

  // 새로고침 핸들러
  const handleRefresh = () => {
    setIframeLoaded(false)
    setError(null)
    setRefreshKey((prev) => prev + 1)
  }

  // 새 창에서 열기
  const handleOpenInNewWindow = () => {
    if (grafanaDashboardUrl) {
      window.open(grafanaDashboardUrl, '_blank', 'noopener,noreferrer')
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-gray-800">운영관리 대시보드</h1>
        <Loading message="Grafana 대시보드를 불러오는 중..." />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 헤더 섹션 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">운영관리 대시보드</h1>
          <p className="text-gray-600 mt-1">Grafana 대시보드</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            새로고침
          </button>
          {grafanaDashboardUrl && (
            <button
              onClick={handleOpenInNewWindow}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              새 창에서 열기
            </button>
          )}
        </div>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded-lg">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-red-500 mr-2 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <p className="text-red-800 font-medium whitespace-pre-line">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Grafana 대시보드 임베딩 */}
      {!error && (
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="w-full" style={{ height: 'calc(100vh - 200px)', minHeight: '600px' }}>
            <iframe
              key={refreshKey}
              src={grafanaDashboardUrl}
              className="w-full h-full border-0"
              title="Grafana Dashboard"
              allow="fullscreen"
              onLoad={() => {
                setIframeLoaded(true)
                setLoading(false)
              }}
              onError={() => {
                setError('대시보드를 불러오는데 실패했습니다.')
                setLoading(false)
                setIframeLoaded(false)
              }}
            />
            {/* iframe 로딩 중 오버레이 (Grafana 로딩은 시간이 걸릴 수 있으므로 즉시 표시) */}
            {!iframeLoaded && !error && (
              <div className="absolute inset-0 bg-white bg-opacity-90 flex items-center justify-center z-10">
                <Loading message="Grafana 대시보드를 불러오는 중..." />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
