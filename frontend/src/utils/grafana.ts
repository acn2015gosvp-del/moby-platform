/**
 * Grafana 설정 및 API 클라이언트
 * 
 * Grafana API를 사용하여 대시보드 정보를 가져오고 동적으로 URL을 생성합니다.
 */

/**
 * Grafana 설정
 * 
 * 대시보드 정보:
 * - UID: adckqfq
 * - 이름: conv1
 */
export const GRAFANA_CONFIG = {
  // Grafana 임베딩 주소를 192.168.80.183:8080으로 고정
  BASE_URL: import.meta.env.VITE_GRAFANA_BASE_URL || 'http://192.168.80.183:8080',
  API_KEY: import.meta.env.VITE_GRAFANA_API_KEY || '',
  DEFAULT_ORG_ID: parseInt(import.meta.env.VITE_GRAFANA_ORG_ID || '1', 10),
  DEFAULT_DASHBOARD_UID: import.meta.env.VITE_GRAFANA_DASHBOARD_UID || 'adckqfq', // conv1 대시보드
  DEFAULT_TIME_RANGE: {
    from: 'now-6h',
    to: 'now',
  },
} as const

/**
 * Grafana API 엔드포인트 URL 생성
 * @param endpoint - API 엔드포인트 경로
 * @returns 완성된 API URL
 */
export const buildGrafanaApiUrl = (endpoint: string): string => {
  const { BASE_URL } = GRAFANA_CONFIG
  const baseUrl = BASE_URL.replace(/\/$/, '')
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  return `${baseUrl}/api${normalizedEndpoint}`
}

/**
 * Grafana API 요청 헤더 생성
 * @returns API 요청에 사용할 헤더
 */
export const getGrafanaApiHeaders = (): HeadersInit => {
  const { API_KEY } = GRAFANA_CONFIG
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }
  
  if (API_KEY) {
    headers['Authorization'] = `Bearer ${API_KEY}`
  }
  
  return headers
}

/**
 * Grafana 대시보드 정보 타입
 */
export interface GrafanaDashboard {
  uid: string
  title: string
  url: string
  version: number
  tags?: string[]
}

/**
 * Grafana API를 사용하여 대시보드 정보 가져오기 (백엔드 프록시 사용)
 * @param dashboardUID - 대시보드 UID
 * @returns 대시보드 정보
 */
export const getGrafanaDashboard = async (dashboardUID: string): Promise<GrafanaDashboard | null> => {
  // 백엔드 프록시를 통해 Grafana API 호출 (CORS 문제 해결)
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://192.168.80.33:8000'
  
  try {
    const url = `${API_BASE_URL}/api/proxy-grafana/dashboard/${dashboardUID}`
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      if (response.status === 404) {
        console.warn(`[Grafana] 대시보드를 찾을 수 없습니다: ${dashboardUID}`)
        return null
      }
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.message || `Grafana API 요청 실패: ${response.status} ${response.statusText}`)
    }
    
    const result = await response.json()
    
    if (!result.success || !result.data) {
      console.warn(`[Grafana] 대시보드 정보 조회 실패: ${result.message || '알 수 없는 오류'}`)
      return null
    }
    
    return {
      uid: result.data.uid,
      title: result.data.title,
      url: result.data.url || `/d/${result.data.uid}`,
      version: result.data.version || 1,
      tags: result.data.tags || [],
    }
  } catch (error: unknown) {
    console.error('[Grafana] 대시보드 정보 가져오기 실패:', error)
    throw error
  }
}

/**
 * Grafana 대시보드 URL 생성 (API를 사용하여 동적으로 생성)
 * @param dashboardUID - Grafana 대시보드 UID
 * @param deviceId - 설비 ID (선택사항, 변수로 전달)
 * @param timeRange - 시간 범위 (선택사항)
 * @returns 완성된 Grafana 대시보드 URL
 */
export const buildGrafanaDashboardUrl = (
  dashboardUID: string,
  deviceId?: string,
  timeRange?: { from: string; to: string },
  theme: 'dark' | 'light' = 'dark'
): string => {
  const { BASE_URL, DEFAULT_ORG_ID, DEFAULT_TIME_RANGE } = GRAFANA_CONFIG
  const baseUrl = BASE_URL.replace(/\/$/, '')
  
  const range = timeRange || DEFAULT_TIME_RANGE
  const params = new URLSearchParams({
    orgId: DEFAULT_ORG_ID.toString(),
    from: range.from,
    to: range.to,
    refresh: '5s', // 5초마다 자동 새로고침
  })

  // deviceId가 있으면 변수로 추가
  if (deviceId) {
    params.append('var-device_id', deviceId)
  }

  // kiosk 파라미터 추가 (값 없이)
  params.append('kiosk', '')

  // 테마 파라미터 추가
  params.append('theme', theme)

  const url = `${baseUrl}/d/${dashboardUID}/view?${params.toString()}`
  
  // 디버깅: kiosk 파라미터 확인
  if (import.meta.env.DEV) {
    console.log('[Grafana] 생성된 URL:', url)
    console.log('[Grafana] kiosk 파라미터 포함 여부:', params.toString().includes('kiosk'))
  }
  
  return url
}

/**
 * Grafana 서버 연결 확인 (백엔드 프록시 사용)
 * @returns 서버가 응답하는지 여부
 */
export const checkGrafanaConnection = async (): Promise<boolean> => {
  // 백엔드 프록시를 통해 Grafana 서버 상태 확인 (CORS 문제 해결)
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://192.168.80.33:8000'
  
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000)
    
    const response = await fetch(`${API_BASE_URL}/api/proxy-grafana/health`, {
      method: 'GET',
      signal: controller.signal,
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      return false
    }
    
    const result = await response.json()
    return result.success && result.data?.connected === true
  } catch (error) {
    console.error('[Grafana] 연결 확인 실패:', error)
    return false
  }
}