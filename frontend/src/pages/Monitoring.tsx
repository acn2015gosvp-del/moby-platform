/**
 * 설비 모니터링 페이지
 * 
 * 실시간 설비 상태 및 센서 데이터를 Grafana 대시보드로 표시
 * Grafana API를 사용하여 동적으로 대시보드 URL을 생성합니다.
 */

import React, { useState, useEffect, useRef, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { DeviceSummary } from '@/types/sensor'
import {
  GRAFANA_CONFIG,
  buildGrafanaDashboardUrl,
  getGrafanaDashboard,
  checkGrafanaConnection,
  type GrafanaDashboard,
} from '@/utils/grafana'
import { useDeviceContext } from '@/context/DeviceContext'
import Loading from '@/components/common/Loading'

const Monitoring: React.FC = () => {
  const { deviceId } = useParams<{ deviceId?: string }>()
  const navigate = useNavigate()
  const { devices, selectedDevice, setSelectedDeviceId } = useDeviceContext()
  const [timeRange, setTimeRange] = useState<string>('1h')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [iframeLoading, setIframeLoading] = useState(true)
  const [iframeError, setIframeError] = useState<string | null>(null)
  const [dashboardInfo, setDashboardInfo] = useState<GrafanaDashboard | null>(null)
  const [grafanaConnected, setGrafanaConnected] = useState<boolean | null>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

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
  }, [timeRange])

  // Grafana 대시보드 URL 생성 (API 기반)
  const grafanaDashboardUrl = useMemo(() => {
    if (!selectedDevice || !GRAFANA_CONFIG.DEFAULT_DASHBOARD_UID) {
      return ''
    }
    
    return buildGrafanaDashboardUrl(
      GRAFANA_CONFIG.DEFAULT_DASHBOARD_UID,
      selectedDevice.device_id,
      selectedTimeRange
    )
  }, [selectedDevice, selectedTimeRange])

  // deviceId가 변경되면 해당 설비로 이동
  useEffect(() => {
    if (deviceId && deviceId !== selectedDevice?.device_id) {
      setSelectedDeviceId(deviceId)
    }
  }, [deviceId, selectedDevice, setSelectedDeviceId])

  // selectedDevice가 없고 deviceId가 있으면 로딩 상태
  useEffect(() => {
    if (deviceId && !selectedDevice) {
      setLoading(true)
    } else {
      setLoading(false)
    }
  }, [deviceId, selectedDevice])

  // Grafana 서버 연결 확인
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const connected = await checkGrafanaConnection()
        setGrafanaConnected(connected)
        if (import.meta.env.DEV) {
          console.log('[Monitoring] Grafana 서버 연결 상태:', connected)
        }
      } catch (error) {
        setGrafanaConnected(false)
        if (import.meta.env.DEV) {
          console.error('[Monitoring] Grafana 서버 연결 확인 실패:', error)
        }
      }
    }

    checkConnection()
  }, [])

  // Grafana 대시보드 정보 가져오기
  useEffect(() => {
    const fetchDashboardInfo = async () => {
      if (!GRAFANA_CONFIG.DEFAULT_DASHBOARD_UID) {
        setIframeError('Grafana 대시보드 UID가 설정되지 않았습니다.\n\n환경 변수 VITE_GRAFANA_DASHBOARD_UID를 확인하세요.')
        setIframeLoading(false)
        return
      }

      // API 키는 백엔드에서 관리하므로 프론트엔드에서는 확인하지 않음

      try {
        const dashboard = await getGrafanaDashboard(GRAFANA_CONFIG.DEFAULT_DASHBOARD_UID)
        if (dashboard) {
          setDashboardInfo(dashboard)
          if (import.meta.env.DEV) {
            console.log('[Monitoring] 대시보드 정보:', dashboard)
          }
        } else {
          setIframeError(`대시보드를 찾을 수 없습니다: ${GRAFANA_CONFIG.DEFAULT_DASHBOARD_UID}\n\nGrafana에서 해당 UID의 대시보드가 존재하는지 확인하세요.`)
          setIframeLoading(false)
        }
      } catch (err: any) {
        console.error('[Monitoring] 대시보드 정보 가져오기 실패:', err)
        setIframeError(`대시보드 정보를 가져올 수 없습니다.\n\n에러: ${err.message || '알 수 없는 오류'}\n\n확인 사항:\n1. Grafana API 키가 올바른지 확인\n2. Grafana 서버가 실행 중인지 확인\n3. 대시보드 UID가 올바른지 확인`)
        setIframeLoading(false)
      }
    }

    fetchDashboardInfo()
  }, [])

  // 설비 변경 핸들러 - DeviceContext를 통해 URL 업데이트
  const handleDeviceChange = (newDeviceId: string) => {
    setSelectedDeviceId(newDeviceId)
    setRefreshKey(prev => prev + 1) // iframe 강제 새로고침
  }

  // 새로고침
  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1)
    setIframeLoading(true)
    setIframeError(null)
  }

  // 내보내기 (Grafana URL을 새 창으로 열기)
  const handleExport = () => {
    if (grafanaDashboardUrl) {
      if (import.meta.env.DEV) {
        console.log('[Monitoring] 새 창에서 Grafana 대시보드 열기:', grafanaDashboardUrl)
      }
      window.open(grafanaDashboardUrl, '_blank', 'noopener,noreferrer')
    } else {
      alert('Grafana 대시보드 URL을 생성할 수 없습니다.')
    }
  }

  // iframe 로드 완료 핸들러
  const handleIframeLoad = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    
    if (import.meta.env.DEV) {
      console.log('[Monitoring] iframe onLoad 이벤트 발생')
    }
    
    setTimeout(() => {
      setIframeLoading(false)
      setIframeError(null)
      if (import.meta.env.DEV) {
        console.log('[Monitoring] Grafana 대시보드 로드 완료')
      }
    }, 500)
  }

  // iframe 에러 핸들러
  const handleIframeError = () => {
    if (import.meta.env.DEV) {
      console.error('[Monitoring] iframe onError 이벤트 발생')
    }
    setIframeLoading(false)
    
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
        setIframeLoading(false)
        const errorMsg = `❌ X-Frame-Options 정책 위반: iframe 임베딩 차단\n\n직접 URL 접속은 성공하지만 iframe에서 로드되지 않습니다.\n이는 Grafana 서버에서 iframe 임베딩이 차단되었기 때문입니다.\n\n현재 URL: ${grafanaDashboardUrl}\n\n🔧 해결 방법:\n\n1. Grafana 설정 파일(grafana.ini)에 다음 추가:\n   [security]\n   allow_embedding = true\n\n2. Grafana 서버 재시작 (필수!)\n\n3. 재시작 후 확인:\n   - 브라우저 캐시 삭제 (Ctrl+Shift+Delete)\n   - 페이지 새로고침 (F5)`
        setIframeError(errorMsg)
        if (import.meta.env.DEV) {
          console.error('[Monitoring] 보안 정책 에러 감지:', errorMessage)
        }
      }
    }

    const originalConsoleError = console.error
    console.error = (...args: any[]) => {
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

  // 설비 변경 시 iframe 상태 초기화 및 타임아웃 설정
  useEffect(() => {
    if (grafanaDashboardUrl && selectedDevice) {
      setIframeLoading(true)
      setIframeError(null)
      
      if (import.meta.env.DEV) {
        console.log('[Monitoring] Grafana 대시보드 URL:', grafanaDashboardUrl)
      }
      
      // 이전 타임아웃이 있으면 취소
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
      
      // 30초 후에도 로딩 중이면 타임아웃으로 간주
      timeoutRef.current = setTimeout(() => {
        setIframeLoading((prevLoading) => {
          if (prevLoading) {
            const errorMsg = `대시보드 로딩 시간이 초과되었습니다.\n\n가능한 원인:\n1. Grafana 서버에서 iframe 임베딩이 차단됨 (X-Frame-Options)\n   → Grafana 설정 파일에서 allow_embedding = true 확인\n   → Grafana 서버 재시작 필요\n\n2. Grafana 서버가 실행 중이지 않음\n   → 브라우저에서 직접 URL 접속 시도\n\n3. 네트워크 연결 문제\n\n사용 중인 URL:\n${grafanaDashboardUrl}\n\n💡 해결 방법:\n1. Grafana 설정 파일(grafana.ini)에 다음 추가:\n   [security]\n   allow_embedding = true\n\n2. Grafana 서버 재시작\n\n3. "새 창에서 열기" 버튼으로 URL 직접 테스트`
            
            setIframeError(errorMsg)
            if (import.meta.env.DEV) {
              console.warn('[Monitoring] Grafana 대시보드 로딩 타임아웃', {
                url: grafanaDashboardUrl,
                deviceId: selectedDevice?.device_id,
                deviceName: selectedDevice?.name,
              })
            }
            return false
          }
          return prevLoading
        })
      }, 30000)

      return () => {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current)
          timeoutRef.current = null
        }
      }
    }
  }, [selectedDevice, timeRange, refreshKey, grafanaDashboardUrl])

  if (loading && !selectedDevice) {
    return (
      <div>
        <h1 className="text-3xl font-bold mb-6 text-gray-800">설비 모니터링</h1>
        <Loading message="설비 정보를 불러오는 중..." />
      </div>
    )
  }

  if (error && !selectedDevice) {
    return (
      <div>
        <h1 className="text-3xl font-bold mb-6 text-gray-800">설비 모니터링</h1>
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          {error}
        </div>
        <button
          onClick={() => window.location.reload()}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          다시 시도
        </button>
      </div>
    )
  }

  if (!selectedDevice) {
    return (
      <div>
        <h1 className="text-3xl font-bold mb-6 text-gray-800">설비 모니터링</h1>
        <div className="text-center py-20 bg-white rounded-lg shadow">
          <div className="text-gray-400 text-6xl mb-4">🏭</div>
          <p className="text-gray-500 text-lg mb-2">등록된 설비가 없습니다.</p>
        </div>
      </div>
    )
  }

  return (
    <div>
      {/* 헤더 섹션 */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">설비 모니터링</h1>
        <p className="text-gray-600">실시간 설비 상태 및 센서 데이터</p>
        {dashboardInfo && (
          <p className="text-sm text-gray-500 mt-1">대시보드: {dashboardInfo.title}</p>
        )}
      </div>


      {/* Grafana 연결 상태 표시 */}
      {grafanaConnected !== null && (
        <div className={`mb-4 p-3 rounded-lg border ${
          grafanaConnected 
            ? 'bg-green-50 border-green-200' 
            : 'bg-yellow-50 border-yellow-200'
        }`}>
          <div className="flex items-center gap-2">
            {grafanaConnected ? (
              <>
                <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-green-800 text-sm font-medium">Grafana 서버 연결됨</p>
              </>
            ) : (
              <>
                <svg className="w-5 h-5 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <p className="text-yellow-800 text-sm font-medium">Grafana 서버 연결 확인 중...</p>
              </>
            )}
          </div>
        </div>
      )}

      {/* Grafana 대시보드 섹션 */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-800">
            실시간 모니터링 대시보드
          </h2>
          <button
            onClick={handleExport}
            className="p-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
            title="전체 화면으로 열기"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>
        </div>
        
        {/* Grafana 대시보드 iframe */}
        <div className="relative" style={{ height: 'calc(100vh - 400px)', minHeight: '600px' }}>
          {selectedDevice && grafanaDashboardUrl ? (
            <>
              {/* 로딩 오버레이 */}
              {iframeLoading && (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-50 z-10">
                  <div className="text-center">
                    <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-600 text-lg font-medium">Grafana 대시보드 로딩 중...</p>
                    <p className="text-gray-400 text-sm mt-2">잠시만 기다려주세요</p>
                  </div>
                </div>
              )}

              {/* 에러 메시지 */}
              {iframeError && (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-50 z-10">
                  <div className="text-center max-w-md px-6">
                    <svg className="w-16 h-16 text-red-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-red-600 text-lg font-medium mb-2">대시보드 로드 실패</p>
                    {grafanaDashboardUrl && (
                      <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="text-blue-800 text-xs font-medium mb-1">현재 사용 중인 URL:</p>
                        <p className="text-blue-700 text-xs break-all font-mono">{grafanaDashboardUrl}</p>
                      </div>
                    )}
                    <div className="text-gray-600 text-sm mb-4 whitespace-pre-line text-left bg-gray-50 p-4 rounded-lg">
                      {iframeError}
                    </div>
                    <div className="flex gap-2 justify-center flex-wrap">
                      <button
                        onClick={() => {
                          setIframeError(null)
                          setIframeLoading(true)
                          setRefreshKey(prev => prev + 1)
                        }}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        다시 시도
                      </button>
                      <button
                        onClick={handleExport}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-semibold"
                      >
                        ✨ 새 창에서 열기 (권장)
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* iframe */}
              <iframe
                key={refreshKey}
                src={grafanaDashboardUrl}
                className="w-full h-full border-0"
                title={`${selectedDevice?.name || ''} 모니터링 대시보드`}
                allow="fullscreen"
                style={{ minHeight: '600px' }}
                onLoad={handleIframeLoad}
                onError={handleIframeError}
                sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-presentation"
                referrerPolicy="no-referrer-when-downgrade"
              />
            </>
          ) : (
            <div className="flex items-center justify-center h-full bg-gray-50">
              <div className="text-center">
                <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-gray-500 text-lg">Grafana 대시보드 URL을 생성할 수 없습니다</p>
                <p className="text-gray-400 text-sm mt-2">환경 변수를 확인하세요</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Monitoring

