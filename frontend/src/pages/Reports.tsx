import { useState, useRef } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import { reportService, type ReportRequest, type ReportResponse } from '@/services/reports/reportService';
import { useDeviceContext } from '@/context/DeviceContext';
import Button from '@/components/common/Button';
import Loading from '@/components/common/Loading';
import { downloadReportAsPDF } from '@/utils/pdfGenerator';

export default function Reports() {
  const { deviceId } = useParams<{ deviceId?: string }>();
  const { selectedDevice } = useDeviceContext();
  const formRef = useRef<HTMLFormElement | null>(null);
  const [loading, setLoading] = useState(false);
  const [reportContent, setReportContent] = useState<string | null>(null);
  const [reportData, setReportData] = useState<ReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  // 날짜와 시간을 분리하여 관리 (24시간 형식)
  const getDefaultDateTime = () => {
    const date = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return {
      date: date.toISOString().slice(0, 10), // YYYY-MM-DD
      hours: hours, // HH (00-23)
      minutes: minutes, // MM (00-59)
    };
  };
  
  const getCurrentDateTime = () => {
    const date = new Date();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return {
      date: date.toISOString().slice(0, 10), // YYYY-MM-DD
      hours: hours, // HH (00-23)
      minutes: minutes, // MM (00-59)
    };
  };

  const defaultDT = getDefaultDateTime();
  const currentDT = getCurrentDateTime();

  const [periodStartDate, setPeriodStartDate] = useState(defaultDT.date);
  const [periodStartHours, setPeriodStartHours] = useState(defaultDT.hours);
  const [periodStartMinutes, setPeriodStartMinutes] = useState(defaultDT.minutes);
  const [periodEndDate, setPeriodEndDate] = useState(currentDT.date);
  const [periodEndHours, setPeriodEndHours] = useState(currentDT.hours);
  const [periodEndMinutes, setPeriodEndMinutes] = useState(currentDT.minutes);
  
  const [formData, setFormData] = useState<ReportRequest>({
    period_start: '',
    period_end: '',
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
      // 날짜와 시간을 결합하여 UTC로 변환 (24시간 형식)
      const formatDateTime = (dateStr: string, hoursStr: string, minutesStr: string): string => {
        if (!dateStr || !hoursStr || !minutesStr) {
          throw new Error('날짜, 시, 분이 모두 입력되어야 합니다.');
        }
        
        // 시간 유효성 검증 (00-23, 00-59)
        const hours = parseInt(hoursStr, 10);
        const minutes = parseInt(minutesStr, 10);
        if (isNaN(hours) || hours < 0 || hours > 23) {
          throw new Error(`시간이 올바르지 않습니다: ${hoursStr} (00-23 범위)`);
        }
        if (isNaN(minutes) || minutes < 0 || minutes > 59) {
          throw new Error(`분이 올바르지 않습니다: ${minutesStr} (00-59 범위)`);
        }
        
        // 날짜와 시간을 결합 (YYYY-MM-DD HH:MM 형식, 로컬 시간, 24시간 형식)
        const timeStr = `${hoursStr}:${minutesStr}`;
        const localDateTimeStr = `${dateStr} ${timeStr}`;
        const localDate = new Date(localDateTimeStr);
        
        // 유효한 날짜인지 확인
        if (isNaN(localDate.getTime())) {
          throw new Error(`날짜를 파싱할 수 없습니다: ${localDateTimeStr}`);
        }
        
        // UTC로 변환하여 YYYY-MM-DD HH:MM:SS 형식으로 반환
        const utcYear = localDate.getUTCFullYear();
        const utcMonth = String(localDate.getUTCMonth() + 1).padStart(2, '0');
        const utcDay = String(localDate.getUTCDate()).padStart(2, '0');
        const utcHours = String(localDate.getUTCHours()).padStart(2, '0');
        const utcMinutes = String(localDate.getUTCMinutes()).padStart(2, '0');
        const utcSeconds = String(localDate.getUTCSeconds()).padStart(2, '0');
        
        const utcString = `${utcYear}-${utcMonth}-${utcDay} ${utcHours}:${utcMinutes}:${utcSeconds}`;
        
        console.log(`[Reports] 시간 변환: ${localDateTimeStr} (로컬, 24시간) -> ${utcString} (UTC)`);
        console.log(`[Reports] 로컬 시간: ${localDate.toLocaleString()}, UTC 시간: ${localDate.toUTCString()}`);
        
        return utcString;
      };

      const formattedStart = formatDateTime(periodStartDate, periodStartHours, periodStartMinutes);
      const formattedEnd = formatDateTime(periodEndDate, periodEndHours, periodEndMinutes);
      
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

      // equipment 값 결정: 설비명 또는 ID 사용
      // 백엔드에서는 설비명을 받지만, 실제로는 "Conveyor A-01" 같은 영문 설비명을 선호
      // 한글 설비명("컨베이어 벨트 #1")도 허용하지만, 가능하면 영문 설비명 사용
      let equipmentValue = formData.equipment || 'Conveyor A-01';
      
      // selectedDevice가 있으면 name 사용 (한글일 수 있음)
      if (selectedDevice?.name) {
        equipmentValue = selectedDevice.name;
      }
      
      // deviceId가 있으면 그것도 고려 (하지만 우선순위는 낮음)
      if (!equipmentValue || equipmentValue === 'Unknown Device') {
        equipmentValue = deviceId || 'Conveyor A-01';
      }

      const request: ReportRequest = {
        period_start: formattedStart,
        period_end: formattedEnd,
        equipment: equipmentValue,
        include_mlp_anomalies: formData.include_mlp_anomalies,
        include_if_anomalies: formData.include_if_anomalies,
        sensor_ids: formData.sensor_ids,
      };

      console.log('[Reports] 보고서 생성 요청 (전체):', JSON.stringify(request, null, 2));
      console.log('[Reports] equipment 값:', equipmentValue, 'selectedDevice:', selectedDevice);
      console.log('[Reports] 입력된 날짜/시간 (24시간 형식):', {
        start: { date: periodStartDate, hours: periodStartHours, minutes: periodStartMinutes },
        end: { date: periodEndDate, hours: periodEndHours, minutes: periodEndMinutes },
      });
      console.log('[Reports] 입력된 날짜/시간:', {
        start: { date: periodStartDate, hours: periodStartHours, minutes: periodStartMinutes },
        end: { date: periodEndDate, hours: periodEndHours, minutes: periodEndMinutes },
      });

      const report = await reportService.generateReport(request);
      
      // 응답 검증
      if (!report) {
        throw new Error('보고서 응답이 없습니다.');
      }
      
      if (!report.report_content) {
        console.error('보고서 응답 구조:', report);
        throw new Error('보고서 내용이 없습니다.');
      }
      
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
      } catch (pdfError: unknown) {
        // PDF 다운로드 실패는 에러로 표시하지 않고 콘솔에만 로그
        console.warn('PDF 자동 다운로드 실패:', pdfError);
        // 사용자에게는 보고서는 생성되었지만 PDF 다운로드에 실패했다는 메시지를 표시하지 않음
        // (수동으로 다운로드 버튼을 클릭할 수 있으므로)
      }
    } catch (err: unknown) {
      // 더 자세한 에러 메시지 추출
      let errorMessage = '보고서 생성 중 오류가 발생했습니다.';
      
      const errObj = err as { message?: string; response?: { data?: unknown; status?: number }; config?: unknown }
      console.error('[Reports] 보고서 생성 오류 상세:', {
        message: errObj.message,
        response: errObj.response,
        responseData: errObj.response?.data,
        responseStatus: errObj.response?.status,
        request: errObj.config,
      });
      
      // 에러 응답 데이터 상세 로깅
      if (errObj.response) {
        console.error('[Reports] HTTP 응답 상태:', errObj.response.status);
        console.error('[Reports] HTTP 응답 헤더:', errObj.response.headers);
        console.error('[Reports] HTTP 응답 데이터 (원본):', errObj.response.data);
        console.error('[Reports] HTTP 응답 데이터 (타입):', typeof errObj.response.data);
        console.error('[Reports] HTTP 응답 데이터 (JSON):', JSON.stringify(errObj.response.data, null, 2));
      }
      
      if (errObj.response?.data) {
        const errorData = errObj.response.data;
        console.log('[Reports] 에러 응답 데이터 (파싱):', errorData);
        
        // ErrorResponse 형식인 경우 (success: false, error: {code, message})
        if (errorData.error && typeof errorData.error === 'object') {
          if (errorData.error.message) {
            errorMessage = errorData.error.message;
            if (errorData.error.code) {
              errorMessage = `[${errorData.error.code}] ${errorMessage}`;
            }
          }
        } 
        // FastAPI의 HTTPException detail 필드
        else if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string' 
            ? errorData.detail 
            : JSON.stringify(errorData.detail, null, 2);
        } 
        // 일반적인 message 필드
        else if (errorData.message) {
          errorMessage = errorData.message;
        } 
        // 문자열 응답
        else if (typeof errorData === 'string') {
          errorMessage = errorData;
        } 
        // 객체 응답 (전체 출력)
        else {
          errorMessage = `서버 오류 (${err.response.status}): ${JSON.stringify(errorData, null, 2)}`;
        }
      } 
      // 응답이 없지만 상태 코드가 있는 경우
      else if (errObj.response?.status) {
        errorMessage = `서버 오류 (${errObj.response.status}): ${errObj.message || '알 수 없는 오류'}`;
      }
      // 네트워크 오류
      else if ((errObj as { request?: unknown }).request) {
        errorMessage = '서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인하세요.';
      }
      // 기타 오류
      else if (errObj.message) {
        errorMessage = errObj.message;
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
    } catch (error: unknown) {
      console.error('[Reports] PDF 다운로드 오류:', error);
      const errorObj = error instanceof Error ? error : { message: String(error) }
      const errorMessage = errorObj.message || 'PDF 다운로드 중 오류가 발생했습니다.';
      setError(errorMessage);
      alert(`PDF 다운로드 실패: ${errorMessage}`);
    }
  };

  // deviceId가 없으면 설비 목록으로 리다이렉트
  if (!deviceId) {
    return <Navigate to="/devices" replace />;
  }

  return (
    <div className="min-h-screen bg-background-main p-6">
      <div className="max-w-7xl mx-auto space-y-6">
      {/* 리포트 생성 폼 */}
      <div className="bg-background-surface border border-border rounded-xl p-6 mb-4">
        <form ref={formRef} onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">
                보고 기간 시작
              </label>
              <div className="flex gap-2">
                <input
                  type="date"
                  value={periodStartDate}
                  onChange={(e) => setPeriodStartDate(e.target.value)}
                  className="flex-1 px-3 py-2 border border-border rounded-md bg-background-main text-text-primary focus:outline-none focus:ring-2 focus:ring-primary/30"
                  required
                />
                <div className="flex items-center gap-1 flex-1">
                  <input
                    type="number"
                    min="0"
                    max="23"
                    value={periodStartHours}
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val === '' || (parseInt(val, 10) >= 0 && parseInt(val, 10) <= 23)) {
                        setPeriodStartHours(val.padStart(2, '0'));
                      }
                    }}
                    onBlur={(e) => {
                      const val = e.target.value;
                      if (val === '') {
                        setPeriodStartHours('00');
                      } else {
                        const num = parseInt(val, 10);
                        if (num < 0) setPeriodStartHours('00');
                        else if (num > 23) setPeriodStartHours('23');
                        else setPeriodStartHours(String(num).padStart(2, '0'));
                      }
                    }}
                    className="w-16 px-2 py-2 border border-border rounded-md bg-background-main text-text-primary text-center focus:outline-none focus:ring-2 focus:ring-primary/30"
                    placeholder="00"
                    required
                  />
                  <span className="text-text-secondary">:</span>
                  <input
                    type="number"
                    min="0"
                    max="59"
                    value={periodStartMinutes}
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val === '' || (parseInt(val, 10) >= 0 && parseInt(val, 10) <= 59)) {
                        setPeriodStartMinutes(val.padStart(2, '0'));
                      }
                    }}
                    onBlur={(e) => {
                      const val = e.target.value;
                      if (val === '') {
                        setPeriodStartMinutes('00');
                      } else {
                        const num = parseInt(val, 10);
                        if (num < 0) setPeriodStartMinutes('00');
                        else if (num > 59) setPeriodStartMinutes('59');
                        else setPeriodStartMinutes(String(num).padStart(2, '0'));
                      }
                    }}
                    className="w-16 px-2 py-2 border border-border rounded-md bg-background-main text-text-primary text-center focus:outline-none focus:ring-2 focus:ring-primary/30"
                    placeholder="00"
                    required
                  />
                </div>
              </div>
              <p className="mt-1 text-xs text-text-tertiary">24시간 형식 (00:00 ~ 23:59)</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">
                보고 기간 종료
              </label>
              <div className="flex gap-2 items-center">
                <input
                  type="date"
                  value={periodEndDate}
                  onChange={(e) => setPeriodEndDate(e.target.value)}
                  className="flex-1 px-3 py-2 border border-border rounded-md bg-background-main text-text-primary focus:outline-none focus:ring-2 focus:ring-primary/30"
                  required
                />
                <div className="flex items-center gap-1 flex-1">
                  <input
                    type="number"
                    min="0"
                    max="23"
                    value={periodEndHours}
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val === '' || (parseInt(val, 10) >= 0 && parseInt(val, 10) <= 23)) {
                        setPeriodEndHours(val.padStart(2, '0'));
                      }
                    }}
                    onBlur={(e) => {
                      const val = e.target.value;
                      if (val === '') {
                        setPeriodEndHours('00');
                      } else {
                        const num = parseInt(val, 10);
                        if (num < 0) setPeriodEndHours('00');
                        else if (num > 23) setPeriodEndHours('23');
                        else setPeriodEndHours(String(num).padStart(2, '0'));
                      }
                    }}
                    className="w-16 px-2 py-2 border border-border rounded-md bg-background-main text-text-primary text-center focus:outline-none focus:ring-2 focus:ring-primary/30"
                    placeholder="00"
                    required
                  />
                  <span className="text-text-secondary">:</span>
                  <input
                    type="number"
                    min="0"
                    max="59"
                    value={periodEndMinutes}
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val === '' || (parseInt(val, 10) >= 0 && parseInt(val, 10) <= 59)) {
                        setPeriodEndMinutes(val.padStart(2, '0'));
                      }
                    }}
                    onBlur={(e) => {
                      const val = e.target.value;
                      if (val === '') {
                        setPeriodEndMinutes('00');
                      } else {
                        const num = parseInt(val, 10);
                        if (num < 0) setPeriodEndMinutes('00');
                        else if (num > 59) setPeriodEndMinutes('59');
                        else setPeriodEndMinutes(String(num).padStart(2, '0'));
                      }
                    }}
                    className="w-16 px-2 py-2 border border-border rounded-md bg-background-main text-text-primary text-center focus:outline-none focus:ring-2 focus:ring-primary/30"
                    placeholder="00"
                    required
                  />
                </div>
              </div>
              <p className="mt-1 text-xs text-text-tertiary">24시간 형식 (00:00 ~ 23:59)</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              설비명
            </label>
            <input
              type="text"
              value={formData.equipment}
              onChange={(e) => setFormData({ ...formData, equipment: e.target.value })}
              className="w-full px-3 py-2 border border-border rounded-md bg-background-main text-text-primary placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-primary/30"
              placeholder="예: Conveyor A-01"
              required
            />
          </div>

          <div className="flex flex-col md:flex-row md:items-center md:space-x-4 space-y-2 md:space-y-0">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.include_mlp_anomalies}
                onChange={(e) => setFormData({ ...formData, include_mlp_anomalies: e.target.checked })}
                className="mr-2 rounded border-border text-primary focus:ring-primary/40 bg-background-main"
              />
              <span className="text-sm text-text-secondary">MLP 이상 탐지 포함</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.include_if_anomalies}
                onChange={(e) => setFormData({ ...formData, include_if_anomalies: e.target.checked })}
                className="mr-2 rounded border-border text-primary focus:ring-primary/40 bg-background-main"
              />
              <span className="text-sm text-text-secondary">Isolation Forest 이상 탐지 포함</span>
            </label>
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="w-full md:w-auto bg-primary text-background-main font-bold hover:brightness-110"
          >
            {loading ? '생성 중...' : '보고서 생성'}
          </Button>
        </form>
      </div>

      {error && (
        <div className="bg-danger/10 border border-danger rounded-xl p-4 mb-4">
          <p className="text-danger">{error}</p>
        </div>
      )}

      {loading && (
        <div className="bg-background-surface border border-border rounded-xl p-6 mb-4">
          <div className="flex items-center justify-center space-x-4">
            <Loading />
            <div className="text-left">
              <p className="text-text-primary font-medium">보고서 생성 중...</p>
              <p className="text-text-secondary text-sm mt-1">
                데이터 수집 및 LLM 보고서 생성 중... 예상 시간: 30-90초
              </p>
              <p className="text-text-secondary text-xs mt-1">
                최적화된 설정으로 더 빠르게 생성됩니다. (타임아웃: 3분)
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 리포트 목록 / 카드 */}
      {reportData ? (
        <div className="bg-background-surface border border-border rounded-xl p-5 mb-4 flex items-center justify-between hover:border-primary hover:bg-white/5 transition-colors">
          <div className="flex items-center gap-4">
            <div className="text-2xl">📄</div>
            <div>
              <h2 className="text-lg font-medium text-text-primary">
                생성된 주간 리포트
              </h2>
              <p className="text-sm text-text-secondary font-mono">
                {reportData.generated_at || reportData.metadata?.period_start}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleDownloadPDF}
            className="text-primary text-sm font-medium hover:underline"
          >
            다운로드
          </button>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-16 text-text-secondary">
          <div className="text-5xl mb-4">📄</div>
          <p className="text-lg">생성된 리포트가 없습니다.</p>
        </div>
      )}

      {reportContent && (
        <div className="bg-background-surface border border-border rounded-xl">
          <div className="border-b border-border px-6 py-4 flex justify-between items-center">
            <h2 className="text-xl font-semibold text-text-primary">생성된 보고서 내용</h2>
            <div className="flex gap-2">
              <Button
                type="button"
                onClick={handleDownloadPDF}
                variant="danger"
                className="bg-danger hover:brightness-110 text-white"
              >
                📄 PDF 다운로드
              </Button>
            </div>
          </div>
          <div className="p-6">
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap font-sans text-sm bg-background-main p-4 rounded border border-border overflow-auto max-h-[600px] text-text-primary">
                {reportContent}
              </pre>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}

