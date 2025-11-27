/**
 * 설비 선택 전역 상태 관리 Context
 * 
 * 현재 선택된 설비를 전역으로 관리하고 URL과 동기화합니다.
 */

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import type { DeviceSummary } from '@/types/sensor'
import { getSensorStatus } from '@/services/sensors/sensorService'
import type { SensorStatusResponse } from '@/types/sensor'
import type { AddEquipmentFormData } from '@/components/AddEquipmentModal'

interface DeviceContextType {
  devices: DeviceSummary[]
  selectedDevice: DeviceSummary | null
  selectedDeviceId: string | null
  loading: boolean
  error: string | null
  setSelectedDeviceId: (deviceId: string | null) => void
  refreshDevices: () => Promise<void>
  addDevice: (formData: AddEquipmentFormData) => DeviceSummary
  removeDevice: (deviceId: string) => void
}

const DeviceContext = createContext<DeviceContextType | undefined>(undefined)

interface DeviceProviderProps {
  children: ReactNode
}

export function DeviceProvider({ children }: DeviceProviderProps) {
  const [devices, setDevices] = useState<DeviceSummary[]>([])
  const [selectedDevice, setSelectedDevice] = useState<DeviceSummary | null>(null)
  const [loading, setLoading] = useState(false) // 초기값을 false로 변경하여 UI 블로킹 방지
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const location = useLocation()
  const params = useParams<{ deviceId?: string }>()

  // 설비 목록 가져오기
  const fetchDevices = async () => {
    try {
      setLoading(true)
      setError(null)

      // 타임아웃 설정 (3초로 단축)
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('타임아웃')), 3000)
      })

      const response = await Promise.race([
        getSensorStatus(),
        timeoutPromise
      ]) as Awaited<ReturnType<typeof getSensorStatus>>
      
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
      console.error('[DeviceContext] 설비 목록 로딩 실패:', err)
      setError(err.response?.data?.message || err.message || '설비 목록을 불러오는데 실패했습니다.')
      setDevices([])
    } finally {
      setLoading(false)
    }
  }

  // URL 파라미터에서 deviceId 추출 및 선택된 설비 설정
  useEffect(() => {
    const deviceId = params.deviceId
    if (deviceId && devices.length > 0) {
      const device = devices.find((d) => d.device_id === deviceId)
      if (device) {
        setSelectedDevice(device)
      } else {
        setSelectedDevice(null)
      }
    } else {
      setSelectedDevice(null)
    }
  }, [params.deviceId, devices])

  // 초기 로드 시 설비 목록 가져오기 (지연 실행으로 초기 렌더링 블로킹 방지)
  useEffect(() => {
    // 초기 렌더링 후 약간의 지연을 두고 데이터 로딩 (UI 블로킹 방지)
    const timer = setTimeout(() => {
      fetchDevices()
    }, 50) // 50ms로 단축 (더 빠른 데이터 로딩)
    
    return () => clearTimeout(timer)
  }, [])

  // 설비 ID 자동 생성
  const generateDeviceId = (existingDevices: DeviceSummary[]): string => {
    // 기존 설비 ID 패턴 분석
    const patterns: { prefix: string; numbers: number[] }[] = []
    
    existingDevices.forEach((device) => {
      const match = device.device_id.match(/^(.+?)-(\d+)$/)
      if (match) {
        const prefix = match[1]
        const number = parseInt(match[2], 10)
        const pattern = patterns.find((p) => p.prefix === prefix)
        if (pattern) {
          pattern.numbers.push(number)
        } else {
          patterns.push({ prefix, numbers: [number] })
        }
      }
    })

    // 가장 많이 사용된 패턴 찾기
    if (patterns.length > 0) {
      const mostUsedPattern = patterns.reduce((prev, curr) => 
        curr.numbers.length > prev.numbers.length ? curr : prev
      )
      const maxNumber = Math.max(...mostUsedPattern.numbers, 0)
      return `${mostUsedPattern.prefix}-${maxNumber + 1}`
    }

    // 기본 패턴 사용
    const defaultPrefix = 'Demo-Conveyor'
    const existingNumbers = existingDevices
      .map((d) => {
        const match = d.device_id.match(/^Demo-Conveyor-(\d+)$/)
        return match ? parseInt(match[1], 10) : 0
      })
      .filter((n) => n > 0)
    
    const nextNumber = existingNumbers.length > 0 ? Math.max(...existingNumbers) + 1 : 1
    return `${defaultPrefix}-${String(nextNumber).padStart(2, '0')}`
  }

  // 설비 추가 함수
  const addDevice = (formData: AddEquipmentFormData): DeviceSummary => {
    // 새 설비 ID 생성
    const newDeviceId = generateDeviceId(devices)

    // 새 설비 객체 생성
    const newDevice: DeviceSummary = {
      device_id: newDeviceId,
      name: formData.name,
      category: formData.category,
      dashboardUID: 'adckqfq', // 기본 대시보드 UID
      status: formData.status,
      sensorCount: formData.sensorCount,
      alertCount: formData.alertCount,
      operationRate: formData.operationRate,
      lastUpdated: new Date().toISOString(),
    }

    // 설비 목록에 추가
    setDevices((prevDevices) => [...prevDevices, newDevice])
    
    console.log('[DeviceContext] 새 설비 추가:', newDevice)
    return newDevice
  }

  // 설비 삭제 함수
  const removeDevice = (deviceId: string) => {
    setDevices((prevDevices) => {
      const filtered = prevDevices.filter((d) => d.device_id !== deviceId)
      console.log('[DeviceContext] 설비 삭제:', deviceId, '남은 설비 수:', filtered.length)
      
      // 삭제된 설비가 현재 선택된 설비인 경우 선택 해제
      if (selectedDevice?.device_id === deviceId) {
        setSelectedDevice(null)
      }
      
      return filtered
    })
  }

  // 설비 선택 변경 핸들러
  const setSelectedDeviceId = (deviceId: string | null) => {
    if (!deviceId) {
      // 설비 목록 페이지로 이동
      navigate('/devices')
      return
    }

    // 현재 경로에서 deviceId만 변경
    const currentPath = location.pathname
    
    // /devices/:deviceId/* 패턴인지 확인
    if (currentPath.startsWith('/devices/')) {
      const pathParts = currentPath.split('/')
      if (pathParts.length >= 3) {
        // /devices/:deviceId/dashboard -> /devices/newDeviceId/dashboard
        const newPath = `/devices/${deviceId}/${pathParts.slice(3).join('/') || 'dashboard'}`
        navigate(newPath)
      } else {
        // /devices/:deviceId -> /devices/newDeviceId/dashboard
        navigate(`/devices/${deviceId}/dashboard`)
      }
    } else {
      // 기존 경로에서 deviceId 경로로 리다이렉트
      // 예: /alerts -> /devices/:deviceId/alerts
      const pathMap: Record<string, string> = {
        '/': 'dashboard',
        '/alerts': 'alerts',
        '/reports': 'reports',
        '/monitoring': 'monitoring',
      }
      
      const subPath = pathMap[currentPath] || 'dashboard'
      navigate(`/devices/${deviceId}/${subPath}`)
    }
  }

  const value: DeviceContextType = {
    devices,
    selectedDevice,
    selectedDeviceId: params.deviceId || null,
    loading,
    error,
    setSelectedDeviceId,
    refreshDevices: fetchDevices,
    addDevice,
    removeDevice,
  }

  return <DeviceContext.Provider value={value}>{children}</DeviceContext.Provider>
}

export function useDeviceContext() {
  const context = useContext(DeviceContext)
  if (context === undefined) {
    throw new Error('useDeviceContext must be used within a DeviceProvider')
  }
  return context
}

