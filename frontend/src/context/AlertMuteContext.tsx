/**
 * 알림 음소거 Context
 * 화면 효과와 하단 티커를 끄고 켤 수 있는 기능 제공
 */

import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'

interface AlertMuteContextType {
  isMuted: boolean
  isTickerHidden: boolean
  toggleMute: () => void
  toggleTicker: () => void
  muteAll: () => void
  unmuteAll: () => void
}

const AlertMuteContext = createContext<AlertMuteContextType | undefined>(undefined)

const STORAGE_KEY_MUTE = 'moby_alert_muted'
const STORAGE_KEY_TICKER_HIDDEN = 'moby_ticker_hidden'

export function AlertMuteProvider({ children }: { children: ReactNode }) {
  // localStorage에서 초기값 로드 (안전하게 처리)
  const [isMuted, setIsMuted] = useState(() => {
    try {
      if (typeof window !== 'undefined') {
        const stored = localStorage.getItem(STORAGE_KEY_MUTE)
        return stored === 'true'
      }
    } catch (error) {
      console.warn('[AlertMuteContext] localStorage 접근 실패:', error)
    }
    return false
  })
  
  const [isTickerHidden, setIsTickerHidden] = useState(() => {
    try {
      if (typeof window !== 'undefined') {
        const stored = localStorage.getItem(STORAGE_KEY_TICKER_HIDDEN)
        return stored === 'true'
      }
    } catch (error) {
      console.warn('[AlertMuteContext] localStorage 접근 실패:', error)
    }
    return false
  })

  // localStorage에 저장 (안전하게 처리)
  useEffect(() => {
    try {
      if (typeof window !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_MUTE, String(isMuted))
      }
    } catch (error) {
      console.warn('[AlertMuteContext] localStorage 저장 실패:', error)
    }
  }, [isMuted])

  useEffect(() => {
    try {
      if (typeof window !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_TICKER_HIDDEN, String(isTickerHidden))
      }
    } catch (error) {
      console.warn('[AlertMuteContext] localStorage 저장 실패:', error)
    }
  }, [isTickerHidden])

  const toggleMute = () => {
    setIsMuted((prev) => !prev)
  }

  const toggleTicker = () => {
    setIsTickerHidden((prev) => !prev)
  }

  const muteAll = () => {
    setIsMuted(true)
    setIsTickerHidden(true)
  }

  const unmuteAll = () => {
    setIsMuted(false)
    setIsTickerHidden(false)
  }

  const value: AlertMuteContextType = {
    isMuted,
    isTickerHidden,
    toggleMute,
    toggleTicker,
    muteAll,
    unmuteAll,
  }

  return <AlertMuteContext.Provider value={value}>{children}</AlertMuteContext.Provider>
}

// Fast refresh 경고: hook과 컴포넌트를 같은 파일에서 export하는 것은 허용됨
// eslint-disable-next-line react-refresh/only-export-components
export function useAlertMute() {
  const context = useContext(AlertMuteContext)
  if (context === undefined) {
    throw new Error('useAlertMute must be used within AlertMuteProvider')
  }
  return context
}

