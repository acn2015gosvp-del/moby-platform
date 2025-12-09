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
        badge: 'bg-success/10 text-success border-success/30',
        icon: (
          <svg className="w-5 h-5 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
      },
      '경고': {
        badge: 'bg-warning/10 text-warning border-warning/30',
        icon: (
          <svg className="w-5 h-5 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        ),
      },
      '긴급': {
        badge: 'bg-danger/10 text-danger border-danger/30',
        icon: (
          <svg className="w-5 h-5 text-danger" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
      },
      '오프라인': {
        badge: 'bg-text-secondary/10 text-text-secondary border-border',
        icon: (
          <svg className="w-5 h-5 text-text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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

  // CNC 밀링 머신인지 확인
  const isCNCMillingMachine = device.name?.includes('CNC 밀링 머신') || device.name?.includes('밀링')

  // 알림 색상 결정
  const getAlertColor = () => {
    if (isCNCMillingMachine) {
      // CNC 밀링 머신은 주황색
      return 'text-warning'
    }
    // 기존 로직: 경고/긴급 상태이거나 알림이 있으면 빨간색
    if (device.status === '경고' || device.status === '긴급' || (device.alertCount && device.alertCount > 0)) {
      return 'text-danger'
    }
    return 'text-secondary'
  }

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
        relative bg-background-surface border border-border rounded-xl shadow-sm p-6 cursor-pointer
        transition-all duration-300 ease-out
        ${isHovered
          ? 'shadow-lg scale-[1.02] border-primary'
          : 'hover:shadow-md'
        }
        ${isNewlyAdded ? 'animate-pulse border-success shadow-lg' : ''}
        focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background-main
        active:scale-[0.98]
      `}
    >

      <div className="flex items-start justify-between mb-4">
        <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
          <svg className="w-6 h-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
              className="w-6 h-6 flex items-center justify-center rounded-full bg-background-main hover:bg-danger text-text-secondary hover:text-white transition-all duration-200"
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
        <h3 className="text-lg font-bold text-text-primary mb-1">
          {device.name}
        </h3>
        {device.category && (
          <p className="text-sm text-text-secondary">{device.category}</p>
        )}
      </div>

      <div className="border-t border-border pt-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="flex items-center gap-1 mb-1">
              <div className="w-2 h-2 rounded-full bg-warning"></div>
              <span className="text-xs text-text-secondary">알림</span>
            </div>
            <p className={`text-2xl font-semibold font-mono ${getAlertColor()}`}>
              {device.alertCount ?? '-'}
            </p>
          </div>
          <div>
            <div className="flex items-center gap-1 mb-1">
              <div className="w-2 h-2 rounded-full bg-success"></div>
              <span className="text-xs text-text-secondary">가동률</span>
            </div>
            <p className="text-2xl font-semibold font-mono text-secondary">
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
        <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </div>
  )
}

export default EquipmentCard

