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
          bg: 'bg-danger/90',
          border: 'border-danger',
          text: 'text-white',
          icon: '🔴',
        }
      case 'warning':
        return {
          bg: 'bg-warning/90',
          border: 'border-warning',
          text: 'text-black',
          icon: '⚠️',
        }
      case 'info':
      case 'notice':
        return {
          bg: 'bg-secondary/90',
          border: 'border-secondary',
          text: 'text-white',
          icon: 'ℹ️',
        }
      case 'resolved':
        return {
          bg: 'bg-success/90',
          border: 'border-success',
          text: 'text-white',
          icon: '✅',
        }
      default:
        return {
          bg: 'bg-background-surface/90',
          border: 'border-border',
          text: 'text-text-primary',
          icon: '📢',
        }
    }
  }

  const styles = getLevelStyles()

  return (
    <div
      className={`
        ${styles.bg} ${styles.border} ${styles.text}
        border-l-4 rounded backdrop-blur-sm shadow-lg mb-3
        min-w-[960px] max-w-[1440px]
        transform transition-all duration-300 ease-in-out
        ${isVisible && !isExiting ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0'}
      `}
      style={{ padding: '48px' }}
      role="alert"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1">
          <span style={{ fontSize: '60px' }}>{styles.icon}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-2">
              <span className="font-semibold" style={{ fontSize: '42px' }}>{alert.message}</span>
              <span className="opacity-70" style={{ fontSize: '36px' }}>
                {formatRelativeTime(alert.ts)}
              </span>
            </div>
            {alert.llm_summary && (
              <p className="opacity-80 line-clamp-2 mt-2" style={{ fontSize: '36px' }}>
                {alert.llm_summary}
              </p>
            )}
            <div className="opacity-70 mt-2" style={{ fontSize: '36px' }}>
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
            transition-opacity flex-shrink-0 leading-none
          `}
          style={{ fontSize: '54px' }}
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
      className="fixed top-4 left-1/2 -translate-x-1/2 z-50 flex flex-col items-center"
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

