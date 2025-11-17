// frontend/src/services/alertApi.ts

import apiClient from './apiClient';
import type { Alert, CreateAlertPayload } from '../types/api';

// --- 모킹된 데이터 정의 ---
const MOCKED_ALERTS: Alert[] = [
    { id: 'a-001', sensor_id: 'temp-01', level: 'critical', message: 'Engine Overheat Detected', timestamp: '2025-11-17T10:00:00Z', resolved: false },
    { id: 'a-002', sensor_id: 'vib-05', level: 'warning', message: 'Abnormal Vibration (Threshold near)', timestamp: '2025-11-17T10:05:00Z', resolved: false },
    { id: 'a-003', sensor_id: 'temp-01', level: 'info', message: 'Regular system check', timestamp: '2025-11-17T10:10:00Z', resolved: true },
    { id: 'a-004', sensor_id: 'flow-02', level: 'error', message: 'Flow sensor disconnected', timestamp: '2025-11-17T10:15:00Z', resolved: false },
    { id: 'a-005', sensor_id: 'vib-05', level: 'critical', message: 'Catastrophic failure imminent', timestamp: '2025-11-17T10:20:00Z', resolved: false },
    // 페이지네이션 테스트를 위해 충분한 데이터를 추가합니다.
    { id: 'a-006', sensor_id: 'temp-05', level: 'info', message: 'Routine inspection complete', timestamp: '2025-11-17T10:25:00Z', resolved: false },
    { id: 'a-007', sensor_id: 'vib-01', level: 'warning', message: 'Vibration spike detected', timestamp: '2025-11-17T10:30:00Z', resolved: false },
    { id: 'a-008', sensor_id: 'flow-03', level: 'error', message: 'Low pressure warning', timestamp: '2025-11-17T10:35:00Z', resolved: false },
    { id: 'a-009', sensor_id: 'temp-01', level: 'critical', message: 'Emergency shutdown triggered', timestamp: '2025-11-17T10:40:00Z', resolved: false },
    { id: 'a-010', sensor_id: 'vib-05', level: 'info', message: 'Maintenance schedule reminder', timestamp: '2025-11-17T10:45:00Z', resolved: false },
    { id: 'a-011', sensor_id: 'flow-02', level: 'error', message: 'Sensor failure due to corrosion', timestamp: '2025-11-17T10:50:00Z', resolved: false },
    { id: 'a-012', sensor_id: 'temp-05', level: 'warning', message: 'Temperature fluctuation outside norm', timestamp: '2025-11-17T10:55:00Z', resolved: false },
];
// --------------------

/**
 * 모든 알림 목록을 가져옵니다.
 * GET /alerts
 */
export const getAlerts = async (): Promise<Alert[]> => {
    // 실제 API 호출 대신 1초 딜레이 후 모킹 데이터를 반환합니다.
    return new Promise((resolve) => {
        setTimeout(() => {
            // 가장 최신 데이터가 위에 오도록 내림차순 정렬하여 반환합니다.
            const sortedAlerts = [...MOCKED_ALERTS].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
            resolve(sortedAlerts);
        }, 1000);
    });
  // .get<Alert[]>(...)는 응답 데이터의 타입을 지정합니다.
  //const response = await apiClient.get<Alert[]>('/alerts');
  //return response.data;
};

/**
 * ID로 특정 알림을 가져옵니다.
 * GET /alerts/{alert_id}
 */
export const getAlertById = async (alertId: string): Promise<Alert> => {
  const response = await apiClient.get<Alert>(`/alerts/${alertId}`);
  return response.data;
};

/**
 * 새 알림을 생성합니다. (테스트용 또는 수동 생성용)
 * POST /alerts
 */
export const createAlert = async (payload: CreateAlertPayload): Promise<Alert> => {
  const response = await apiClient.post<Alert>('/alerts', payload);
  return response.data;
};