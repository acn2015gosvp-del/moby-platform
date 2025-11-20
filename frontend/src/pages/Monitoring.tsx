/**
 * 설비 모니터링 페이지
 * 
 * 실시간 설비 상태 및 센서 데이터를 Grafana 대시보드로 표시
 */

import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { DeviceSummary, SensorStatusResponse } from '@/types/sensor'
import { getSensorStatus } from '@/services/sensors/sensorService'
import { GRAFANA_CONFIG } from '@/utils/grafana'
import Loading from '@/components/common/Loading'

const Monitoring: React.FC = () => {
  const { deviceId } = useParams<{ deviceId: string }>()
  const navigate = useNavigate()
  
  const [devices, setDevices] = useState<DeviceSummary[]>([])
  const [selectedDevice, setSelectedDevice] = useState<DeviceSummary | null>(null)
  const [timeRange, setTimeRange] = useState<string>('1h')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [iframeLoading, setIframeLoading] = useState(true)
  const [iframeError, setIframeError] = useState<string | null>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  const [serverStatus, setServerStatus] = useState<{
    checking: boolean
    reachable: boolean | null
    message: string
  }>({ checking: false, reachable: null, message: '' })

  // 시간 범위 옵션
  const timeRangeOptions = [
    { value: '1h', label: '최근 1시간' },
    { value: '6h', label: '최근 6시간' },
    { value: '24h', label: '최근 24시간' },
    { value: '7d', label: '최근 7일' },
    { value: '30d', label: '최근 30일' },
  ]

  // 시간 범위 선택 기능은 환경 변수 URL 사용 시 비활성화됨

  // 설비 목록 가져오기
  useEffect(() => {
    const fetchDevices = async () => {
      try {
        setLoading(true)
        setError(null)

        const response = await getSensorStatus()
        
        if (response.success && response.data) {
          const data = response.data as SensorStatusResponse
          if (data.devices && data.devices.length > 0) {
            setDevices(data.devices)
            
            // URL 파라미터로 전달된 deviceId로 설비 선택
            if (deviceId) {
              const device = data.devices.find(d => d.device_id === deviceId)
              if (device) {
                setSelectedDevice(device)
              } else {
                // deviceId가 없으면 첫 번째 설비 선택
                setSelectedDevice(data.devices[0])
              }
            } else {
              // deviceId가 없으면 첫 번째 설비 선택
              setSelectedDevice(data.devices[0])
            }
          } else {
            setDevices([])
            setSelectedDevice(null)
          }
        } else {
          setDevices([])
          setSelectedDevice(null)
        }
      } catch (err: any) {
        console.error('설비 목록 로딩 실패:', err)
        setError(err.response?.data?.message || '설비 목록을 불러오는데 실패했습니다.')
      } finally {
        setLoading(false)
      }
    }

    fetchDevices()
  }, [deviceId])

  // 설비 변경 시 URL 업데이트
  const handleDeviceChange = (device: DeviceSummary) => {
    setSelectedDevice(device)
    navigate(`/monitoring/${device.device_id}`, { replace: true })
    setRefreshKey(prev => prev + 1) // iframe 강제 새로고침
  }

  // 새로고침
  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1)
  }

  // 내보내기 (Grafana URL을 새 창으로 열기)
  const handleExport = () => {
    const grafanaUrl = grafanaDashboardUrl
    if (grafanaUrl) {
      if (import.meta.env.DEV) {
        console.log('[Monitoring] 새 창에서 Grafana 대시보드 열기:', grafanaUrl)
      }
      window.open(grafanaUrl, '_blank', 'noopener,noreferrer')
    } else {
      alert('Grafana 대시보드 URL이 설정되지 않았습니다. 환경 변수 VITE_GRAFANA_DASHBOARD_URL을 확인하세요.')
    }
  }

  // Grafana 대시보드 URL (환경 변수에 설정된 URL만 사용, 생성하지 않음)
  const grafanaDashboardUrl = GRAFANA_CONFIG.DASHBOARD_URL || ''
  
  // URL이 설정되지 않았으면 에러 표시
  useEffect(() => {
    if (!grafanaDashboardUrl) {
      const errorMsg = 'Grafana 대시보드 URL이 설정되지 않았습니다.\n\n해결 방법:\n1. frontend/.env 파일에 다음 추가:\n   VITE_GRAFANA_DASHBOARD_URL=http://192.168.80.99:3001/public-dashboards/...\n\n2. Vite 개발 서버 재시작'
      setIframeError(errorMsg)
      setIframeLoading(false)
    }
  }, [grafanaDashboardUrl])

  // iframe 로드 완료 핸들러
  const handleIframeLoad = () => {
    // 타임아웃 취소
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    
    if (import.meta.env.DEV) {
      console.log('[Monitoring] iframe onLoad 이벤트 발생')
    }
    // 약간의 지연 후 로딩 상태 해제 (실제 콘텐츠 로드 확인)
    setTimeout(() => {
      setIframeLoading(false)
      setIframeError(null)
      // iframe이 로드되면 서버가 작동하는 것이므로 서버 상태 업데이트
      setServerStatus({ 
        checking: false, 
        reachable: true, 
        message: '대시보드 로드 완료' 
      })
      if (import.meta.env.DEV) {
        console.log('[Monitoring] Grafana 대시보드 로드 완료')
      }
    }, 1000)
  }

  // iframe 에러 핸들러 (일부 브라우저에서 작동하지 않을 수 있음)
  const handleIframeError = () => {
    if (import.meta.env.DEV) {
      console.error('[Monitoring] iframe onError 이벤트 발생')
    }
    setIframeLoading(false)
    
    // X-Frame-Options 에러 감지
    const errorMsg = `Grafana 대시보드 로드 실패\n\n가능한 원인:\n1. Grafana 서버에서 iframe 임베딩이 차단됨\n   → Grafana 설정 파일에서 allow_embedding = true 확인\n   → 또는 Grafana UI에서 Settings → Security → Allow embedding 확인\n   → Grafana 서버 재시작 필요\n\n2. X-Frame-Options 정책 위반\n   → Grafana 서버가 X-Frame-Options: deny를 설정하고 있음\n   → allow_embedding = true 설정으로 해결 가능\n\n3. CORS 정책 위반\n   → Grafana 설정에서 CORS 허용 확인\n\n해결 방법:\n1. Grafana 설정 파일(grafana.ini)에 다음 추가:\n   [security]\n   allow_embedding = true\n\n2. Grafana 서버 재시작\n\n3. "새 창에서 열기" 버튼으로 URL 직접 테스트`
    
    setIframeError(errorMsg)
  }

  // X-Frame-Options 및 보안 에러 감지 (전역 에러 리스너)
  useEffect(() => {
    const handleSecurityError = (event: ErrorEvent) => {
      const errorMessage = event.message || ''
      
      // X-Frame-Options 에러 감지
      if (errorMessage.includes('X-Frame-Options') || 
          errorMessage.includes('frame') || 
          errorMessage.includes('Refused to display')) {
        setIframeLoading(false)
        const errorMsg = `❌ X-Frame-Options 정책 위반: iframe 임베딩 차단\n\n직접 URL 접속은 성공하지만 iframe에서 로드되지 않습니다.\n이는 Grafana 서버에서 iframe 임베딩이 차단되었기 때문입니다.\n\n현재 URL: ${grafanaDashboardUrl}\n\n에러 메시지:\n"Refused to display in a frame because it set 'X-Frame-Options' to 'deny'"\n\n🔧 해결 방법 (설정 파일 수정):\n\n1. Grafana 설정 파일(grafana.ini) 찾기:\n   - Linux: /etc/grafana/grafana.ini\n   - Docker: 볼륨 마운트된 설정 파일\n   - Windows: Grafana 설치 디렉토리/conf/grafana.ini\n\n2. [security] 섹션에 다음 추가:\n   [security]\n   allow_embedding = true\n\n3. Grafana 서버 재시작 (필수!):\n   - Docker: docker restart grafana\n   - Linux: sudo systemctl restart grafana-server\n   - Windows: Grafana 서비스 재시작\n\n4. 재시작 후 확인:\n   - 브라우저 캐시 삭제 (Ctrl+Shift+Delete)\n   - 페이지 새로고침 (F5)\n   - "새 창에서 열기" 버튼으로 URL이 정상 작동하는지 확인\n\n💡 참고:\n   - 직접 URL 접속이 성공한다면 네트워크 문제가 아니라 iframe 임베딩 정책 문제입니다.\n   - 설정 파일 수정 후 반드시 Grafana 서버를 재시작해야 합니다.`
        setIframeError(errorMsg)
        if (import.meta.env.DEV) {
          console.error('[Monitoring] 보안 정책 에러 감지:', errorMessage)
        }
      }
    }

    // 콘솔 에러도 감지 (X-Frame-Options는 콘솔에만 나타날 수 있음)
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
    // URL이 설정되어 있으면 iframe 로드 시작
    if (grafanaDashboardUrl) {
      setIframeLoading(true)
      setIframeError(null)
      
      if (import.meta.env.DEV) {
        console.log('[Monitoring] Grafana 대시보드 URL:', grafanaDashboardUrl)
      }
      
        // Grafana 서버 연결 확인 (비동기, 실패해도 계속 진행)
        // iframe이 실제로 로드되면 그것이 가장 정확한 지표이므로, 이 체크는 참고용으로만 사용
        const checkGrafanaConnection = async () => {
          // 실제 사용 중인 대시보드 URL의 origin을 사용
          const baseUrl = grafanaDashboardUrl 
            ? new URL(grafanaDashboardUrl).origin 
            : (import.meta.env.VITE_GRAFANA_URL?.replace(/\/$/, '') || 'http://localhost:3000')

          if (import.meta.env.DEV) {
            console.log('[Monitoring] Grafana 서버 확인:', baseUrl)
            console.log('[Monitoring] 전체 대시보드 URL:', grafanaDashboardUrl)
          }
        // 서버 상태를 확인 중으로 표시하지 않음 (사용자 경험 개선)
        // 대신 백그라운드에서 조용히 확인
        
        try {
          // Public Dashboard는 로드 시간이 오래 걸릴 수 있으므로 타임아웃을 늘림 (10초)
          const controller = new AbortController()
          const timeoutId = setTimeout(() => controller.abort(), 10000)
          
          try {
            const startTime = Date.now()
            // HEAD 요청으로 빠르게 확인 (응답 본문 없이 헤더만 확인)
            await fetch(baseUrl, {
              method: 'HEAD',
              signal: controller.signal,
              mode: 'no-cors', // CORS 우회
              cache: 'no-cache',
            })
            clearTimeout(timeoutId)
            const duration = Date.now() - startTime
            
            if (import.meta.env.DEV) {
              console.log(`[Monitoring] ✅ Grafana 서버 연결 확인 성공 (${duration}ms)`)
            }
            
            setServerStatus({ 
              checking: false, 
              reachable: true, 
              message: `서버 연결 확인됨 (${duration}ms)` 
            })
          } catch (err: any) {
            clearTimeout(timeoutId)
            
            if (err?.name === 'AbortError') {
              // 타임아웃은 서버가 느리게 응답하거나 네트워크 문제일 수 있음
              if (import.meta.env.DEV) {
                console.warn(`[Monitoring] ⚠️ 서버 연결 확인 타임아웃 (10초) - ${baseUrl} 서버가 응답하지 않습니다`)
              }
              setServerStatus({ 
                checking: false, 
                reachable: false, 
                message: `서버 연결 타임아웃 (10초)\n\n가능한 원인:\n1. Grafana 서버가 실행되지 않음\n2. 네트워크 연결 문제\n3. 방화벽이 포트를 차단\n\n해결 방법:\n1. Grafana 서버 상태 확인\n2. 네트워크 연결 확인\n3. 브라우저에서 직접 URL 접속 테스트`
              })
            } else {
              // 네트워크 에러 등
              if (import.meta.env.DEV) {
                console.warn('[Monitoring] 서버 연결 확인 실패:', err?.message || err)
              }
              setServerStatus({ 
                checking: false, 
                reachable: false, 
                message: `서버 연결 실패\n\n에러: ${err?.message || '알 수 없는 오류'}\n\n가능한 원인:\n1. Grafana 서버가 실행되지 않음\n2. 네트워크 연결 문제\n3. 방화벽이 포트를 차단\n\n해결 방법:\n1. Grafana 서버 상태 확인\n2. 네트워크 연결 확인\n3. 브라우저에서 직접 URL 접속 테스트`
              })
            }
          }
          
        } catch (error: any) {
          // 예상치 못한 에러
          if (import.meta.env.DEV) {
            console.error('[Monitoring] 서버 연결 확인 중 예상치 못한 오류:', error?.message || error)
          }
          setServerStatus({ 
            checking: false, 
            reachable: false, 
            message: `서버 연결 확인 중 오류 발생\n\n에러: ${error?.message || '알 수 없는 오류'}`
          })
        }
      }
      
      // 비동기로 실행 (실패해도 계속 진행)
      checkGrafanaConnection().catch(() => {
        // 조용히 실패 처리
      })
      
      // 이전 타임아웃이 있으면 취소
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
      
      // 15초 후에도 로딩 중이면 타임아웃으로 간주 (더 긴 시간 제공)
      timeoutRef.current = setTimeout(() => {
        setIframeLoading((prevLoading) => {
          if (prevLoading) {
            const baseUrl = String(import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3000')
            const dashboardUrl = grafanaDashboardUrl || ''
            
            // 더 상세한 진단 정보 제공
            const errorMsg = `대시보드 로딩 시간이 초과되었습니다.\n\n가능한 원인:\n1. Grafana 서버에서 iframe 임베딩이 차단됨 (X-Frame-Options)\n   → Grafana 설정 파일에서 allow_embedding = true 확인\n   → 또는 Grafana UI에서 Settings → Security → Allow embedding 확인\n   → Grafana 서버 재시작 필요\n\n2. Grafana 서버가 실행 중이지 않음\n   → 브라우저에서 직접 URL 접속 시도\n\n3. 대시보드 URL이 올바르지 않음\n   → 환경 변수 VITE_GRAFANA_DASHBOARD_URL 확인 필요\n\n사용 중인 URL:\n${dashboardUrl || '(URL이 설정되지 않음)'}\n\n💡 해결 방법:\n1. Grafana 설정 파일(grafana.ini)에 다음 추가:\n   [security]\n   allow_embedding = true\n\n2. Grafana 서버 재시작\n\n3. "새 창에서 열기" 버튼으로 URL 직접 테스트\n4. 브라우저 콘솔(F12)에서 X-Frame-Options 에러 확인`
            
            setIframeError(errorMsg)
            if (import.meta.env.DEV) {
              console.warn('[Monitoring] Grafana 대시보드 로딩 타임아웃', {
                url: dashboardUrl,
                deviceId: String(selectedDevice?.device_id || ''),
                deviceName: String(selectedDevice?.name || ''),
              troubleshooting: [
                '1. Grafana 서버가 실행 중인지 확인',
                '2. Grafana 설정에서 allow_embedding = true 확인',
                '3. 대시보드 UID가 실제 Grafana 대시보드와 일치하는지 확인',
                '4. 브라우저 콘솔에서 네트워크 에러 확인'
              ]
              })
            }
            return false
          }
          return prevLoading
        })
      }, 15000)

      return () => {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current)
          timeoutRef.current = null
        }
      }
    }
  }, [selectedDevice, timeRange, refreshKey])

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
      </div>

      {/* 필터 및 액션 버튼 */}
      <div className="mb-6 flex flex-wrap items-center gap-4">
        {/* 설비 선택 드롭다운 */}
        <div className="flex-1 min-w-[200px]">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            설비 선택
          </label>
          <select
            value={selectedDevice?.device_id || ''}
            onChange={(e) => {
              const device = devices.find(d => d.device_id === e.target.value)
              if (device) handleDeviceChange(device)
            }}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
          >
            {devices.map((device) => (
              <option key={device.device_id} value={device.device_id}>
                {device.name}
              </option>
            ))}
          </select>
        </div>

        {/* 시간 범위 선택 드롭다운 */}
        <div className="flex-1 min-w-[150px]">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            시간 범위
          </label>
          <select
            value={timeRange}
            onChange={(e) => {
              setTimeRange(e.target.value)
              setRefreshKey(prev => prev + 1)
            }}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
          >
            {timeRangeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* 액션 버튼 */}
        <div className="flex gap-2 items-end">
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            새로고침
          </button>
          <button
            onClick={handleExport}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            내보내기
          </button>
        </div>
      </div>

      {/* Grafana 대시보드 섹션 */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-800">
            실시간 모니터링 대시보드
          </h2>
          <button
            onClick={() => {
              const url = grafanaDashboardUrl
              window.open(url, '_blank', 'noopener,noreferrer')
            }}
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
          {selectedDevice ? (
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
                      <button
                        onClick={() => {
                          const url = grafanaDashboardUrl
                          if (url) {
                            navigator.clipboard.writeText(url).then(() => {
                              alert('URL이 클립보드에 복사되었습니다.\n\n브라우저 주소창에 붙여넣어 직접 테스트하세요.')
                            }).catch(() => {
                              alert(`URL을 복사할 수 없습니다.\n\n다음 URL을 직접 사용하세요:\n\n${url}`)
                            })
                          }
                        }}
                        className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                      >
                        📋 URL 복사
                      </button>
                    </div>
                    <div className="mt-4 space-y-3">
                      {/* 서버 상태 표시 */}
                      {serverStatus.checking && (
                        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                          <div className="flex items-center gap-2">
                            <div className="w-4 h-4 border-2 border-yellow-600 border-t-transparent rounded-full animate-spin"></div>
                            <p className="text-yellow-800 text-sm">{serverStatus.message}</p>
                          </div>
                        </div>
                      )}
                      
                      {!serverStatus.checking && serverStatus.reachable !== null && (
                        <div className={`p-3 border rounded-lg ${
                          serverStatus.reachable 
                            ? 'bg-green-50 border-green-200' 
                            : 'bg-red-50 border-red-200'
                        }`}>
                          <div className="flex items-center gap-2 mb-2">
                            {serverStatus.reachable ? (
                              <>
                                <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <p className="text-green-800 text-sm font-medium">서버 연결 성공</p>
                              </>
                            ) : (
                              <>
                                <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <p className="text-red-800 text-sm font-medium">서버 연결 실패</p>
                              </>
                            )}
                          </div>
                          <p className={`text-xs ${serverStatus.reachable ? 'text-green-700' : 'text-red-700'}`}>
                            {serverStatus.message}
                          </p>
                          {!serverStatus.reachable && (
                            <div className="mt-2 text-xs text-red-600 space-y-1">
                              <p className="font-medium">💡 확인 사항:</p>
                              <ul className="list-disc list-inside ml-2 space-y-0.5">
                                <li>Grafana 서버가 실행 중인지 확인</li>
                                <li>URL이 올바른지 확인: <code className="bg-red-100 px-1 rounded">{import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3000'}</code></li>
                                <li>방화벽 설정 확인</li>
                                <li>네트워크 연결 확인</li>
                                <li>서버 로그 확인</li>
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                      
                      {/* 진단 도구 */}
                      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="text-blue-800 text-sm font-medium mb-2">🔧 진단 도구</p>
                        <div className="space-y-2">
                          <div className="text-xs text-gray-600 mb-2 p-2 bg-white rounded border">
                            <strong>현재 사용 중인 URL:</strong><br />
                            <code className="text-xs break-all">{grafanaDashboardUrl || '(URL이 설정되지 않음)'}</code>
                          </div>
                          <button
                            onClick={() => {
                              window.open(grafanaDashboardUrl, '_blank', 'noopener,noreferrer')
                            }}
                            className="block w-full text-left text-xs text-blue-600 hover:text-blue-800 underline"
                          >
                            📍 대시보드 URL 직접 열기 (새 창)
                          </button>
                          <button
                            onClick={() => {
                              const baseUrl = grafanaDashboardUrl ? new URL(grafanaDashboardUrl).origin : (import.meta.env.VITE_GRAFANA_URL?.replace(/\/$/, '') || 'http://localhost:3000')
                              window.open(baseUrl, '_blank', 'noopener,noreferrer')
                            }}
                            className="block w-full text-left text-xs text-blue-600 hover:text-blue-800 underline"
                          >
                            📍 Grafana 서버 직접 접속: {grafanaDashboardUrl ? new URL(grafanaDashboardUrl).origin : (import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3000')}
                          </button>
                          <button
                            onClick={async () => {
                              // 실제 사용 중인 대시보드 URL의 origin을 사용
                              const baseUrl = grafanaDashboardUrl 
                                ? new URL(grafanaDashboardUrl).origin 
                                : (import.meta.env.VITE_GRAFANA_URL?.replace(/\/$/, '') || 'http://localhost:3000')
                              
                              setServerStatus({ checking: true, reachable: null, message: `서버 연결 확인 중: ${baseUrl}` })
                              try {
                                const controller = new AbortController()
                                const timeoutId = setTimeout(() => controller.abort(), 8000)
                                const startTime = Date.now()
                                await fetch(baseUrl, { method: 'GET', signal: controller.signal, mode: 'no-cors' })
                                clearTimeout(timeoutId)
                                const duration = Date.now() - startTime
                                setServerStatus({ checking: false, reachable: true, message: `서버 연결 성공 (${duration}ms)` })
                              } catch (err: any) {
                                if (err?.name === 'AbortError') {
                                  setServerStatus({ checking: false, reachable: false, message: `서버 연결 타임아웃 (8초) - ${baseUrl} 서버가 실행 중인지 확인하세요` })
                                } else {
                                  setServerStatus({ checking: false, reachable: false, message: `연결 실패: ${err?.message || '알 수 없는 오류'} (${baseUrl})` })
                                }
                              }
                            }}
                            className="block w-full text-left text-xs text-blue-600 hover:text-blue-800 underline"
                          >
                            🔄 서버 연결 다시 확인
                          </button>
                          <p className="text-blue-700 text-xs mt-2">
                            브라우저 콘솔(F12)에서 상세한 진단 정보를 확인할 수 있습니다.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* iframe */}
              {grafanaDashboardUrl ? (
                <iframe
                  key={refreshKey}
                  src={grafanaDashboardUrl}
                  className="w-full h-full border-0"
                  title={`${String(selectedDevice?.name || '')} 모니터링 대시보드`}
                  allow="fullscreen"
                  style={{ minHeight: '600px' }}
                  onLoad={handleIframeLoad}
                  onError={handleIframeError}
                  sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-presentation"
                  referrerPolicy="no-referrer-when-downgrade"
                />
              ) : (
                <div className="flex items-center justify-center h-full bg-gray-50">
                  <div className="text-center">
                    <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-gray-500 text-lg">Grafana 대시보드 URL이 설정되지 않았습니다</p>
                    <p className="text-gray-400 text-sm mt-2">환경 변수 VITE_GRAFANA_DASHBOARD_URL을 확인하세요</p>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center justify-center h-full bg-gray-50">
              <div className="text-center">
                <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p className="text-gray-500 text-lg">Grafana 대시보드 뷰</p>
                <p className="text-gray-400 text-sm mt-1">실시간 센서 데이터 및 성능 메트릭</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Monitoring



