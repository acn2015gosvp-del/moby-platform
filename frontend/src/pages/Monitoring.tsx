/**
 * 설비 모니터링 페이지
 * 
 * 실시간 설비 상태 및 센서 데이터를 Grafana 대시보드로 표시
 * Grafana API를 사용하여 동적으로 대시보드 URL을 생성합니다.
 */

import React, { useState, useEffect, useRef, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import {
  GRAFANA_CONFIG,
  buildGrafanaDashboardUrl,
} from '@/utils/grafana'
import { useDeviceContext } from '@/context/DeviceContext'
import { useTheme } from '@/context/ThemeContext'
import Loading from '@/components/common/Loading'

const Monitoring: React.FC = () => {
  const { deviceId } = useParams<{ deviceId?: string }>()
  const { selectedDevice, setSelectedDeviceId } = useDeviceContext()
  const { theme } = useTheme()
  const [timeRange] = useState<string>('1h')
  // loading은 현재 사용되지 않지만 향후 사용을 위해 유지
  const [loading, _setLoading] = useState(false)
  void _setLoading
  const [iframeError, setIframeError] = useState<string | null>(null)
  const [iframeLoaded, setIframeLoaded] = useState(false)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const iframeRef = useRef<HTMLIFrameElement | null>(null)

  // 시간 범위 옵션
  const timeRangeOptions = [
    { value: '1h', label: '최근 1시간', from: 'now-1h', to: 'now' },
    { value: '6h', label: '최근 6시간', from: 'now-6h', to: 'now' },
    { value: '24h', label: '최근 24시간', from: 'now-24h', to: 'now' },
    { value: '7d', label: '최근 7일', from: 'now-7d', to: 'now' },
    { value: '30d', label: '최근 30일', from: 'now-30d', to: 'now' },
  ]

  // 선택된 시간 범위에 해당하는 from/to 값
  const selectedTimeRange = useMemo(() => {
    const option = timeRangeOptions.find(opt => opt.value === timeRange)
    return option ? { from: option.from, to: option.to } : { from: 'now-6h', to: 'now' }
  }, [timeRange, timeRangeOptions])

  // Grafana 대시보드 URL 생성 (API 기반)
  const grafanaDashboardUrl = useMemo(() => {
    if (!selectedDevice || !GRAFANA_CONFIG.DEFAULT_DASHBOARD_UID) {
      return ''
    }
    
    return buildGrafanaDashboardUrl(
      GRAFANA_CONFIG.DEFAULT_DASHBOARD_UID,
      selectedDevice.device_id,
      selectedTimeRange,
      theme
    )
  }, [selectedDevice, selectedTimeRange, theme])

  // deviceId가 변경되면 해당 설비로 이동
  useEffect(() => {
    if (deviceId && deviceId !== selectedDevice?.device_id) {
      setSelectedDeviceId(deviceId)
    }
  }, [deviceId, selectedDevice, setSelectedDeviceId])

  // selectedDevice가 없고 deviceId가 있으면 로딩 상태
  // useEffect 내에서 setState를 직접 호출하는 대신, 로딩 상태를 계산된 값으로 관리
  const isLoadingDevice = deviceId && !selectedDevice
  void isLoadingDevice

  // Grafana 연결 확인 및 대시보드 정보는 백그라운드에서 처리 (로딩 블로킹 제거)



  // iframe 로드 완료 핸들러
  const handleIframeLoad = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    
    setIframeLoaded(true)
    setIframeError(null)
    
    if (import.meta.env.DEV) {
      console.log('[Monitoring] iframe onLoad 이벤트 발생 - Grafana 대시보드 로드 완료')
    }
  }

  // iframe 에러 핸들러
  const handleIframeError = () => {
    if (import.meta.env.DEV) {
      console.error('[Monitoring] iframe onError 이벤트 발생')
    }
    
    const errorMsg = `Grafana 대시보드 로드 실패\n\n가능한 원인:\n1. Grafana 서버에서 iframe 임베딩이 차단됨\n   → Grafana 설정 파일에서 allow_embedding = true 확인\n   → Grafana 서버 재시작 필요\n\n2. X-Frame-Options 정책 위반\n   → allow_embedding = true 설정으로 해결 가능\n\n3. CORS 정책 위반\n   → Grafana 설정에서 CORS 허용 확인`
    
    setIframeError(errorMsg)
  }

  // X-Frame-Options 및 보안 에러 감지
  useEffect(() => {
    const handleSecurityError = (event: ErrorEvent) => {
      const errorMessage = event.message || ''
      
      if (errorMessage.includes('X-Frame-Options') || 
          errorMessage.includes('frame') || 
          errorMessage.includes('Refused to display')) {
        const errorMsg = `❌ X-Frame-Options 정책 위반: iframe 임베딩 차단\n\n직접 URL 접속은 성공하지만 iframe에서 로드되지 않습니다.\n이는 Grafana 서버에서 iframe 임베딩이 차단되었기 때문입니다.\n\n현재 URL: ${grafanaDashboardUrl}\n\n🔧 해결 방법:\n\n1. Grafana 설정 파일(grafana.ini)에 다음 추가:\n   [security]\n   allow_embedding = true\n\n2. Grafana 서버 재시작 (필수!)\n\n3. 재시작 후 확인:\n   - 브라우저 캐시 삭제 (Ctrl+Shift+Delete)\n   - 페이지 새로고침 (F5)`
        setIframeError(errorMsg)
        if (import.meta.env.DEV) {
          console.error('[Monitoring] 보안 정책 에러 감지:', errorMessage)
        }
      }
    }

    const originalConsoleError = console.error
    console.error = (...args: unknown[]) => {
      const errorText = args.join(' ')
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

  // 설비 변경 시 iframe 상태 초기화
  useEffect(() => {
    if (grafanaDashboardUrl && selectedDevice) {
      setIframeError(null)
      
      if (import.meta.env.DEV) {
        console.log('[Monitoring] Grafana 대시보드 URL:', grafanaDashboardUrl)
      }
      
      // 이전 타임아웃이 있으면 취소
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
      
      // iframe 로드 상태 초기화
      setIframeLoaded(false)
    }
  }, [selectedDevice, timeRange, grafanaDashboardUrl])

  if (loading && !selectedDevice) {
    return (
      <div className="bg-transparent p-6">
        <Loading message="설비 정보를 불러오는 중..." />
      </div>
    )
  }

  if (!selectedDevice) {
    return (
      <div className="bg-transparent p-6">
        <div className="text-center py-20 bg-background-surface border border-border rounded-xl">
          <div className="text-text-secondary text-6xl mb-4">🏭</div>
          <p className="text-text-primary text-lg mb-2">등록된 설비가 없습니다.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full h-[calc(100vh-80px)] flex flex-col bg-transparent">
      {/* 에러 메시지 */}
      {iframeError && (
        <div className="mx-8 mb-4 p-4 bg-danger/10 border-l-4 border-danger rounded-xl">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-danger mr-2 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <p className="text-danger font-medium whitespace-pre-line">{iframeError}</p>
            </div>
          </div>
        </div>
      )}

      {/* Grafana 대시보드 컨테이너 (사이드바 제외 가로 최대) */}
      <div className="flex-1 relative min-h-0 mb-6">
        {selectedDevice && grafanaDashboardUrl ? (
          <div className="w-full h-full bg-background-surface border border-border rounded-xl overflow-hidden">
            <iframe
              ref={iframeRef}
              src={grafanaDashboardUrl}
              className="w-full h-full border-0"
              title={`${selectedDevice?.name || ''} 모니터링 대시보드`}
              allow="fullscreen"
              onLoad={handleIframeLoad}
              onError={handleIframeError}
              sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-presentation"
              referrerPolicy="no-referrer-when-downgrade"
              loading="lazy"
            />
          </div>
        ) : (
          <div className="flex items-center justify-center h-full bg-background-surface border border-border rounded-xl">
            <div className="text-center p-4">
              <svg className="w-16 h-16 text-text-secondary mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-text-primary text-lg">Grafana 대시보드 URL을 생성할 수 없습니다</p>
              <p className="text-text-secondary text-sm mt-2">환경 변수를 확인하세요</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Monitoring

