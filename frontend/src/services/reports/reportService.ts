import apiClient from '../api/client';
import type { SuccessResponse } from '@/types/api';

export interface ReportRequest {
  period_start: string;
  period_end: string;
  equipment: string;
  sensor_ids?: string[];
  include_mlp_anomalies?: boolean;
  include_if_anomalies?: boolean;
}

export interface ReportResponse {
  report_id: string;
  report_content: string;
  metadata: {
    period_start: string;
    period_end: string;
    equipment: string;
    generated_at: string;
  };
  generated_at: string;
}

export const reportService = {
  /**
   * 보고서 생성
   * LLM API 호출이 포함되어 있어 더 긴 타임아웃이 필요합니다.
   */
  async generateReport(request: ReportRequest): Promise<ReportResponse> {
    const response = await apiClient.post<SuccessResponse<ReportResponse>>(
      '/reports/generate',
      request,
      {
        timeout: 120000, // 120초 (보고서 생성은 LLM API 호출로 인해 시간이 오래 걸릴 수 있음)
      }
    );
    return response.data.data;
  },
};

