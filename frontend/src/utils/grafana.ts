/**
 * Grafana 설정 및 URL 빌더
 */

/**
 * Grafana 설정
 */
export const GRAFANA_CONFIG = {
  BASE_URL: import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3000',
  // 전체 대시보드 URL이 환경 변수에 설정되어 있으면 그대로 사용
  DASHBOARD_URL: import.meta.env.VITE_GRAFANA_DASHBOARD_URL || '',
  DEFAULT_ORG_ID: 1,
  DEFAULT_TIME_RANGE: {
    from: 'now-6h',
    to: 'now',
  },
  // 모든 설비에 공통으로 사용할 대시보드 UID (DASHBOARD_URL이 없을 때만 사용)
  DEFAULT_DASHBOARD_UID: import.meta.env.VITE_GRAFANA_DASHBOARD_UID || 'conveyor-dashboard',
} as const

/**
 * Grafana 대시보드 URL 생성
 * @param dashboardUID - Grafana 대시보드 UID
 * @param deviceId - 설비 ID (선택사항)
 * @returns 완성된 Grafana URL
 */
export const buildGrafanaUrl = (dashboardUID: string, deviceId?: string): string => {
  const { BASE_URL, DEFAULT_ORG_ID, DEFAULT_TIME_RANGE } = GRAFANA_CONFIG
  
  // BASE_URL 끝의 슬래시 제거 (이중 슬래시 방지)
  const baseUrl = BASE_URL.replace(/\/$/, '')
  
  const params = new URLSearchParams({
    orgId: DEFAULT_ORG_ID.toString(),
    from: DEFAULT_TIME_RANGE.from,
    to: DEFAULT_TIME_RANGE.to,
    refresh: '30s',
    kiosk: 'tv',
  })

  // deviceId가 있으면 추가
  if (deviceId) {
    params.append('var-device_id', deviceId)
  }

  const url = `${baseUrl}/d/${dashboardUID}/view?${params.toString()}`
  console.log('[Grafana] 생성된 URL:', url)
  return url
}

// Grafana API는 현재 사용하지 않으므로 제거됨
// 필요시 다음 함수를 사용할 수 있습니다:
// export const buildGrafanaApiUrl = (endpoint: string): string => {
//   const baseUrl = GRAFANA_CONFIG.BASE_URL.replace(/\/$/, '')
//   const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
//   return `${baseUrl}${normalizedEndpoint}`
// }