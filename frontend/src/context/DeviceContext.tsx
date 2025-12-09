/**
 * 설비 선택 전역 상태 관리 Context
 * 
 * 현재 선택된 설비를 전역으로 관리하고 URL과 동기화합니다.
 */

import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
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

// 기본 목 데이터 (즉시 화면 표시용)
const DEFAULT_DEVICES: DeviceSummary[] = [
  {
    device_id: 'conveyor-belt-1',
    name: '컨베이어 벨트 #1',
    category: '운송 시스템',
    dashboardUID: 'conveyor-dashboard',
    status: '정상',
    sensorCount: 18,
    alertCount: 0,
    operationRate: 99.9,
    lastUpdated: new Date().toISOString(),
  },
  {
    device_id: 'cnc-machine-a3',
    name: 'CNC 밀링 머신 #A3',
    category: '가공 장비',
    dashboardUID: 'cnc-dashboard',
    status: '경고',
    sensorCount: 24,
    alertCount: 3,
    operationRate: 97.2,
    lastUpdated: new Date().toISOString(),
  },
  {
    device_id: 'robot-arm-r7',
    name: '산업용 로봇 팔 #R7',
    category: '자동화 설비',
    dashboardUID: 'robot-dashboard',
    status: '긴급',
    sensorCount: 32,
    alertCount: 8,
    operationRate: 85.4,
    lastUpdated: new Date().toISOString(),
  },
]

export function DeviceProvider({ children }: DeviceProviderProps) {
  // 기본 목 데이터로 초기화하여 즉시 화면 표시
  const [devices, setDevices] = useState<DeviceSummary[]>(DEFAULT_DEVICES)
  const [selectedDevice, setSelectedDevice] = useState<DeviceSummary | null>(null)
  const [loading, setLoading] = useState(false) // 초기값을 false로 설정하여 즉시 UI 표시
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const location = useLocation()
  const params = useParams<{ deviceId?: string }>()

  // 설비 목록 가져오기
  const fetchDevices = async () => {
    try {
      setError(null)
      
      // 로딩 상태는 설정하지 않음 (UI 블로킹 방지)
      // 데이터가 로드되면 자동으로 업데이트됨
      
      // 타임아웃 설정 (2초로 단축 - 빠른 실패)
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('타임아웃')), 2000)
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
    } catch (err: unknown) {
      // 에러는 조용히 처리 (콘솔에만 기록)
      console.warn('[DeviceContext] 설비 목록 로딩 실패:', err)
      // 에러 상태는 설정하지 않음 (사용자 경험 개선)
      setDevices([])
    }
    // 로딩 상태는 항상 false로 유지 (UI 블로킹 방지)
    setLoading(false)
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

  // 초기 로드 시 설비 목록 가져오기 (비동기, 블로킹 없음)
  useEffect(() => {
    // 기본 데이터는 이미 표시되었으므로, API는 백그라운드에서 로드
    // 타임아웃을 더 짧게 설정 (1초)
    const loadDevices = async () => {
      try {
        const timeoutPromise = new Promise<never>((_, reject) => {
          setTimeout(() => reject(new Error('타임아웃')), 1000)
        })

        const response = await Promise.race([
          getSensorStatus(),
          timeoutPromise
        ]) as Awaited<ReturnType<typeof getSensorStatus>>
        
        if (response.success && response.data) {
          const data = response.data as SensorStatusResponse
          if (data.devices && data.devices.length > 0) {
            // API 데이터로 업데이트 (기본 데이터 대체)
            setDevices(data.devices)
          }
        }
      } catch (err: any) {
        // API 실패 시 기본 데이터 유지 (이미 표시됨)
        console.debug('[DeviceContext] API 업데이트 실패, 기본 데이터 유지:', err.message)
      }
    }
    
    // 2초 후 백그라운드에서 로드 (사용자가 화면을 먼저 볼 수 있도록)
    setTimeout(loadDevices, 2000)
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

