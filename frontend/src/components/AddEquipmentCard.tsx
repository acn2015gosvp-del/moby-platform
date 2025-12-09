/**
 * 설비 추가 카드 컴포넌트
 * 
 * '+ 설비 추가' 버튼 역할을 하는 카드
 */

import React, { useState } from 'react'

interface AddEquipmentCardProps {
  onClick: () => void
  onRemove?: () => void
}

const AddEquipmentCard: React.FC<AddEquipmentCardProps> = ({ onClick, onRemove }) => {
  const [isHovered, setIsHovered] = useState(false)

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation() // 카드 클릭 이벤트 방지
    if (onRemove) {
      onRemove()
    }
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="새 설비 추가"
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onClick()
        }
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`
        relative bg-background-surface border border-dashed border-border rounded shadow-sm p-6 cursor-pointer
        transition-all duration-300 ease-out
        ${isHovered
          ? 'border-primary shadow-lg scale-[1.02] bg-primary/5'
          : 'hover:border-primary/50 hover:shadow-md'
        }
        focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background-main
        active:scale-[0.98]
      `}
    >
      {/* X 버튼 (제거 버튼) */}
      {onRemove && (
        <button
          onClick={handleRemove}
          onMouseEnter={(e) => e.stopPropagation()}
          onMouseLeave={(e) => e.stopPropagation()}
          className="absolute top-2 right-2 w-6 h-6 flex items-center justify-center rounded-full bg-background-main hover:bg-danger text-text-secondary hover:text-white transition-all duration-200 z-10"
          aria-label="설비 추가 슬롯 제거"
          title="이 슬롯 제거"
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
      <div className="flex flex-col items-center justify-center h-full min-h-[200px]">
        <div className={`
          w-16 h-16 rounded-full flex items-center justify-center mb-4
          transition-colors duration-300
          ${isHovered ? 'bg-primary/20' : 'bg-background-main'}
        `}>
          <svg
            className={`
              w-8 h-8 transition-colors duration-300
              ${isHovered ? 'text-primary' : 'text-text-secondary'}
            `}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
        </div>
        <h3 className={`
          text-lg font-bold mb-2 transition-colors duration-300
          ${isHovered ? 'text-primary' : 'text-text-primary'}
        `}>
          설비 추가
        </h3>
        <p className="text-sm text-text-secondary text-center">
          클릭하여 새 설비를 추가하세요
        </p>
      </div>
    </div>
  )
}

export default AddEquipmentCard

