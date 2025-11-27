import { useState } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import { reportService, type ReportRequest, type ReportResponse } from '@/services/reports/reportService';
import { useDeviceContext } from '@/context/DeviceContext';
import Button from '@/components/common/Button';
import Loading from '@/components/common/Loading';
import { downloadReportAsPDF } from '@/utils/pdfGenerator';

export default function Reports() {
  const { deviceId } = useParams<{ deviceId?: string }>();
  const { selectedDevice } = useDeviceContext();

  // deviceId가 없으면 설비 목록으로 리다이렉트
  if (!deviceId) {
    return <Navigate to="/devices" replace />;
  }
  const [loading, setLoading] = useState(false);
  const [reportContent, setReportContent] = useState<string | null>(null);
  const [reportData, setReportData] = useState<ReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<ReportRequest>({
    // datetime-local 입력은 YYYY-MM-DDTHH:MM 형식을 사용
    period_start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16),
    period_end: new Date().toISOString().slice(0, 16),
    equipment: 'Conveyor A-01',
    include_mlp_anomalies: true,
    include_if_anomalies: true,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setReportContent(null);

    try {
      // 날짜 형식 변환 (YYYY-MM-DDTHH:MM -> YYYY-MM-DD HH:MM:SS)
      // datetime-local 입력은 "2025-11-11T11:00" 형식으로 반환되므로 변환 필요
      const formatDateTime = (dateTimeStr: string): string => {
        if (!dateTimeStr) {
          throw new Error('날짜가 입력되지 않았습니다.');
        }
        
        // 이미 공백이 있으면 (YYYY-MM-DD HH:MM 형식)
        if (dateTimeStr.includes(' ')) {
          // 초가 없으면 :00 추가
          const parts = dateTimeStr.split(' ');
          if (parts.length === 2) {
            const timePart = parts[1];
            // HH:MM 형식이면 :00 추가
            if (timePart.match(/^\d{2}:\d{2}$/)) {
              return `${dateTimeStr}:00`;
            }
            // HH:MM:SS 형식이면 그대로 반환
            if (timePart.match(/^\d{2}:\d{2}:\d{2}$/)) {
              return dateTimeStr;
            }
          }
          return dateTimeStr;
        }
        
        // T가 있으면 (YYYY-MM-DDTHH:MM 형식)
        if (dateTimeStr.includes('T')) {
          // T를 공백으로 바꾸고
          let result = dateTimeStr.replace('T', ' ');
          // 초가 없으면 :00 추가
          if (result.match(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/)) {
            result = result + ':00';
          }
          return result;
        }
        
        // 그 외의 경우는 그대로 반환
        return dateTimeStr;
      };

      const formattedStart = formatDateTime(formData.period_start);
      const formattedEnd = formatDateTime(formData.period_end);
      
      // 날짜 형식 검증
      const dateFormatRegex = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/;
      if (!dateFormatRegex.test(formattedStart)) {
        throw new Error(`시작 날짜 형식이 올바르지 않습니다: ${formattedStart} (예상 형식: YYYY-MM-DD HH:MM:SS)`);
      }
      if (!dateFormatRegex.test(formattedEnd)) {
        throw new Error(`종료 날짜 형식이 올바르지 않습니다: ${formattedEnd} (예상 형식: YYYY-MM-DD HH:MM:SS)`);
      }
      
      // 날짜 비교 검증
      const startDate = new Date(formattedStart);
      const endDate = new Date(formattedEnd);
      if (isNaN(startDate.getTime())) {
        throw new Error(`시작 날짜를 파싱할 수 없습니다: ${formattedStart}`);
      }
      if (isNaN(endDate.getTime())) {
        throw new Error(`종료 날짜를 파싱할 수 없습니다: ${formattedEnd}`);
      }
      if (endDate <= startDate) {
        throw new Error(`종료 시간이 시작 시간보다 이후여야 합니다. (시작: ${formattedStart}, 종료: ${formattedEnd})`);
      }
      
      console.log('[Reports] 날짜 변환 결과:', {
        원본_start: formData.period_start,
        변환_start: formattedStart,
        원본_end: formData.period_end,
        변환_end: formattedEnd,
        검증_통과: true,
      });

      const request: ReportRequest = {
        ...formData,
        period_start: formattedStart,
        period_end: formattedEnd,
        // equipment는 선택된 디바이스 이름을 사용하거나 기본값 사용
        equipment: selectedDevice?.name || formData.equipment || deviceId || 'Unknown Device',
      };

      console.log('[Reports] 보고서 생성 요청 (전체):', JSON.stringify(request, null, 2));

      const report = await reportService.generateReport(request);
      setReportContent(report.report_content);
      setReportData(report);
      
      // 보고서 생성 성공 시 자동으로 PDF 다운로드
      try {
        const filename = `MOBY_Report_${report.report_id || new Date().toISOString().slice(0, 10)}`;
        await downloadReportAsPDF(
          report.report_content,
          filename,
          {
            period_start: report.metadata?.period_start,
            period_end: report.metadata?.period_end,
            equipment: report.metadata?.equipment,
            generated_at: report.generated_at
          }
        );
      } catch (pdfError: any) {
        // PDF 다운로드 실패는 에러로 표시하지 않고 콘솔에만 로그
        console.warn('PDF 자동 다운로드 실패:', pdfError);
        // 사용자에게는 보고서는 생성되었지만 PDF 다운로드에 실패했다는 메시지를 표시하지 않음
        // (수동으로 다운로드 버튼을 클릭할 수 있으므로)
      }
    } catch (err: any) {
      // 더 자세한 에러 메시지 추출
      let errorMessage = '보고서 생성 중 오류가 발생했습니다.';
      
      console.error('[Reports] 보고서 생성 오류 상세:', {
        message: err.message,
        response: err.response,
        responseData: err.response?.data,
        responseStatus: err.response?.status,
        request: err.config,
      });
      
      if (err.response?.data) {
        const errorData = err.response.data;
        console.log('[Reports] 에러 응답 데이터:', errorData);
        
        // ErrorResponse 형식인 경우
        if (errorData.error?.message) {
          errorMessage = errorData.error.message;
        } else if (errorData.detail) {
          // FastAPI의 detail 필드
          errorMessage = typeof errorData.detail === 'string' 
            ? errorData.detail 
            : JSON.stringify(errorData.detail);
        } else if (errorData.message) {
          errorMessage = errorData.message;
        } else if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else {
          // 전체 에러 객체를 문자열로 변환
          errorMessage = `서버 오류: ${JSON.stringify(errorData, null, 2)}`;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      console.error('[Reports] 최종 에러 메시지:', errorMessage);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async (e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    
    console.log('[Reports] PDF 다운로드 버튼 클릭됨');
    console.log('[Reports] reportContent 존재 여부:', !!reportContent);
    console.log('[Reports] reportData 존재 여부:', !!reportData);
    
    if (!reportContent || !reportData) {
      console.warn('[Reports] reportContent 또는 reportData가 없어서 다운로드 불가');
      setError('다운로드할 보고서 데이터가 없습니다.');
      return;
    }

    try {
      const filename = `MOBY_Report_${reportData.report_id || new Date().toISOString().slice(0, 10)}`;
      console.log('[Reports] PDF 다운로드 시작:', filename);
      
      // 에러 상태 초기화
      setError(null);
      
      await downloadReportAsPDF(
        reportContent,
        filename,
        {
          period_start: reportData.metadata.period_start,
          period_end: reportData.metadata.period_end,
          equipment: reportData.metadata.equipment,
          generated_at: reportData.generated_at
        }
      );
      console.log('[Reports] PDF 다운로드 완료');
    } catch (error: any) {
      console.error('[Reports] PDF 다운로드 오류:', error);
      const errorMessage = error?.message || error?.toString() || 'PDF 다운로드 중 오류가 발생했습니다.';
      setError(errorMessage);
      alert(`PDF 다운로드 실패: ${errorMessage}`);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">보고서 생성</h1>
        <p className="mt-2 text-gray-600">LLM 기반 주간/일일 보고서를 자동 생성합니다.</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                보고 기간 시작
              </label>
              <input
                type="datetime-local"
                value={formData.period_start}
                onChange={(e) => setFormData({ ...formData, period_start: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                보고 기간 종료
              </label>
              <input
                type="datetime-local"
                value={formData.period_end}
                onChange={(e) => setFormData({ ...formData, period_end: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              설비명
            </label>
            <input
              type="text"
              value={formData.equipment}
              onChange={(e) => setFormData({ ...formData, equipment: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="예: Conveyor A-01"
              required
            />
          </div>

          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.include_mlp_anomalies}
                onChange={(e) => setFormData({ ...formData, include_mlp_anomalies: e.target.checked })}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">MLP 이상 탐지 포함</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.include_if_anomalies}
                onChange={(e) => setFormData({ ...formData, include_if_anomalies: e.target.checked })}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">Isolation Forest 이상 탐지 포함</span>
            </label>
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="w-full md:w-auto"
          >
            {loading ? '생성 중...' : '보고서 생성'}
          </Button>
        </form>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {loading && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
          <div className="flex items-center justify-center space-x-4">
            <Loading />
            <div className="text-left">
              <p className="text-blue-800 font-medium">보고서 생성 중...</p>
              <p className="text-blue-600 text-sm mt-1">
                데이터 수집 및 LLM 보고서 생성 중... 예상 시간: 30-90초
              </p>
              <p className="text-blue-500 text-xs mt-1">
                최적화된 설정으로 더 빠르게 생성됩니다. (타임아웃: 3분)
              </p>
            </div>
          </div>
        </div>
      )}

      {reportContent && (
        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200 px-6 py-4 flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">생성된 보고서</h2>
            <div className="flex gap-2">
              <Button 
                type="button"
                onClick={handleDownloadPDF} 
                variant="danger" 
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                📄 PDF 다운로드
              </Button>
            </div>
          </div>
          <div className="p-6">
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap font-sans text-sm bg-gray-50 p-4 rounded border overflow-auto max-h-[600px]">
                {reportContent}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

