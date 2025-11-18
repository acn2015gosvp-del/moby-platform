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
   */
  async generateReport(request: ReportRequest): Promise<ReportResponse> {
    const response = await apiClient.post<SuccessResponse<ReportResponse>>(
      '/reports/generate',
      request
    );
    return response.data.data;
  },
};

