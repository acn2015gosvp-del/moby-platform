/**
 * 센서 API 서비스
 */

import apiClient from '../api/client'
import type { Sensor, SensorStatus, SensorDataResponse } from '@/types/sensor'
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
export const getSensorStatus = async (): Promise<SuccessResponse<SensorStatus>> => {
  const response = await apiClient.get<SuccessResponse<SensorStatus>>(
    '/sensors/status'
  )
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

