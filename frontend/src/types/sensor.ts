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

