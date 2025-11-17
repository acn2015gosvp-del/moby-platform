// frontend/src/services/alertApi.ts

import apiClient from './apiClient';
import type { Alert, CreateAlertPayload } from '../types/api';

/**
 * 모든 알림 목록을 가져옵니다.
 * GET /alerts
 */
export const getAlerts = async (): Promise<Alert[]> => {
  // .get<Alert[]>(...)는 응답 데이터의 타입을 지정합니다.
  const response = await apiClient.get<Alert[]>('/alerts');
  return response.data;
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