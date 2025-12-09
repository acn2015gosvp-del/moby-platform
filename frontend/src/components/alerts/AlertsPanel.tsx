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
  onDeleteAll?: () => void
}

type SortField = 'ts' | 'level' | 'message'
type SortOrder = 'asc' | 'desc'

export function AlertsPanel({
  alerts,
  loading = false,
  onRefresh,
  onDismissAlert,
  onDeleteAll,
}: AlertsPanelProps) {
  // onRefresh는 향후 사용을 위해 유지
  void onRefresh
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
        case 'level': {
          const levelOrder: Record<Alert['level'], number> = { 
            critical: 4, 
            warning: 3, 
            info: 2,
            notice: 1,
            resolved: 0
          }
          comparison = (levelOrder[a.level] ?? 0) - (levelOrder[b.level] ?? 0)
          break
        }
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

  const getLevelBadgeColor = (level: Alert['level']) => {
    switch (level) {
      case 'critical':
        return 'bg-danger/10 text-danger border-danger/40'
      case 'warning':
        return 'bg-warning/10 text-warning border-warning/40'
      case 'info':
        return 'bg-secondary/10 text-secondary border-secondary/40'
      default:
        return 'bg-background-surface text-text-secondary border-border'
    }
  }

  const getLevelBorderColor = (level: Alert['level']) => {
    switch (level) {
      case 'critical':
        return 'border-l-4 border-danger'
      case 'warning':
        return 'border-l-4 border-warning'
      case 'info':
        return 'border-l-4 border-secondary'
      default:
        return 'border-l-4 border-border'
    }
  }

  const getLevelText = (level: Alert['level'] | string) => {
    switch (level) {
      case 'critical':
        return '긴급'
      case 'warning':
        return '경고'
      case 'info':
      case 'notice':
        return '이상'
      default:
        return level === 'notice' ? '이상' : level
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
    <div className="space-y-6">
      {/* 요약 통계 */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-background-surface border border-border rounded-xl p-4">
          <div className="text-sm text-text-secondary mb-1">전체</div>
          <div className="text-2xl font-bold text-text-primary">{stats.total}</div>
        </div>
        <div className="bg-background-surface border border-border rounded-xl p-4">
          <div className="text-sm text-text-secondary mb-1">긴급</div>
          <div className="text-2xl font-bold text-danger">{stats.critical}</div>
        </div>
        <div className="bg-background-surface border border-border rounded-xl p-4">
          <div className="text-sm text-text-secondary mb-1">경고</div>
          <div className="text-2xl font-bold text-warning">{stats.warning}</div>
        </div>
        <div className="bg-background-surface border border-border rounded-xl p-4">
          <div className="text-sm text-text-secondary mb-1">이상</div>
          <div className="text-2xl font-bold text-secondary">{stats.info}</div>
        </div>
        <div className="bg-background-surface border border-border rounded-xl p-4">
          <div className="text-sm text-text-secondary mb-1">필터링됨</div>
          <div className="text-2xl font-bold text-text-primary">{stats.filtered}</div>
        </div>
      </div>

      {/* 필터 및 검색 */}
      <div className="bg-background-surface border border-border rounded-xl p-4 space-y-4">
        {/* 전체 삭제 버튼 */}
        {onDeleteAll && alerts.length > 0 && (
          <div className="flex justify-end">
            <button
              onClick={onDeleteAll}
              className="px-4 py-2 bg-danger/10 text-danger border border-danger/40 rounded-lg hover:bg-danger/20 transition-colors font-medium text-sm"
              title="모든 알림 삭제"
            >
              전체 삭제
            </button>
          </div>
        )}
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* 검색 */}
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
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
              className="w-full px-3 py-2 border border-border rounded-lg bg-background-main text-text-primary placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>

          {/* 레벨 필터 */}
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              등급 필터
            </label>
            <div className="flex flex-wrap gap-2">
              {[
                { value: 'all', label: '전체' },
                { value: 'critical', label: '긴급' },
                { value: 'warning', label: '경고' },
                { value: 'info', label: '이상' },
              ].map((opt) => {
                const active = levelFilter === opt.value
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => {
                      setLevelFilter(opt.value as Alert['level'] | 'all')
                      setCurrentPage(1)
                    }}
                    className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
                      active
                        ? 'bg-primary text-background-main font-bold'
                        : 'bg-background-main text-text-secondary hover:text-text-primary border border-border'
                    }`}
                  >
                    {opt.label}
                  </button>
                )
              })}
            </div>
          </div>

          {/* 정렬 */}
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              정렬
            </label>
            <div className="flex gap-2">
              <select
                value={sortField}
                onChange={(e) => {
                  setSortField(e.target.value as SortField)
                  setCurrentPage(1)
                }}
                className="flex-1 px-3 py-2 border border-border rounded-lg bg-background-main text-text-primary focus:outline-none focus:ring-2 focus:ring-primary/30"
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
                className="px-4 py-2 border border-border rounded-lg bg-background-main text-text-primary hover:bg-white/5 transition-colors"
                title={sortOrder === 'asc' ? '오름차순' : '내림차순'}
              >
                {sortOrder === 'asc' ? '↑' : '↓'}
              </button>
            </div>
          </div>
        </div>

        {/* 페이지 크기 */}
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-text-secondary">페이지당 항목:</label>
          <select
            value={itemsPerPage}
            onChange={(e) => {
              setItemsPerPage(Number(e.target.value))
              setCurrentPage(1)
            }}
            className="px-3 py-2 border border-border rounded-lg bg-background-main text-text-primary focus:outline-none focus:ring-2 focus:ring-primary/30"
          >
            <option value="10">10</option>
            <option value="20">20</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
        </div>
      </div>

      {/* 알림 목록 */}
      <div className="bg-background-surface border border-border rounded-xl">
        {loading && paginatedAlerts.length === 0 ? (
          <div className="p-8 text-center text-text-secondary">로딩 중...</div>
        ) : paginatedAlerts.length === 0 ? (
          <div className="p-8 text-center text-text-secondary">
            {filteredAlerts.length === 0 && alerts.length > 0
              ? '필터 조건에 맞는 알림이 없습니다.'
              : '표시할 알림이 없습니다.'}
          </div>
        ) : (
          <>
            <div className="divide-y divide-border/60">
              {paginatedAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`p-5 md:p-6 hover:bg-white/5 transition-colors relative bg-background-main/60 ${getLevelBorderColor(
                    alert.level
                  )} rounded-lg`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium border ${getLevelBadgeColor(
                            alert.level
                          )}`}
                        >
                          {getLevelText(alert.level)}
                        </span>
                        <span className="text-sm text-text-secondary">
                          센서: {alert.sensor_id || 'N/A'}
                        </span>
                        <span className="text-sm text-text-secondary font-mono">
                          {formatRelativeTime(alert.ts)}
                        </span>
                      </div>
                      <h3 className="text-lg font-semibold text-text-primary mb-2">
                        {alert.message}
                      </h3>
                      {alert.llm_summary && (
                        <p className="text-sm text-text-secondary mb-2 bg-background-surface p-3 rounded-lg">
                          {alert.llm_summary}
                        </p>
                      )}
                      <div className="flex items-center gap-4 text-xs text-text-secondary">
                        <span className="font-mono">
                          소스: {alert.source}
                        </span>
                        {alert.details?.severity && (
                          <span>심각도: {alert.details.severity}</span>
                        )}
                      </div>
                    </div>
                    {/* 개별 삭제 버튼 */}
                    {onDismissAlert && (
                      <button
                        onClick={() => onDismissAlert(alert.id)}
                        className="ml-4 p-1 text-text-secondary hover:text-text-primary hover:bg-white/10 rounded transition-colors"
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
              <div className="p-4 border-t border-border flex items-center justify-between">
                <div className="text-sm text-text-secondary">
                  {((currentPage - 1) * itemsPerPage + 1).toLocaleString()} -{' '}
                  {Math.min(currentPage * itemsPerPage, sortedAlerts.length).toLocaleString()} /{' '}
                  {sortedAlerts.length.toLocaleString()}개
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="px-3 py-1 border border-border rounded-lg bg-background-main text-text-primary hover:bg-white/5 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    이전
                  </button>
                  <span className="px-4 py-1 text-sm text-text-primary">
                    {currentPage} / {totalPages}
                  </span>
                  <button
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 border border-border rounded-lg bg-background-main text-text-primary hover:bg-white/5 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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

