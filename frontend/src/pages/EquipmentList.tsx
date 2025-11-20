/**
 * 설비 목록 페이지
 * 
 * 설비 카드를 표시하고 Grafana 대시보드로 이동하는 기능 제공
 */

import React, { useEffect, useState } from 'react'
import EquipmentCard from '@/components/EquipmentCard'
import type { DeviceSummary, SensorStatusResponse } from '@/types/sensor'
import { getSensorStatus } from '@/services/sensors/sensorService'
import Loading from '@/components/common/Loading'

const EquipmentList: React.FC = () => {
  const [devices, setDevices] = useState<DeviceSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchDevices = async () => {
      try {
        setLoading(true)
        setError(null)

        const response = await getSensorStatus()
        
        if (response.success && response.data) {
          const data = response.data as SensorStatusResponse
          if (data.devices && data.devices.length > 0) {
            setDevices(data.devices)
          } else {
            setDevices([])
          }
        } else {
          setDevices([])
        }
      } catch (err: any) {
        console.error('설비 목록 로딩 실패:', err)
        setError(err.response?.data?.message || '설비 목록을 불러오는데 실패했습니다.')
      } finally {
        setLoading(false)
      }
    }

    fetchDevices()
  }, [])

  if (loading) {
    return (
      <div>
        <h1 className="text-3xl font-bold mb-6 text-gray-800">설비 목록</h1>
        <Loading message="설비 목록을 불러오는 중..." />
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <h1 className="text-3xl font-bold mb-6 text-gray-800">설비 목록</h1>
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          {error}
        </div>
        <button
          onClick={() => window.location.reload()}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          다시 시도
        </button>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">설비 목록</h1>
        <p className="text-gray-600">설비 카드를 클릭하여 Grafana 대시보드를 확인하세요</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {devices.map((device) => (
          <EquipmentCard
            key={device.device_id}
            device={device}
          />
        ))}
      </div>

      {devices.length === 0 && (
        <div className="text-center py-20 bg-white rounded-lg shadow">
          <div className="text-gray-400 text-6xl mb-4">🏭</div>
          <p className="text-gray-500 text-lg mb-2">등록된 설비가 없습니다.</p>
          <p className="text-gray-400 text-sm">백엔드 API에서 설비 목록 데이터를 확인해주세요.</p>
        </div>
      )}
    </div>
  )
}

export default EquipmentList

