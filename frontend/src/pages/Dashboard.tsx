/**
 * 운영관리 대시보드 페이지
 * 
 * Grafana 대시보드를 임베딩하여 표시합니다.
 */

import { useState, useMemo, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import Loading from '@/components/common/Loading'
import { useTheme } from '@/context/ThemeContext'

// 운영관리 대시보드 전용 Grafana 설정
const OPERATION_DASHBOARD_CONFIG = {
  BASE_URL: 'http://192.168.80.183:8080',
  DASHBOARD_UID: 'adrvc2v',
  DASHBOARD_SLUG: 'repair',
  ORG_ID: 1,
}

function Dashboard() {
  const { deviceId } = useParams<{ deviceId?: string }>()
  const { theme } = useTheme()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // iframeLoaded는 현재 사용되지 않음
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const iframeRef = useRef<HTMLIFrameElement | null>(null)

  // deviceId를 Grafana device_id 형식으로 변환
  // 예: "conveyor-belt-1" → "Conveyor_IR_01"
  const getGrafanaDeviceId = (deviceId: string): string => {
    // deviceId 매핑 (필요시 확장 가능)
    const deviceIdMap: Record<string, string> = {
      'conveyor-belt-1': 'Conveyor_IR_01',
      // 추가 매핑 필요시 여기에 추가
    }
    
    // 매핑이 있으면 사용, 없으면 원본 사용
    return deviceIdMap[deviceId] || deviceId
  }

  // 운영관리 대시보드 URL 생성 (직접 URL 사용)
  const grafanaDashboardUrl = useMemo(() => {
    const { BASE_URL, DASHBOARD_UID, DASHBOARD_SLUG, ORG_ID } = OPERATION_DASHBOARD_CONFIG
    
    // 현재 시간 기준으로 시간 범위 설정 (최근 1시간)
    const now = new Date()
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000)
    
    const params = new URLSearchParams({
      orgId: ORG_ID.toString(),
      from: oneHourAgo.toISOString(),
      to: now.toISOString(),
      timezone: 'browser',
      refresh: '5s', // 5초마다 자동 새로고침
    })

    // deviceId를 Grafana device_id 변수로 전달
    if (deviceId) {
      const grafanaDeviceId = getGrafanaDeviceId(deviceId)
      params.append('var-device_id', grafanaDeviceId)
    }

    // kiosk 파라미터 추가 (값 없이) - iframe 임베딩 시 UI 단순화
    params.append('kiosk', '')

    // 테마 파라미터 추가 (다크/라이트 동기화)
    params.append('theme', theme === 'light' ? 'light' : 'dark')

    const url = `${BASE_URL}/d/${DASHBOARD_UID}/${DASHBOARD_SLUG}?${params.toString()}`
    
    if (import.meta.env.DEV) {
      console.log('[Dashboard] 운영관리 대시보드 URL:', url)
      console.log('[Dashboard] deviceId:', deviceId, '→ Grafana device_id:', deviceId ? getGrafanaDeviceId(deviceId) : 'N/A')
    }
    
    return url
  }, [deviceId, theme])

  // iframe 로드 완료 핸들러
  const handleIframeLoad = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    
    setError(null)
    setLoading(false)
    
    if (import.meta.env.DEV) {
      console.log('[Dashboard] iframe onLoad 이벤트 발생 - Grafana 대시보드 로드 완료')
    }
  }

  // iframe 에러 핸들러
  const handleIframeError = () => {
    if (import.meta.env.DEV) {
      console.error('[Dashboard] iframe onError 이벤트 발생')
    }
    
    const errorMsg = `Grafana 대시보드 로드 실패\n\n가능한 원인:\n1. Grafana 서버에서 iframe 임베딩이 차단됨\n   → Grafana 설정 파일에서 allow_embedding = true 확인\n   → Grafana 서버 재시작 필요\n\n2. X-Frame-Options 정책 위반\n   → allow_embedding = true 설정으로 해결 가능\n\n3. CORS 정책 위반\n   → Grafana 설정에서 CORS 허용 확인`
    
    setError(errorMsg)
    setLoading(false)
  }

  // X-Frame-Options 및 보안 에러 감지
  useEffect(() => {
    const handleSecurityError = (event: ErrorEvent) => {
      const errorMessage = event.message || ''
      
      if (errorMessage.includes('X-Frame-Options') || 
          errorMessage.includes('frame') || 
          errorMessage.includes('Refused to display')) {
        const errorMsg = `❌ X-Frame-Options 정책 위반: iframe 임베딩 차단\n\n직접 URL 접속은 성공하지만 iframe에서 로드되지 않습니다.\n이는 Grafana 서버에서 iframe 임베딩이 차단되었기 때문입니다.\n\n현재 URL: ${grafanaDashboardUrl}\n\n🔧 해결 방법:\n\n1. Grafana 설정 파일(grafana.ini)에 다음 추가:\n   [security]\n   allow_embedding = true\n\n2. Grafana 서버 재시작 (필수!)\n\n3. 재시작 후 확인:\n   - 브라우저 캐시 삭제 (Ctrl+Shift+Delete)\n   - 페이지 새로고침 (F5)`
        setError(errorMsg)
        if (import.meta.env.DEV) {
          console.error('[Dashboard] 보안 정책 에러 감지:', errorMessage)
        }
      }
    }

    const originalConsoleError = console.error
    console.error = (...args: unknown[]) => {
      const errorText = args.map(arg => String(arg)).join(' ')
      if (errorText.includes('X-Frame-Options') || 
          errorText.includes('Refused to display') ||
          errorText.includes('frame')) {
        handleSecurityError({ message: errorText } as ErrorEvent)
      }
      originalConsoleError.apply(console, args)
    }

    window.addEventListener('error', handleSecurityError)
    return () => {
      window.removeEventListener('error', handleSecurityError)
      console.error = originalConsoleError
    }
  }, [grafanaDashboardUrl])

  // URL 변경 시 iframe 상태 초기화
  useEffect(() => {
    if (grafanaDashboardUrl && deviceId) {
      // useEffect 내에서 setState를 직접 호출하는 대신, 
      // 다음 렌더링 사이클에서 업데이트하도록 수정
      const timeoutId = setTimeout(() => {
        setError(null)
        setLoading(false)
      }, 0)
      return () => clearTimeout(timeoutId)
      
      if (import.meta.env.DEV) {
        console.log('[Dashboard] Grafana 대시보드 URL:', grafanaDashboardUrl)
      }
      
      // 이전 타임아웃이 있으면 취소
      if (timeoutRef.current !== null) {
        clearTimeout(timeoutRef.current as unknown as number)
        timeoutRef.current = null
      }
    }
  }, [deviceId, grafanaDashboardUrl])

  if (loading) {
    return (
      <div className="bg-transparent space-y-6 p-6">
        <Loading message="Grafana 대시보드를 불러오는 중..." />
      </div>
    )
  }

  return (
    <div className="w-full h-[calc(100vh-80px)] flex flex-col bg-transparent">
      {/* 에러 메시지 */}
      {error && (
        <div className="mx-8 mb-4 p-4 bg-danger/10 border-l-4 border-danger rounded-xl">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-danger mr-2 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <p className="text-danger font-medium whitespace-pre-line">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Grafana 대시보드 임베딩 (사이드바 제외 가로 최대) */}
      {!error && (
        <div className="flex-1 relative min-h-0 mb-4 md:mb-6">
          <div className="w-full h-full bg-background-surface border border-border rounded-xl shadow-lg overflow-hidden">
            <iframe
              ref={iframeRef}
              src={grafanaDashboardUrl}
              className="w-full h-full border-0"
              title="Grafana Dashboard"
              allow="fullscreen"
              onLoad={handleIframeLoad}
              onError={handleIframeError}
              sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-presentation"
              referrerPolicy="no-referrer-when-downgrade"
              loading="lazy"
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
