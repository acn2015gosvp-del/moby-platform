/**
 * 설비 카드 컴포넌트
 * 
 * Grafana 대시보드로 이동하는 기능을 포함한 설비 카드
 */

import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { DeviceSummary } from '@/types/sensor'

interface EquipmentCardProps {
  device: DeviceSummary
  onClick?: (device: DeviceSummary) => void
  onRemove?: (deviceId: string) => void
}

const EquipmentCard: React.FC<EquipmentCardProps> = ({ device, onClick, onRemove }) => {
  const navigate = useNavigate()
  const [isHovered, setIsHovered] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isNewlyAdded, setIsNewlyAdded] = useState(false)
  
  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation() // 카드 클릭 이벤트 방지
    if (onRemove && device.device_id) {
      if (window.confirm(`"${device.name}" 설비를 삭제하시겠습니까?`)) {
        onRemove(device.device_id)
      }
    }
  }
  
  // 새로 추가된 카드인지 확인 (lastUpdated가 최근 5초 이내면 새로 추가된 것으로 간주)
  React.useEffect(() => {
    if (device.lastUpdated) {
      const lastUpdated = new Date(device.lastUpdated).getTime()
      const now = Date.now()
      const diff = now - lastUpdated
      
      if (diff < 5000) { // 5초 이내
        setIsNewlyAdded(true)
        // 3초 후 애니메이션 제거
        const timer = setTimeout(() => {
          setIsNewlyAdded(false)
        }, 3000)
        return () => clearTimeout(timer)
      }
    }
  }, [device.lastUpdated])

  const getStatusStyles = (status: DeviceSummary['status']) => {
    const styles = {
      '정상': {
        badge: 'bg-green-100 text-green-800 border-green-300',
        icon: (
          <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
      },
      '경고': {
        badge: 'bg-yellow-100 text-yellow-800 border-yellow-300',
        icon: (
          <svg className="w-5 h-5 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        ),
      },
      '긴급': {
        badge: 'bg-red-100 text-red-800 border-red-300',
        icon: (
          <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
      },
      '오프라인': {
        badge: 'bg-gray-100 text-gray-800 border-gray-300',
        icon: (
          <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
          </svg>
        ),
      },
    }
    return styles[status] || styles['오프라인']
  }

  const handleCardClick = () => {
    if (!device.device_id) {
      console.warn(`[${device.name}] 설비 ID가 없습니다.`)
      return
    }

    // onClick 콜백이 있으면 그것을 사용, 없으면 기본 동작
    if (onClick) {
      onClick(device)
    } else {
      // 기본 동작: 모니터링 페이지로 이동
      navigate(`/monitoring/${device.device_id}`)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleCardClick()
    }
  }

  const statusStyle = getStatusStyles(device.status)

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={`${device.name} 설비 대시보드 열기`}
      data-device-id={device.device_id}
      onClick={handleCardClick}
      onKeyDown={handleKeyPress}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`
        relative bg-white rounded-lg shadow p-6 cursor-pointer
        transition-all duration-300 ease-out
        ${isHovered
          ? 'shadow-xl scale-[1.02] border-2 border-blue-600'
          : 'border-2 border-transparent hover:shadow-lg'
        }
        ${isLoading ? 'opacity-60 pointer-events-none' : ''}
        ${isNewlyAdded ? 'animate-pulse border-2 border-green-400 shadow-lg' : ''}
        focus:outline-none focus:ring-4 focus:ring-blue-300
        active:scale-[0.98]
      `}
    >
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-70 rounded-lg z-10">
          <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
        </div>
      )}

      <div className="flex items-start justify-between mb-4">
        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
          <svg className="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-3 py-1 rounded-full text-xs font-medium border ${statusStyle.badge}`}>
            {device.status}
          </span>
          {/* 삭제 버튼 (X) */}
          {onRemove && (
            <button
              onClick={handleRemove}
              onMouseEnter={(e) => e.stopPropagation()}
              onMouseLeave={(e) => e.stopPropagation()}
              className="w-6 h-6 flex items-center justify-center rounded-full bg-gray-200 hover:bg-red-500 text-gray-600 hover:text-white transition-all duration-200"
              aria-label={`${device.name} 설비 삭제`}
              title="설비 삭제"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
        </div>
      </div>

      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-1">
          {device.name}
        </h3>
        {device.category && (
          <p className="text-sm text-gray-600">{device.category}</p>
        )}
      </div>

      <div className="border-t border-gray-200 pt-4">
        <div className="grid grid-cols-3 gap-3">
          <div>
            <div className="flex items-center gap-1 mb-1">
              <div className="w-2 h-2 rounded-full bg-blue-600"></div>
              <span className="text-xs text-gray-600">센서</span>
            </div>
            <p className="text-lg font-semibold text-gray-800">
              {device.sensorCount ?? '-'}
            </p>
          </div>
          <div>
            <div className="flex items-center gap-1 mb-1">
              <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
              <span className="text-xs text-gray-600">알림</span>
            </div>
            <p className="text-lg font-semibold text-gray-800">
              {device.alertCount ?? '-'}
            </p>
          </div>
          <div>
            <div className="flex items-center gap-1 mb-1">
              <div className="w-2 h-2 rounded-full bg-green-500"></div>
              <span className="text-xs text-gray-600">가동률</span>
            </div>
            <p className="text-lg font-semibold text-gray-800">
              {device.operationRate != null ? `${device.operationRate}%` : '-'}
            </p>
          </div>
        </div>
      </div>

      <div
        className={`
          absolute bottom-4 right-4
          transition-all duration-300
          ${isHovered ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-2'}
        `}
        aria-hidden="true"
      >
        <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </div>
  )
}

export default EquipmentCard

