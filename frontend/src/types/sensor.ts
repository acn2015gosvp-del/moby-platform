/**
 * 센서 관련 타입 정의
 */

export interface Sensor {
  device_id: string
  temperature?: number
  humidity?: number
  vibration?: number
  sound?: number
}

export interface SensorStatus {
  status: string
  count: number
  active: number
  inactive: number
}

export interface SensorDataResponse {
  status: string
  sensor_id: string
  timestamp: string
}

/**
 * 설비 요약 정보
 */
export interface DeviceSummary {
  device_id: string
  name: string
  category?: string
  dashboardUID: string
  status: '정상' | '경고' | '긴급' | '오프라인'
  sensorCount?: number | null
  alertCount?: number | null
  operationRate?: number | null
  lastUpdated?: string | null
}

/**
 * 센서 상태 응답 (설비 목록 포함)
 */
export interface SensorStatusResponse {
  status: string
  count: number
  active: number
  inactive: number
  devices: DeviceSummary[]
}
