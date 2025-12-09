/**
 * Alert Ticker 컴포넌트
 * 대시보드 하단에 고정된 실시간 알림 티커
 */

import { useEffect, useState, useRef } from 'react'
import type { Alert } from '@/types/alert'
import { useAlertMute } from '@/context/AlertMuteContext'

interface AlertTickerProps {
  alerts: Alert[]
}

export function AlertTicker({ alerts }: AlertTickerProps) {
  // ⚠️ 중요: 모든 hooks는 조건부 return 이전에 호출되어야 합니다!
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isPaused, setIsPaused] = useState(false)
  const tickerRef = useRef<HTMLDivElement>(null)
  const { isTickerHidden, toggleTicker } = useAlertMute()

  // 티커 자동 스크롤
  useEffect(() => {
    if (alerts.length === 0 || isPaused) return

    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % alerts.length)
    }, 3000) // 3초마다 다음 알림으로 전환

    return () => clearInterval(interval)
  }, [alerts.length, isPaused])

  // 알림이 없거나 티커가 숨겨져 있으면 null 반환 (hooks 호출 이후에 조건부 return 가능)
  if (alerts.length === 0 || isTickerHidden) {
    return null
  }

  // 현재 알림 가져오기 (안전하게)
  const currentAlert = alerts.length > 0 ? alerts[currentIndex] : null

  // 알림이 없거나 currentAlert가 없으면 null 반환
  if (!currentAlert) {
    return null
  }

  const getLevelStyles = () => {
    switch (currentAlert.level) {
      case 'critical':
        return {
          bg: 'bg-danger/90',
          progressBg: 'bg-danger',
          text: 'text-white',
          icon: '🔴',
        }
      case 'warning':
        return {
          bg: 'bg-warning/90',
          progressBg: 'bg-warning',
          text: 'text-black',
          icon: '⚠️',
        }
      case 'info':
      case 'notice':
        return {
          bg: 'bg-secondary/90',
          progressBg: 'bg-secondary',
          text: 'text-white',
          icon: 'ℹ️',
        }
      case 'resolved':
        return {
          bg: 'bg-success/90',
          progressBg: 'bg-success',
          text: 'text-white',
          icon: '✅',
        }
      default:
        return {
          bg: 'bg-background-surface/90',
          progressBg: 'bg-background-surface',
          text: 'text-text-primary',
          icon: '📢',
        }
    }
  }

  const styles = getLevelStyles()

  return (
    <div
      ref={tickerRef}
      className={`
        fixed bottom-0 left-0 right-0 z-50
        ${styles.bg} ${styles.text}
        backdrop-blur-sm rounded-t shadow-lg
        py-2 px-4
        transform transition-all duration-300 ease-in-out
      `}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <span className="text-xl flex-shrink-0">{styles.icon}</span>
          <div className="flex-1 min-w-0 overflow-hidden">
            <div className="whitespace-nowrap animate-scroll">
              <span className="font-semibold">{currentAlert.message}</span>
              {currentAlert.sensor_id && (
                <span className="ml-2 opacity-90">· 센서: {currentAlert.sensor_id}</span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className="text-xs opacity-90">
              {currentIndex + 1} / {alerts.length}
            </span>
            <button
              type="button"
              onClick={toggleTicker}
              className="p-1 rounded hover:bg-black/20 transition-colors"
              title="티커 숨기기"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="w-4 h-4"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
      
      {/* 프로그레스 바 */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-black/20">
        <div
          className={`h-full ${styles.progressBg} transition-all duration-3000 ease-linear`}
          style={{
            width: isPaused ? '0%' : '100%',
            animation: isPaused ? 'none' : 'progress 3s linear forwards',
          }}
        />
      </div>
    </div>
  )
}

