/**
 * 설비 추가 모달 컴포넌트
 * 
 * 새로운 설비 정보를 입력받는 모달 폼
 */

import React, { useState, useEffect, useRef } from 'react'

export interface AddEquipmentFormData {
  name: string
  category: string
  status: '정상' | '경고' | '긴급' | '오프라인'
  sensorCount: number
  alertCount: number
  operationRate: number
}

interface AddEquipmentModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: AddEquipmentFormData) => void
}

const AddEquipmentModal: React.FC<AddEquipmentModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [formData, setFormData] = useState<AddEquipmentFormData>({
    name: '',
    category: '',
    status: '정상',
    sensorCount: 0,
    alertCount: 0,
    operationRate: 0,
  })

  const [errors, setErrors] = useState<Partial<Record<keyof AddEquipmentFormData, string>>>({})
  const modalRef = useRef<HTMLDivElement>(null)

  // 모달이 열릴 때마다 폼 초기화 (기본값 설정)
  useEffect(() => {
    if (isOpen) {
      setFormData({
        name: '',
        category: '',
        status: '정상',
        sensorCount: 0, // 기본값: 0
        alertCount: 0, // 기본값: 0 (알림)
        operationRate: 100, // 기본값: 100% (정상 상태)
      })
      setErrors({})
    }
  }, [isOpen])

  // 모달 외부 클릭 시 닫기
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
        onClose()
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      // ESC 키로 닫기
      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          onClose()
        }
      }
      document.addEventListener('keydown', handleEscape)
      return () => {
        document.removeEventListener('mousedown', handleClickOutside)
        document.removeEventListener('keydown', handleEscape)
      }
    }
  }, [isOpen, onClose])

  // 모달이 열려있을 때 body 스크롤 방지
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  const handleChange = (
    field: keyof AddEquipmentFormData,
    value: string | number
  ) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }))
    // 에러 초기화
    if (errors[field]) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }))
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof AddEquipmentFormData, string>> = {}

    if (!formData.name.trim()) {
      newErrors.name = '설비 이름을 입력해주세요.'
    }

    if (!formData.category.trim()) {
      newErrors.category = '운용 시스템을 입력해주세요.'
    }

    if (formData.sensorCount < 0) {
      newErrors.sensorCount = '센서 수는 0 이상이어야 합니다.'
    }

    if (formData.alertCount < 0) {
      newErrors.alertCount = '알림 수는 0 이상이어야 합니다.'
    }

    if (formData.operationRate < 0 || formData.operationRate > 100) {
      newErrors.operationRate = '가동률은 0~100 사이의 값이어야 합니다.'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    onSubmit(formData)
    onClose()
  }

  const handleCancel = () => {
    setFormData({
      name: '',
      category: '',
      status: '정상',
      sensorCount: 0,
      alertCount: 0,
      operationRate: 100,
    })
    setErrors({})
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* 배경 오버레이 */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={handleCancel}
      />

      {/* 모달 컨텐츠 */}
      <div
        ref={modalRef}
        className="relative bg-white rounded-xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 헤더 */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg
                className="w-6 h-6 text-blue-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-800">새로운 설비 추가</h2>
          </div>
          <button
            onClick={handleCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="닫기"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* 폼 컨텐츠 */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* 설비 이름 */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              설비 이름
            </label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              placeholder="예: 컨베이어 벨트 #5"
              className={`
                w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500
                ${errors.name ? 'border-red-300' : 'border-gray-300'}
              `}
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-600">{errors.name}</p>
            )}
          </div>

          {/* 운용 시스템 */}
          <div>
            <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
              운용 시스템
            </label>
            <input
              type="text"
              id="category"
              value={formData.category}
              onChange={(e) => handleChange('category', e.target.value)}
              placeholder="예: 큐 타놀리하"
              className={`
                w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500
                ${errors.category ? 'border-red-300' : 'border-gray-300'}
              `}
            />
            {errors.category && (
              <p className="mt-1 text-sm text-red-600">{errors.category}</p>
            )}
          </div>

          {/* 상태 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              상태
            </label>
            <div className="grid grid-cols-3 gap-3">
              {(['정상', '경고', '긴급'] as const).map((status) => (
                <button
                  key={status}
                  type="button"
                  onClick={() => handleChange('status', status)}
                  className={`
                    px-4 py-2 rounded-lg border-2 font-medium transition-all
                    ${
                      formData.status === status
                        ? status === '정상'
                          ? 'bg-green-50 border-green-500 text-green-700'
                          : status === '경고'
                          ? 'bg-yellow-50 border-yellow-500 text-yellow-700'
                          : 'bg-red-50 border-red-500 text-red-700'
                        : 'bg-white border-gray-300 text-gray-700 hover:border-gray-400'
                    }
                  `}
                >
                  {status}
                </button>
              ))}
            </div>
          </div>

          {/* 센서 */}
          <div>
            <label htmlFor="sensorCount" className="block text-sm font-medium text-gray-700 mb-2">
              센서 <span className="text-gray-400 font-normal text-xs">(선택사항)</span>
            </label>
            <input
              type="number"
              id="sensorCount"
              value={formData.sensorCount || ''}
              onChange={(e) => handleChange('sensorCount', parseInt(e.target.value) || 0)}
              placeholder="0"
              min="0"
              className={`
                w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500
                ${errors.sensorCount ? 'border-red-300' : 'border-gray-300'}
              `}
            />
            {errors.sensorCount && (
              <p className="mt-1 text-sm text-red-600">{errors.sensorCount}</p>
            )}
          </div>

          {/* 알림 */}
          <div>
            <label htmlFor="alertCount" className="block text-sm font-medium text-gray-700 mb-2">
              알림 <span className="text-gray-400 font-normal text-xs">(선택사항)</span>
            </label>
            <input
              type="number"
              id="alertCount"
              value={formData.alertCount || ''}
              onChange={(e) => handleChange('alertCount', parseInt(e.target.value) || 0)}
              placeholder="0"
              min="0"
              className={`
                w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500
                ${errors.alertCount ? 'border-red-300' : 'border-gray-300'}
              `}
            />
            {errors.alertCount && (
              <p className="mt-1 text-sm text-red-600">{errors.alertCount}</p>
            )}
          </div>

          {/* 가동률 */}
          <div>
            <label htmlFor="operationRate" className="block text-sm font-medium text-gray-700 mb-2">
              가동률 (%) <span className="text-gray-400 font-normal text-xs">(선택사항)</span>
            </label>
            <div className="relative">
              <input
                type="number"
                id="operationRate"
                value={formData.operationRate || ''}
                onChange={(e) => handleChange('operationRate', parseFloat(e.target.value) || 100)}
                placeholder="100"
                min="0"
                max="100"
                step="0.1"
                className={`
                  w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500
                  ${errors.operationRate ? 'border-red-300' : 'border-gray-300'}
                `}
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none">
                %
              </span>
            </div>
            {errors.operationRate && (
              <p className="mt-1 text-sm text-red-600">{errors.operationRate}</p>
            )}
          </div>

          {/* 액션 버튼 */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={handleCancel}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              추가
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default AddEquipmentModal

