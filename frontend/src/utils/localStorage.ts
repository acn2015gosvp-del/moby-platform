/**
 * localStorage 유틸리티 함수
 * 삭제된 알림 ID 목록을 관리합니다.
 */

const DISMISSED_ALERTS_KEY = 'moby_dismissed_alerts'

/**
 * 삭제된 알림 ID 목록을 가져옵니다.
 */
export function getDismissedAlerts(): Set<string> {
  try {
    const stored = localStorage.getItem(DISMISSED_ALERTS_KEY)
    if (!stored) return new Set()
    const ids = JSON.parse(stored) as string[]
    return new Set(ids)
  } catch (error) {
    console.error('Failed to load dismissed alerts from localStorage:', error)
    return new Set()
  }
}

/**
 * 알림 ID를 삭제된 목록에 추가합니다.
 */
export function dismissAlert(alertId: string): void {
  try {
    const dismissed = getDismissedAlerts()
    dismissed.add(alertId)
    localStorage.setItem(DISMISSED_ALERTS_KEY, JSON.stringify(Array.from(dismissed)))
  } catch (error) {
    console.error('Failed to save dismissed alert to localStorage:', error)
  }
}

/**
 * 삭제된 알림 ID 목록을 초기화합니다.
 */
export function clearDismissedAlerts(): void {
  try {
    localStorage.removeItem(DISMISSED_ALERTS_KEY)
  } catch (error) {
    console.error('Failed to clear dismissed alerts from localStorage:', error)
  }
}

/**
 * 알림이 삭제되었는지 확인합니다.
 */
export function isAlertDismissed(alertId: string): boolean {
  const dismissed = getDismissedAlerts()
  return dismissed.has(alertId)
}

