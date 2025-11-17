/**
 * 메인 대시보드 페이지
 */

import { useState, useEffect } from 'react'
import { getSensorStatus } from '@/services/sensors/sensorService'
import { getLatestAlerts } from '@/services/alerts/alertService'
import { SensorStatus } from '@/types/sensor'
import { Alert } from '@/types/alert'
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
        getLatestAlerts({ limit: 5 }),
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
        return 'bg-green-100 text-green-800 border-green-300'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'error':
        return 'bg-red-100 text-red-800 border-red-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
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
        return 'bg-red-100 text-red-800 border-red-300'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'info':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
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

  if (loading && !sensorStatus) {
    return (
      <div>
        <h1 className="text-3xl font-bold mb-6 text-gray-800">대시보드</h1>
        <Loading message="데이터를 불러오는 중..." />
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">대시보드</h1>
        <button
          onClick={fetchData}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? '갱신 중...' : '새로고침'}
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
        {/* 센서 상태 카드 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">센서 상태</h2>
          {sensorStatus ? (
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-gray-600">전체 상태</span>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(
                    sensorStatus.status
                  )}`}
                >
                  {getStatusText(sensorStatus.status)}
                </span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">전체 센서</span>
                  <span className="font-semibold text-gray-800">{sensorStatus.count}개</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">활성 센서</span>
                  <span className="font-semibold text-green-600">{sensorStatus.active}개</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">비활성 센서</span>
                  <span className="font-semibold text-red-600">{sensorStatus.inactive}개</span>
                </div>
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="flex justify-between">
                    <span className="text-gray-600">활성 비율</span>
                    <span className="font-semibold text-blue-600">
                      {sensorStatus.count > 0
                        ? Math.round((sensorStatus.active / sensorStatus.count) * 100)
                        : 0}
                      %
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-gray-600">센서 상태 정보가 없습니다.</p>
          )}
        </div>

        {/* 최근 알림 카드 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">최근 알림</h2>
          {recentAlerts.length > 0 ? (
            <div className="space-y-3">
              {recentAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className="p-3 bg-gray-50 rounded-lg border border-gray-200"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium border ${getLevelColor(
                        alert.level
                      )}`}
                    >
                      {getLevelText(alert.level)}
                    </span>
                    <span className="text-xs text-gray-500">
                      {formatRelativeTime(alert.ts)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-800 line-clamp-2">{alert.message}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-600">최근 알림이 없습니다.</p>
          )}
        </div>

        {/* 통계 카드 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">통계</h2>
          <div className="space-y-4">
            {recentAlerts.length > 0 && (
              <>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">전체 알림</span>
                  <span className="text-2xl font-bold text-gray-800">
                    {recentAlerts.length}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">긴급 알림</span>
                  <span className="text-2xl font-bold text-red-600">
                    {recentAlerts.filter((a) => a.level === 'critical').length}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">경고 알림</span>
                  <span className="text-2xl font-bold text-yellow-600">
                    {recentAlerts.filter((a) => a.level === 'warning').length}
                  </span>
                </div>
              </>
            )}
            {sensorStatus && (
              <div className="pt-4 border-t border-gray-200">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">센서 가동률</span>
                  <span className="text-2xl font-bold text-blue-600">
                    {sensorStatus.count > 0
                      ? Math.round((sensorStatus.active / sensorStatus.count) * 100)
                      : 0}
                    %
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 추가 정보 섹션 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">시스템 정보</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium text-gray-700 mb-2">센서 모니터링</h3>
            <p className="text-sm text-gray-600">
              최근 5분 내 데이터가 있는 센서를 활성으로 간주합니다. 센서 상태는 30초마다
              자동으로 갱신됩니다.
            </p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium text-gray-700 mb-2">알림 시스템</h3>
            <p className="text-sm text-gray-600">
              최근 알림은 실시간으로 업데이트되며, 긴급, 경고, 정보 레벨로 분류됩니다.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
