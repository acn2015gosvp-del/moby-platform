/**
 * AlertsPanel 컴포넌트
 * 알림 목록을 표시하고 필터링, 정렬, 검색 기능 제공
 */

import { useState, useMemo } from 'react'
import type { Alert } from '@/types/alert'
import { formatRelativeTime } from '@/utils/formatters'

interface AlertsPanelProps {
  alerts: Alert[]
  loading?: boolean
  onRefresh?: () => void
  onDismissAlert?: (alertId: string) => void
}

type SortField = 'ts' | 'level' | 'message'
type SortOrder = 'asc' | 'desc'

export function AlertsPanel({
  alerts,
  loading = false,
  onRefresh,
  onDismissAlert,
}: AlertsPanelProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [levelFilter, setLevelFilter] = useState<Alert['level'] | 'all'>('all')
  const [sortField, setSortField] = useState<SortField>('ts')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(20)

  // 필터링 및 검색
  const filteredAlerts = useMemo(() => {
    let result = [...alerts]

    // 레벨 필터
    if (levelFilter !== 'all') {
      result = result.filter((alert) => alert.level === levelFilter)
    }

    // 검색
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      result = result.filter(
        (alert) =>
          alert.message.toLowerCase().includes(query) ||
          alert.llm_summary?.toLowerCase().includes(query) ||
          alert.sensor_id.toLowerCase().includes(query) ||
          alert.source.toLowerCase().includes(query)
      )
    }

    return result
  }, [alerts, levelFilter, searchQuery])

  // 정렬
  const sortedAlerts = useMemo(() => {
    const result = [...filteredAlerts]

    result.sort((a, b) => {
      let comparison = 0

      switch (sortField) {
        case 'ts':
          comparison = new Date(a.ts).getTime() - new Date(b.ts).getTime()
          break
        case 'level':
          const levelOrder = { critical: 3, warning: 2, info: 1 }
          comparison = levelOrder[a.level] - levelOrder[b.level]
          break
        case 'message':
          comparison = a.message.localeCompare(b.message)
          break
      }

      return sortOrder === 'asc' ? comparison : -comparison
    })

    return result
  }, [filteredAlerts, sortField, sortOrder])

  // 페이지네이션
  const totalPages = Math.ceil(sortedAlerts.length / itemsPerPage)
  const paginatedAlerts = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage
    return sortedAlerts.slice(startIndex, startIndex + itemsPerPage)
  }, [sortedAlerts, currentPage, itemsPerPage])

  const getLevelColor = (level: Alert['level']) => {
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

  const getLevelText = (level: Alert['level']) => {
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

  // 통계
  const stats = useMemo(() => {
    return {
      total: alerts.length,
      critical: alerts.filter((a) => a.level === 'critical').length,
      warning: alerts.filter((a) => a.level === 'warning').length,
      info: alerts.filter((a) => a.level === 'info').length,
      filtered: filteredAlerts.length,
    }
  }, [alerts, filteredAlerts])

  return (
    <div className="space-y-4">
      {/* 헤더 및 새로고침 */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">알림 목록</h2>
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? '갱신 중...' : '새로고침'}
          </button>
        )}
      </div>

      {/* 통계 */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600 mb-1">전체</div>
          <div className="text-2xl font-bold text-gray-800">{stats.total}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600 mb-1">긴급</div>
          <div className="text-2xl font-bold text-red-600">{stats.critical}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600 mb-1">경고</div>
          <div className="text-2xl font-bold text-yellow-600">{stats.warning}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600 mb-1">정보</div>
          <div className="text-2xl font-bold text-blue-600">{stats.info}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600 mb-1">필터링됨</div>
          <div className="text-2xl font-bold text-gray-800">{stats.filtered}</div>
        </div>
      </div>

      {/* 필터 및 검색 */}
      <div className="bg-white rounded-lg shadow p-4 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* 검색 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              검색
            </label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                setCurrentPage(1)
              }}
              placeholder="메시지, 센서 ID, 소스 검색..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* 레벨 필터 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              레벨 필터
            </label>
            <select
              value={levelFilter}
              onChange={(e) => {
                setLevelFilter(e.target.value as Alert['level'] | 'all')
                setCurrentPage(1)
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">전체</option>
              <option value="critical">긴급</option>
              <option value="warning">경고</option>
              <option value="info">정보</option>
            </select>
          </div>

          {/* 정렬 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              정렬
            </label>
            <div className="flex gap-2">
              <select
                value={sortField}
                onChange={(e) => {
                  setSortField(e.target.value as SortField)
                  setCurrentPage(1)
                }}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="ts">시간</option>
                <option value="level">레벨</option>
                <option value="message">메시지</option>
              </select>
              <button
                onClick={() => {
                  setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
                  setCurrentPage(1)
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                title={sortOrder === 'asc' ? '오름차순' : '내림차순'}
              >
                {sortOrder === 'asc' ? '↑' : '↓'}
              </button>
            </div>
          </div>
        </div>

        {/* 페이지 크기 */}
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">페이지당 항목:</label>
          <select
            value={itemsPerPage}
            onChange={(e) => {
              setItemsPerPage(Number(e.target.value))
              setCurrentPage(1)
            }}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="10">10</option>
            <option value="20">20</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
        </div>
      </div>

      {/* 알림 목록 */}
      <div className="bg-white rounded-lg shadow">
        {loading && paginatedAlerts.length === 0 ? (
          <div className="p-8 text-center text-gray-500">로딩 중...</div>
        ) : paginatedAlerts.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            {filteredAlerts.length === 0 && alerts.length > 0
              ? '필터 조건에 맞는 알림이 없습니다.'
              : '표시할 알림이 없습니다.'}
          </div>
        ) : (
          <>
            <div className="divide-y divide-gray-200">
              {paginatedAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className="p-6 hover:bg-gray-50 transition-colors relative"
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
                    {/* 개별 삭제 버튼 */}
                    {onDismissAlert && (
                      <button
                        onClick={() => onDismissAlert(alert.id)}
                        className="ml-4 p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded transition-colors"
                        title="알림 삭제"
                        aria-label="알림 삭제"
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="h-5 w-5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* 페이지네이션 */}
            {totalPages > 1 && (
              <div className="p-4 border-t border-gray-200 flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  {((currentPage - 1) * itemsPerPage + 1).toLocaleString()} -{' '}
                  {Math.min(currentPage * itemsPerPage, sortedAlerts.length).toLocaleString()} /{' '}
                  {sortedAlerts.length.toLocaleString()}개
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    이전
                  </button>
                  <span className="px-4 py-1 text-sm text-gray-700">
                    {currentPage} / {totalPages}
                  </span>
                  <button
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    다음
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

