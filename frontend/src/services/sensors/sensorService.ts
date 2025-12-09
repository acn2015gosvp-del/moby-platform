/**
 * 센서 API 서비스
 */

import apiClient from '../api/client'
import type { Sensor, SensorStatus, SensorDataResponse, SensorStatusResponse } from '@/types/sensor'
import type { SuccessResponse } from '@/types/api'

/**
 * 센서 데이터 수신
 */
export const postSensorData = async (
  data: Sensor
): Promise<SuccessResponse<SensorDataResponse>> => {
  const response = await apiClient.post<SuccessResponse<SensorDataResponse>>(
    '/sensors/data',
    data
  )
  return response.data
}

/**
 * 센서 상태 조회
 */
export const getSensorStatus = async (): Promise<SuccessResponse<SensorStatus | SensorStatusResponse>> => {
  const response = await apiClient.get<SuccessResponse<SensorStatus | SensorStatusResponse>>(
    '/sensors/status'
  )
  
  // 백엔드에서 devices 필드가 없는 경우를 대비한 임시 목 데이터
  const data = response.data
  if (data.success && data.data) {
    const statusData = data.data as unknown as { devices?: Array<{ device_id: string; [key: string]: unknown }>; [key: string]: unknown }
    if (!statusData.devices || statusData.devices.length === 0) {
      // 임시 목 데이터 (백엔드 수정 전)
      return {
        ...data,
        data: {
          ...statusData,
          devices: [
            {
              device_id: 'conveyor-belt-1',
              name: '컨베이어 벨트 #1',
              category: '운송 시스템',
              dashboardUID: 'conveyor-dashboard',
              status: '정상' as const,
              sensorCount: 18,
              alertCount: 0,
              operationRate: 99.9,
            },
            {
              device_id: 'cnc-machine-a3',
              name: 'CNC 밀링 머신 #A3',
              category: '가공 장비',
              dashboardUID: 'cnc-dashboard',
              status: '경고' as const,
              sensorCount: 24,
              alertCount: 3,
              operationRate: 97.2,
            },
            {
              device_id: 'robot-arm-r7',
              name: '산업용 로봇 팔 #R7',
              category: '자동화 설비',
              dashboardUID: 'robot-dashboard',
              status: '긴급' as const,
              sensorCount: 32,
              alertCount: 8,
              operationRate: 85.4,
            },
          ],
        } as SensorStatusResponse,
      }
    }
  }
  
  return response.data
}

/**
 * 센서 목록 조회 (향후 구현)
 */
export const getSensors = async (): Promise<SuccessResponse<Sensor[]>> => {
  const response = await apiClient.get<SuccessResponse<Sensor[]>>('/sensors')
  return response.data
}

/**
 * 센서 상세 조회 (향후 구현)
 */
export const getSensorById = async (id: string): Promise<SuccessResponse<Sensor>> => {
  const response = await apiClient.get<SuccessResponse<Sensor>>(`/sensors/${id}`)
  return response.data
}

