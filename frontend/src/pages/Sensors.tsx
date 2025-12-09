/**
 * 센서 페이지
 */

import { useState, useEffect } from 'react'
import { getSensorStatus } from '@/services/sensors/sensorService'
import type { SensorStatus } from '@/types/sensor'
import Loading from '@/components/common/Loading'

function Sensors() {
  const [sensorStatus, setSensorStatus] = useState<SensorStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSensorStatus = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await getSensorStatus()
      if (response.success && response.data) {
        setSensorStatus(response.data)
      }
    } catch (err: unknown) {
      const errObj = err as { response?: { data?: { message?: string } } }
      setError(errObj.response?.data?.message || '센서 상태를 불러오는데 실패했습니다.')
      console.error('Failed to fetch sensor status:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSensorStatus()
    // 30초마다 자동 갱신
    const interval = setInterval(fetchSensorStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ok':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'error':
        return 'bg-red-100 text-red-800 border-red-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'ok':
        return '정상'
      case 'warning':
        return '경고'
      case 'error':
        return '오류'
      default:
        return '알 수 없음'
    }
  }

  if (loading && !sensorStatus) {
    return (
      <div>
        <h1 className="text-3xl font-bold mb-6 text-gray-800">센서 관리</h1>
        <Loading message="센서 상태를 불러오는 중..." />
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">센서 관리</h1>
        <button
          onClick={fetchSensorStatus}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? '갱신 중...' : '새로고침'}
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          {error}
        </div>
      )}

      {sensorStatus && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          {/* 전체 상태 카드 */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-700">전체 상태</h2>
              <span
                className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(
                  sensorStatus.status
                )}`}
              >
                {getStatusText(sensorStatus.status)}
              </span>
            </div>
            <div className="text-3xl font-bold text-gray-800">{sensorStatus.count}</div>
            <p className="text-sm text-gray-500 mt-2">전체 센서 수</p>
          </div>

          {/* 활성 센서 카드 */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-700">활성 센서</h2>
              <span className="w-3 h-3 bg-green-500 rounded-full"></span>
            </div>
            <div className="text-3xl font-bold text-green-600">{sensorStatus.active}</div>
            <p className="text-sm text-gray-500 mt-2">정상 작동 중</p>
          </div>

          {/* 비활성 센서 카드 */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-700">비활성 센서</h2>
              <span className="w-3 h-3 bg-red-500 rounded-full"></span>
            </div>
            <div className="text-3xl font-bold text-red-600">{sensorStatus.inactive}</div>
            <p className="text-sm text-gray-500 mt-2">연결 끊김</p>
          </div>

          {/* 활성 비율 카드 */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-700">활성 비율</h2>
            </div>
            <div className="text-3xl font-bold text-blue-600">
              {sensorStatus.count > 0
                ? Math.round((sensorStatus.active / sensorStatus.count) * 100)
                : 0}
              %
            </div>
            <p className="text-sm text-gray-500 mt-2">정상 작동 비율</p>
          </div>
        </div>
      )}

      {/* 센서 상태 상세 정보 */}
      {sensorStatus && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">센서 상태 상세</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <span className="text-gray-700">전체 센서 수</span>
              <span className="font-semibold text-gray-800">{sensorStatus.count}개</span>
            </div>
            <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
              <span className="text-gray-700">활성 센서</span>
              <span className="font-semibold text-green-600">{sensorStatus.active}개</span>
            </div>
            <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
              <span className="text-gray-700">비활성 센서</span>
              <span className="font-semibold text-red-600">{sensorStatus.inactive}개</span>
            </div>
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-600">
                <strong>참고:</strong> 최근 5분 내 데이터가 있는 센서를 활성으로 간주합니다.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Sensors
