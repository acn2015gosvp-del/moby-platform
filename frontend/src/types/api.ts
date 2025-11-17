// frontend/src/types/api.ts

/**
 * 알림(Alert) 데이터 스키마
 */
export interface Alert {
  id: string;
  sensor_id: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  timestamp: string; // ISO 8601 날짜 문자열
  resolved: boolean;
}

/**
 * 센서(Sensor) 데이터 스키마
 */
export interface SensorData {
  sensor_id: string;
  value: number;
  timestamp: string;
}

/**
 * 새 알림 생성을 위한 요청 스키마 (예시)
 * (백엔드의 alert_request_schema.py에 맞춰야 함)
 */
export interface CreateAlertPayload {
  sensor_id: string;
  value: number;
  threshold: number;
  timestamp: string;
}