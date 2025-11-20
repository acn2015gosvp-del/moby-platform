import { useState } from 'react';
import { reportService, type ReportRequest } from '@/services/reports/reportService';
import Button from '@/components/common/Button';
import Loading from '@/components/common/Loading';

export default function Reports() {
  const [loading, setLoading] = useState(false);
  const [reportContent, setReportContent] = useState<string | null>(null);
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
        // 이미 공백이 있으면 그대로 사용하고 :00 추가
        if (dateTimeStr.includes(' ')) {
          return dateTimeStr.includes(':00') ? dateTimeStr : dateTimeStr + ':00';
        }
        // T를 공백으로 바꾸고 :00 추가
        return dateTimeStr.replace('T', ' ') + ':00';
      };

      const request: ReportRequest = {
        ...formData,
        period_start: formatDateTime(formData.period_start),
        period_end: formatDateTime(formData.period_end),
      };

      const report = await reportService.generateReport(request);
      setReportContent(report.report_content);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || '보고서 생성 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!reportContent) return;

    const blob = new Blob([reportContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `MOBY_Report_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
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
            <Button onClick={handleDownload} variant="outline">
              다운로드
            </Button>
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

