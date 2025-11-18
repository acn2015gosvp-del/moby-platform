/**
 * 알림 페이지
 */

import { useState, useEffect } from 'react'
import { getLatestAlerts } from '@/services/alerts/alertService'
import type { Alert } from '@/types/alert'
import Loading from '@/components/common/Loading'
import { formatRelativeTime } from '@/utils/formatters'

function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<{
    level?: 'info' | 'warning' | 'critical'
    limit: number
  }>({ limit: 20 })

  const fetchAlerts = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await getLatestAlerts({
        limit: filter.limit,
        level: filter.level,
      })
      if (response.success && response.data) {
        setAlerts(response.data)
      }
    } catch (err: any) {
      setError(err.response?.data?.message || '알림을 불러오는데 실패했습니다.')
      console.error('Failed to fetch alerts:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAlerts()
    // 30초마다 자동 갱신
    const interval = setInterval(fetchAlerts, 30000)
    return () => clearInterval(interval)
  }, [filter])

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

  if (loading && alerts.length === 0) {
    return (
      <div>
        <h1 className="text-3xl font-bold mb-6 text-gray-800">알림 관리</h1>
        <Loading message="알림을 불러오는 중..." />
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">알림 관리</h1>
        <button
          onClick={fetchAlerts}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? '갱신 중...' : '새로고침'}
        </button>
      </div>

      {/* 필터 */}
      <div className="mb-6 bg-white rounded-lg shadow p-4">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">레벨 필터:</label>
          <select
            value={filter.level || 'all'}
            onChange={(e) =>
              setFilter({
                ...filter,
                level: e.target.value === 'all' ? undefined : (e.target.value as any),
              })
            }
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">전체</option>
            <option value="critical">긴급</option>
            <option value="warning">경고</option>
            <option value="info">정보</option>
          </select>
          <label className="text-sm font-medium text-gray-700 ml-4">표시 개수:</label>
          <select
            value={filter.limit}
            onChange={(e) => setFilter({ ...filter, limit: Number(e.target.value) })}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="10">10개</option>
            <option value="20">20개</option>
            <option value="50">50개</option>
            <option value="100">100개</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          {error}
        </div>
      )}

      {/* 알림 통계 */}
      {alerts.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600 mb-1">전체 알림</div>
            <div className="text-2xl font-bold text-gray-800">{alerts.length}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600 mb-1">긴급 알림</div>
            <div className="text-2xl font-bold text-red-600">
              {alerts.filter((a) => a.level === 'critical').length}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600 mb-1">경고 알림</div>
            <div className="text-2xl font-bold text-yellow-600">
              {alerts.filter((a) => a.level === 'warning').length}
            </div>
          </div>
        </div>
      )}

      {/* 알림 목록 */}
      <div className="bg-white rounded-lg shadow">
        {alerts.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <p>표시할 알림이 없습니다.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="p-6 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium border ${getLevelColor(
                          alert.level
                        )}`}
                      >
                        {getLevelText(alert.level)}
                      </span>
                      <span className="text-sm text-gray-500">
                        센서: {alert.sensor_id || 'N/A'}
                      </span>
                      <span className="text-sm text-gray-500">
                        {formatRelativeTime(alert.ts)}
                      </span>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-800 mb-2">
                      {alert.message}
                    </h3>
                    {alert.llm_summary && (
                      <p className="text-sm text-gray-600 mb-2 bg-gray-50 p-3 rounded">
                        {alert.llm_summary}
                      </p>
                    )}
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>소스: {alert.source}</span>
                      {alert.details?.severity && (
                        <span>심각도: {alert.details.severity}</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Alerts
