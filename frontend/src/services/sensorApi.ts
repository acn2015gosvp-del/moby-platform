import apiClient from './apiClient';
import type { SensorData } from '../types/api';

/**
 * 센서 데이터를 가져옵니다. (엔드포인트 예시)
 * GET /sensors/data
 */
export const getSensorData = async (sensorId: string): Promise<SensorData[]> => {
  const response = await apiClient.get<SensorData[]>(`/sensors/data`, {
    params: {
      sensor_id: sensorId,
      // ... (필요한 경우 다른 쿼리 파라미터 추가)
    },
  });
  return response.data;
};

/**
 * 새 센서 데이터를 전송합니다. (Edge 장치에서 호출)
 * POST /sensors/data
 */
export const postSensorData = async (payload: SensorData): Promise<SensorData> => {
  const response = await apiClient.post<SensorData>('/sensors/data', payload);
  return response.data;
};