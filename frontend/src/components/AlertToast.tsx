import React, { useEffect } from 'react';
// 1. 방금 설치한 'react-icons'에서 아이콘들을 가져옵니다.
import {
  FiCheckCircle, // (Success/Info)
  FiAlertTriangle, // (Warning)
  FiAlertOctagon, // (Error)
  FiXCircle, // (Critical)
  FiX, // (닫기 버튼)
} from 'react-icons/fi';

// 2. Alert의 레벨을 정의합니다 (types/api.ts와 유사하게)
export type AlertLevel = 'info' | 'warning' | 'error' | 'critical';

// 3. AlertToast가 받을 props를 정의합니다.
interface AlertToastProps {
  level: AlertLevel;
  message: string;
  onClose: () => void;
  duration?: number; // 닫기 버튼 클릭 시 호출될 함수
}

// 4. 레벨(level)에 따라 다른 스타일(아이콘, 색상)을 매핑하는 객체
const alertStyles = {
  info: {
    icon: <FiCheckCircle className="h-6 w-6 text-blue-500" />,
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-400',
  },
  warning: {
    icon: <FiAlertTriangle className="h-6 w-6 text-yellow-500" />,
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-400',
  },
  error: {
    icon: <FiAlertOctagon className="h-6 w-6 text-red-500" />,
    bgColor: 'bg-red-50',
    borderColor: 'border-red-400',
  },
  critical: {
    icon: <FiXCircle className="h-6 w-6 text-red-800" />,
    bgColor: 'bg-red-100',
    borderColor: 'border-red-700',
  },
};

// 5. AlertToast 컴포넌트 본체
const AlertToast: React.FC<AlertToastProps> = ({
  level,
  message,
  onClose,
  duration = 5000, // 3. 기본 5초, 0이면 자동 닫기 안 함
}) => {
  const style = alertStyles[level];

  // 4. 자동 닫기 useEffect 추가
  useEffect(() => {
    // duration이 0보다 클 때만 타이머 설정
    if (duration > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);

      // 컴포넌트가 언마운트되거나 (예: 수동 닫기)
      // duration, onClose가 변경될 때 타이머를 정리합니다.
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  return (
    // '작업 4' 요구사항: 애니메이션 (임시로 fade-in 효과)
    // '작업 4' 요구사항: 스타일링 (레벨별 색상)
    <div
      className={`
        w-full max-w-sm rounded-lg shadow-lg overflow-hidden 
        border-l-4 ${style.bgColor} ${style.borderColor}
        animate-fade-in
      `}
      role="alert"
    >
      <div className="flex items-center p-4">
        {/* 1. 아이콘 */}
        <div className="flex-shrink-0">{style.icon}</div>

        {/* 2. 메시지 */}
        <div className="ml-3 flex-1">
          <p className="text-sm font-medium text-gray-900">{message}</p>
        </div>

        {/* 3. 닫기 버튼 */}
        {/* '작업 4' 요구사항: 클릭 이벤트 처리 */}
        <div className="ml-4 flex-shrink-0">
          <button
            onClick={onClose}
            className={`
              inline-flex rounded-md p-1 
              text-gray-400 hover:text-gray-500 hover:bg-gray-100 
              focus:outline-none focus:ring-2 focus:ring-gray-400
            `}
          >
            <span className="sr-only">Close</span>
            <FiX className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default AlertToast;