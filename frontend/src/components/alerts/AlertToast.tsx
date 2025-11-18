/**
 * Alert Toast 컴포넌트
 * 실시간 알림을 토스트 형태로 표시
 */

import { useEffect, useState } from 'react'
import type { Alert } from '@/types/alert'
import { formatRelativeTime } from '@/utils/formatters'

interface AlertToastProps {
  alert: Alert
  onClose: () => void
  duration?: number
}

export function AlertToast({ alert, onClose, duration = 5000 }: AlertToastProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [isExiting, setIsExiting] = useState(false)

  useEffect(() => {
    // Fade-in 애니메이션
    const showTimer = setTimeout(() => setIsVisible(true), 10)

    // 자동 사라짐
    const hideTimer = setTimeout(() => {
      setIsExiting(true)
      setTimeout(onClose, 300) // Fade-out 애니메이션 시간
    }, duration)

    return () => {
      clearTimeout(showTimer)
      clearTimeout(hideTimer)
    }
  }, [duration, onClose])

  const getLevelStyles = () => {
    switch (alert.level) {
      case 'critical':
        return {
          bg: 'bg-red-50',
          border: 'border-red-300',
          text: 'text-red-800',
          icon: '🔴',
        }
      case 'warning':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-300',
          text: 'text-yellow-800',
          icon: '⚠️',
        }
      case 'info':
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-300',
          text: 'text-blue-800',
          icon: 'ℹ️',
        }
      default:
        return {
          bg: 'bg-gray-50',
          border: 'border-gray-300',
          text: 'text-gray-800',
          icon: '📢',
        }
    }
  }

  const styles = getLevelStyles()

  return (
    <div
      className={`
        ${styles.bg} ${styles.border} ${styles.text}
        border-l-4 rounded-lg shadow-lg p-4 mb-3
        min-w-[320px] max-w-[480px]
        transform transition-all duration-300 ease-in-out
        ${isVisible && !isExiting ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
      `}
      role="alert"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2 flex-1">
          <span className="text-xl">{styles.icon}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-semibold text-sm">{alert.message}</span>
              <span className="text-xs opacity-70">
                {formatRelativeTime(alert.ts)}
              </span>
            </div>
            {alert.llm_summary && (
              <p className="text-xs opacity-80 line-clamp-2 mt-1">
                {alert.llm_summary}
              </p>
            )}
            <div className="text-xs opacity-70 mt-1">
              센서: {alert.sensor_id || 'N/A'}
            </div>
          </div>
        </div>
        <button
          onClick={() => {
            setIsExiting(true)
            setTimeout(onClose, 300)
          }}
          className={`
            ${styles.text} opacity-50 hover:opacity-100
            transition-opacity flex-shrink-0
            text-lg leading-none
          `}
          aria-label="닫기"
        >
          ×
        </button>
      </div>
    </div>
  )
}

interface AlertToastContainerProps {
  alerts: Alert[]
  onRemove: (id: string) => void
  maxAlerts?: number
}

export function AlertToastContainer({
  alerts,
  onRemove,
  maxAlerts = 5,
}: AlertToastContainerProps) {
  // 최신 알림만 표시 (최대 개수 제한)
  const displayAlerts = alerts.slice(0, maxAlerts)

  return (
    <div
      className="fixed top-4 right-4 z-50 flex flex-col items-end"
      aria-live="polite"
      aria-atomic="true"
    >
      {displayAlerts.map((alert) => (
        <AlertToast
          key={alert.id}
          alert={alert}
          onClose={() => onRemove(alert.id)}
          duration={alert.level === 'critical' ? 8000 : 5000}
        />
      ))}
    </div>
  )
}

