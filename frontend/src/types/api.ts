// frontend/src/types/api.ts

/**
 * 알림(Alert) 데이터 스키마
 */
interface Alert { // ⚠️ 'export' 키워드를 제거하고 일반 interface로 정의
  id: string;
  sensor_id: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  timestamp: string; 
  resolved: boolean;
}

/**
 * 센서(Sensor) 데이터 스키마
 */
interface SensorData { // ⚠️ 'export' 키워드를 제거
  sensor_id: string;
  value: number;
  timestamp: string;
}

/**
 * 새 알림 생성을 위한 요청 스키마 
 */
interface CreateAlertPayload { // ⚠️ 'export' 키워드를 제거
  sensor_id: string;
  value: number;
  threshold: number;
  timestamp: string;
}

// ⚠️ 타입만 노출하는 type-only export 블록 추가 (오류 해결)
export type { Alert, SensorData, CreateAlertPayload };