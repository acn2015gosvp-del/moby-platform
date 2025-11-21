/**
 * 운영관리 대시보드 페이지
 * 
 * 실시간 모니터링, 통계, 알림을 한눈에 볼 수 있는 운영관리 대시보드
 */

import { useState, useEffect } from 'react'
import { getSensorStatus } from '@/services/sensors/sensorService'
import { getLatestAlerts } from '@/services/alerts/alertService'
import type { SensorStatus } from '@/types/sensor'
import type { Alert } from '@/types/alert'
import Loading from '@/components/common/Loading'
import { formatRelativeTime } from '@/utils/formatters'

function Dashboard() {
  const [sensorStatus, setSensorStatus] = useState<SensorStatus | null>(null)
  const [recentAlerts, setRecentAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)

      // 센서 상태와 최근 알림을 동시에 가져오기
      const [sensorResponse, alertsResponse] = await Promise.all([
        getSensorStatus(),
        getLatestAlerts({ limit: 10 }),
      ])

      if (sensorResponse.success && sensorResponse.data) {
        setSensorStatus(sensorResponse.data)
      }

      if (alertsResponse.success && alertsResponse.data) {
        setRecentAlerts(alertsResponse.data)
      }
    } catch (err: any) {
      setError(err.response?.data?.message || '데이터를 불러오는데 실패했습니다.')
      console.error('Failed to fetch dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    // 30초마다 자동 갱신
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ok':
        return 'bg-green-500'
      case 'warning':
        return 'bg-yellow-500'
      case 'error':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'ok':
        return '정상'
      case 'warning':
        return '경고'
      case 'error':
        return '오류'
      default:
        return '알 수 없음'
    }
  }

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'critical':
        return 'bg-red-500'
      case 'warning':
        return 'bg-yellow-500'
      case 'info':
        return 'bg-blue-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getLevelText = (level: string) => {
    switch (level) {
      case 'critical':
        return '긴급'
      case 'warning':
        return '경고'
      case 'info':
        return '정보'
      default:
        return level
    }
  }

  // 통계 계산
  const activeRatio = sensorStatus && sensorStatus.count > 0
    ? Math.round((sensorStatus.active / sensorStatus.count) * 100)
    : 0

  const criticalAlerts = recentAlerts.filter((a) => a.level === 'critical').length
  const warningAlerts = recentAlerts.filter((a) => a.level === 'warning').length
  const infoAlerts = recentAlerts.filter((a) => a.level === 'info').length

  if (loading && !sensorStatus) {
    return (
      <div>
        <h1 className="text-3xl font-bold mb-6 text-gray-800">운영관리 대시보드</h1>
        <Loading message="데이터를 불러오는 중..." />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 헤더 섹션 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">운영관리 대시보드</h1>
          <p className="text-gray-600 mt-1">실시간 시스템 모니터링 및 운영 현황</p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2 shadow-sm"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {loading ? '갱신 중...' : '새로고침'}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded-lg">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-red-800 font-medium">{error}</p>
          </div>
        </div>
      )}

      {/* 주요 KPI 카드 그리드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* 전체 시스템 상태 */}
        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">시스템 상태</h3>
            <div className={`w-3 h-3 rounded-full ${getStatusColor(sensorStatus?.status || 'unknown')}`}></div>
          </div>
          <div className="flex items-baseline">
            <p className="text-3xl font-bold text-gray-800">{getStatusText(sensorStatus?.status || 'unknown')}</p>
          </div>
          <p className="text-xs text-gray-500 mt-2">실시간 모니터링 중</p>
        </div>

        {/* 전체 센서 수 */}
        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-green-500">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">전체 센서</h3>
            <svg className="w-6 h-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <div className="flex items-baseline">
            <p className="text-3xl font-bold text-gray-800">{sensorStatus?.count || 0}</p>
            <span className="ml-2 text-sm text-gray-600">개</span>
          </div>
          <div className="mt-3 flex items-center gap-4 text-sm">
            <span className="text-green-600 font-medium">활성: {sensorStatus?.active || 0}</span>
            <span className="text-red-600 font-medium">비활성: {sensorStatus?.inactive || 0}</span>
          </div>
        </div>

        {/* 센서 가동률 */}
        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-purple-500">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">센서 가동률</h3>
            <svg className="w-6 h-6 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <div className="flex items-baseline">
            <p className="text-3xl font-bold text-gray-800">{activeRatio}</p>
            <span className="ml-2 text-sm text-gray-600">%</span>
          </div>
          <div className="mt-3">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-500 ${
                  activeRatio >= 80 ? 'bg-green-500' : activeRatio >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${activeRatio}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* 전체 알림 수 */}
        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-orange-500">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">전체 알림</h3>
            <svg className="w-6 h-6 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </div>
          <div className="flex items-baseline">
            <p className="text-3xl font-bold text-gray-800">{recentAlerts.length}</p>
            <span className="ml-2 text-sm text-gray-600">건</span>
          </div>
          <div className="mt-3 flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-red-500"></span>
              <span className="text-red-600">{criticalAlerts}</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
              <span className="text-yellow-600">{warningAlerts}</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-blue-500"></span>
              <span className="text-blue-600">{infoAlerts}</span>
            </span>
          </div>
        </div>
      </div>

      {/* 주요 섹션 그리드 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 센서 상세 상태 - 왼쪽 (2/3) */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-800">센서 상태 상세</h2>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">마지막 업데이트:</span>
              <span className="text-sm font-medium text-gray-800">방금 전</span>
            </div>
          </div>

          {sensorStatus ? (
            <div className="space-y-6">
              {/* 상태 요약 */}
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">전체 센서</p>
                  <p className="text-2xl font-bold text-gray-800">{sensorStatus.count}</p>
                  <p className="text-xs text-gray-500 mt-1">개</p>
                </div>
                <div className="p-4 bg-green-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">활성 센서</p>
                  <p className="text-2xl font-bold text-green-600">{sensorStatus.active}</p>
                  <p className="text-xs text-gray-500 mt-1">개</p>
                </div>
                <div className="p-4 bg-red-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">비활성 센서</p>
                  <p className="text-2xl font-bold text-red-600">{sensorStatus.inactive}</p>
                  <p className="text-xs text-gray-500 mt-1">개</p>
                </div>
              </div>

              {/* 가동률 차트 */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm font-medium text-gray-700">센서 가동률</p>
                  <p className="text-lg font-bold text-blue-600">{activeRatio}%</p>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div
                    className={`h-4 rounded-full transition-all duration-700 ${
                      activeRatio >= 80 ? 'bg-gradient-to-r from-green-400 to-green-600' 
                      : activeRatio >= 50 ? 'bg-gradient-to-r from-yellow-400 to-yellow-600' 
                      : 'bg-gradient-to-r from-red-400 to-red-600'
                    }`}
                    style={{ width: `${activeRatio}%` }}
                  ></div>
                </div>
              </div>

              {/* 시스템 정보 */}
              <div className="pt-4 border-t border-gray-200">
                <h3 className="text-sm font-medium text-gray-700 mb-3">시스템 정보</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">모니터링 주기</span>
                    <span className="font-medium text-gray-800">30초</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">활성 판정 기준</span>
                    <span className="font-medium text-gray-800">최근 5분 내 데이터</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">현재 상태</span>
                    <span className={`font-medium ${sensorStatus.status === 'ok' ? 'text-green-600' : sensorStatus.status === 'warning' ? 'text-yellow-600' : 'text-red-600'}`}>
                      {getStatusText(sensorStatus.status)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">센서 상태 정보가 없습니다.</p>
            </div>
          )}
        </div>

        {/* 최근 알림 - 오른쪽 (1/3) */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-800">최근 알림</h2>
            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
              {recentAlerts.length}
            </span>
          </div>

          {recentAlerts.length > 0 ? (
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {recentAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className="p-4 bg-gray-50 rounded-lg border-l-4 hover:bg-gray-100 transition-colors"
                  style={{ borderLeftColor: alert.level === 'critical' ? '#ef4444' : alert.level === 'warning' ? '#eab308' : '#3b82f6' }}
                >
                  <div className="flex items-start justify-between mb-2">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium text-white ${getLevelColor(alert.level)}`}
                    >
                      {getLevelText(alert.level)}
                    </span>
                    <span className="text-xs text-gray-500">
                      {formatRelativeTime(alert.ts)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-800 line-clamp-3">{alert.message}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-gray-500 font-medium">최근 알림이 없습니다</p>
              <p className="text-gray-400 text-sm mt-1">모든 시스템이 정상 작동 중입니다</p>
            </div>
          )}
        </div>
      </div>

      {/* 알림 통계 카드 */}
      {recentAlerts.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-6">알림 통계</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-5 bg-red-50 rounded-lg border border-red-200">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-red-800">긴급 알림</h3>
                <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <p className="text-3xl font-bold text-red-600">{criticalAlerts}</p>
              <p className="text-xs text-red-600 mt-1">즉시 조치 필요</p>
            </div>

            <div className="p-5 bg-yellow-50 rounded-lg border border-yellow-200">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-yellow-800">경고 알림</h3>
                <svg className="w-6 h-6 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <p className="text-3xl font-bold text-yellow-600">{warningAlerts}</p>
              <p className="text-xs text-yellow-600 mt-1">주의 깊게 모니터링</p>
            </div>

            <div className="p-5 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-blue-800">정보 알림</h3>
                <svg className="w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-3xl font-bold text-blue-600">{infoAlerts}</p>
              <p className="text-xs text-blue-600 mt-1">참고 정보</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
