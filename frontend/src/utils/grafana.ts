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
  BASE_URL: import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3000',
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
 * Grafana API를 사용하여 대시보드 정보 가져오기
 * @param dashboardUID - 대시보드 UID
 * @returns 대시보드 정보
 */
export const getGrafanaDashboard = async (dashboardUID: string): Promise<GrafanaDashboard | null> => {
  const { API_KEY, BASE_URL } = GRAFANA_CONFIG
  
  if (!API_KEY) {
    console.warn('[Grafana] API 키가 설정되지 않았습니다. 환경 변수 VITE_GRAFANA_API_KEY를 확인하세요.')
    return null
  }
  
  try {
    const url = buildGrafanaApiUrl(`/dashboards/uid/${dashboardUID}`)
    const response = await fetch(url, {
      method: 'GET',
      headers: getGrafanaApiHeaders(),
    })
    
    if (!response.ok) {
      if (response.status === 404) {
        console.warn(`[Grafana] 대시보드를 찾을 수 없습니다: ${dashboardUID}`)
        return null
      }
      throw new Error(`Grafana API 요청 실패: ${response.status} ${response.statusText}`)
    }
    
    const data = await response.json()
    const dashboard = data.dashboard
    
    return {
      uid: dashboard.uid,
      title: dashboard.title,
      url: dashboard.url || `/d/${dashboard.uid}`,
      version: dashboard.version || 1,
      tags: dashboard.tags || [],
    }
  } catch (error: any) {
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
  timeRange?: { from: string; to: string }
): string => {
  const { BASE_URL, DEFAULT_ORG_ID, DEFAULT_TIME_RANGE } = GRAFANA_CONFIG
  const baseUrl = BASE_URL.replace(/\/$/, '')
  
  const range = timeRange || DEFAULT_TIME_RANGE
  const params = new URLSearchParams({
    orgId: DEFAULT_ORG_ID.toString(),
    from: range.from,
    to: range.to,
    refresh: '30s',
    kiosk: 'tv',
  })

  // deviceId가 있으면 변수로 추가
  if (deviceId) {
    params.append('var-device_id', deviceId)
  }

  return `${baseUrl}/d/${dashboardUID}/view?${params.toString()}`
}

/**
 * Grafana 서버 연결 확인
 * @returns 서버가 응답하는지 여부
 */
export const checkGrafanaConnection = async (): Promise<boolean> => {
  const { BASE_URL } = GRAFANA_CONFIG
  const baseUrl = BASE_URL.replace(/\/$/, '')
  
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000)
    
    await fetch(`${baseUrl}/api/health`, {
      method: 'GET',
      signal: controller.signal,
      mode: 'no-cors',
    })
    
    clearTimeout(timeoutId)
    return true
  } catch (error) {
    return false
  }
}