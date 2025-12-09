/**
 * 알림 API 서비스
 */

import apiClient from '../api/client'
import type { Alert, AlertRequest } from '@/types/alert'
import type { SuccessResponse } from '@/types/api'

/**
 * 알림 생성 및 평가
 */
export const createAlert = async (
  data: AlertRequest
): Promise<SuccessResponse<Alert>> => {
  const response = await apiClient.post<SuccessResponse<Alert>>(
    '/alerts/evaluate',
    data
  )
  return response.data
}

/**
 * 최신 알림 목록 조회
 */
export const getLatestAlerts = async (params?: {
  limit?: number
  sensor_id?: string
  level?: 'info' | 'warning' | 'critical'
}): Promise<SuccessResponse<Alert[]>> => {
  const response = await apiClient.get<SuccessResponse<Alert[]>>('/alerts/latest', {
    params,
  })
  return response.data
}

/**
 * 알림 목록 조회 (향후 구현)
 */
export const getAlerts = async (params?: {
  page?: number
  page_size?: number
  status?: string
}): Promise<SuccessResponse<Alert[]>> => {
  const response = await apiClient.get<SuccessResponse<Alert[]>>('/alerts', {
    params,
  })
  return response.data
}

/**
 * 알림 상세 조회 (향후 구현)
 */
export const getAlertById = async (id: string): Promise<SuccessResponse<Alert>> => {
  const response = await apiClient.get<SuccessResponse<Alert>>(`/alerts/${id}`)
  return response.data
}

/**
 * 알림 상태 변경 (향후 구현)
 */
export const updateAlertStatus = async (
  id: string,
  status: 'pending' | 'acknowledged' | 'resolved'
): Promise<SuccessResponse<Alert>> => {
  const response = await apiClient.patch<SuccessResponse<Alert>>(
    `/alerts/${id}/status`,
    { status }
  )
  return response.data
}

/**
 * 알림 삭제 (향후 구현)
 */
export const deleteAlert = async (id: string): Promise<void> => {
  await apiClient.delete(`/alerts/${id}`)
}

/**
 * 전체 알림 삭제
 */
export const deleteAllAlerts = async (): Promise<SuccessResponse<{ deleted_count: number }>> => {
  const response = await apiClient.delete<SuccessResponse<{ deleted_count: number }>>(
    '/alerts/all'
  )
  return response.data
}

