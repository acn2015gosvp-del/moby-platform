/**
 * 설비 목록 페이지 (진입점)
 * 
 * 로그인 후 첫 화면으로 표시되는 설비 목록 대시보드
 */

import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import EquipmentCard from '@/components/EquipmentCard'
import AddEquipmentCard from '@/components/AddEquipmentCard'
import AddEquipmentModal, { type AddEquipmentFormData } from '@/components/AddEquipmentModal'
import { useDeviceContext } from '@/context/DeviceContext'
import Loading from '@/components/common/Loading'

const EquipmentList: React.FC = () => {
  const { devices, loading, error, addDevice, removeDevice } = useDeviceContext()
  const navigate = useNavigate()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [clickedSlotIndex, setClickedSlotIndex] = useState<number | null>(null)
  const [removedSlots, setRemovedSlots] = useState<Set<number>>(new Set())

  // 설비 카드 클릭 핸들러 - 설비 상세 페이지로 이동
  const handleDeviceClick = (deviceId: string) => {
    navigate(`/devices/${deviceId}/dashboard`)
  }

  // 설비 추가 카드 클릭 핸들러 (클릭한 슬롯 인덱스 저장)
  const handleAddCardClick = (slotIndex: number) => {
    setClickedSlotIndex(slotIndex)
    setIsModalOpen(true)
  }

  // 모달에서 설비 추가 핸들러
  const handleModalSubmit = (formData: AddEquipmentFormData) => {
    try {
      // 1. 설비 데이터 객체 생성 및 상태 업데이트
      const newDevice = addDevice(formData)
      
      console.log('[EquipmentList] 새 설비 추가 완료:', {
        device: newDevice,
        clickedSlotIndex,
        totalDevices: devices.length + 1
      })
      
      // 2. 모달 폼 닫기
      setIsModalOpen(false)
      setClickedSlotIndex(null)
      
      // 3. 새로 추가된 설비 카드로 스크롤 (선택사항)
      // setTimeout을 사용하여 DOM 업데이트 후 스크롤
      setTimeout(() => {
        const newCardElement = document.querySelector(`[data-device-id="${newDevice.device_id}"]`)
        if (newCardElement) {
          newCardElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
        }
      }, 100)
      
    } catch (error) {
      console.error('[EquipmentList] 설비 추가 실패:', error)
      // 에러 발생 시에도 모달은 닫음
      setIsModalOpen(false)
      setClickedSlotIndex(null)
    }
  }

  // 모달 닫기 핸들러
  const handleModalClose = () => {
    setIsModalOpen(false)
    setClickedSlotIndex(null)
  }

  // 설비 추가 슬롯 제거 핸들러
  const handleRemoveSlot = (slotIndex: number) => {
    setRemovedSlots((prev) => {
      const newSet = new Set(prev)
      newSet.add(slotIndex)
      return newSet
    })
  }

  // 표시할 추가 카드 개수 계산 (제거된 슬롯 제외)
  const MAX_ADD_CARDS = 3
  const addCardCount = MAX_ADD_CARDS

  // 로딩 중이어도 기본 UI는 표시 (로딩 오버레이 방식)
  const showLoadingOverlay = loading && devices.length === 0

  if (error) {
    return (
      <div className="min-h-screen bg-background-main p-6">
        <h1 className="text-3xl font-bold mb-6 text-text-primary">설비 목록</h1>
        <div className="mb-6 p-4 bg-danger/10 border border-danger rounded-xl text-danger">
          {error}
        </div>
        <button
          onClick={() => window.location.reload()}
          className="px-6 py-2 bg-primary text-background-main font-bold rounded-lg hover:brightness-110 transition-colors"
        >
          다시 시도
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background-main p-6 relative">
      {/* 헤더 영역 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text-primary mb-2">설비 목록</h1>
      </div>

      {/* 로딩 오버레이 (초기 로딩 시에만 표시) */}
      {showLoadingOverlay && (
        <div className="absolute inset-0 bg-background-main/75 flex items-center justify-center z-10 rounded-lg">
          <Loading message="설비 목록을 불러오는 중..." />
        </div>
      )}

      {/* 설비 카드 그리드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* 기존 설비 카드 */}
        {devices.map((device) => (
          <EquipmentCard
            key={device.device_id}
            device={device}
            onClick={() => handleDeviceClick(device.device_id)}
            onRemove={removeDevice}
          />
        ))}
        
        {/* 설비 추가 카드 (제거되지 않은 슬롯만 표시) */}
        {Array.from({ length: addCardCount })
          .map((_, index) => index)
          .filter((index) => !removedSlots.has(index))
          .map((index) => (
            <AddEquipmentCard
              key={`add-equipment-${index}`}
              onClick={() => handleAddCardClick(index)}
              onRemove={() => handleRemoveSlot(index)}
            />
          ))}
      </div>

      {/* 설비 추가 모달 */}
      <AddEquipmentModal
        isOpen={isModalOpen}
        onClose={handleModalClose}
        onSubmit={handleModalSubmit}
      />

      {!loading && devices.length === 0 && (
        <div className="text-center py-20 bg-background-surface border border-border rounded-xl">
          <div className="text-text-secondary text-6xl mb-4">🏭</div>
          <p className="text-text-primary text-lg mb-2">등록된 설비가 없습니다.</p>
          <p className="text-text-secondary text-sm">백엔드 API에서 설비 목록 데이터를 확인해주세요.</p>
        </div>
      )}
    </div>
  )
}

export default EquipmentList

