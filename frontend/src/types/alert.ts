/**
 * 알림 관련 타입 정의
 */

export type AlertLevel = 'info' | 'warning' | 'critical'
export type AlertStatus = 'pending' | 'acknowledged' | 'resolved'

export interface Alert {
  id: string
  level: AlertLevel
  message: string
  llm_summary?: string
  sensor_id: string
  source: string
  ts: string
  details: AlertDetails
}

export interface AlertDetails {
  vector: number[]
  norm: number
  threshold?: number
  warning_threshold?: number
  critical_threshold?: number
  severity: string
  meta?: Record<string, any>
}

export interface AlertRequest {
  vector: number[]
  threshold?: number
  warning_threshold?: number
  critical_threshold?: number
  sensor_id?: string
  enable_llm_summary?: boolean
  message?: string
  meta?: Record<string, any>
}

