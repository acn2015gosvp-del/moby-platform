import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';
import AlertToast from '../components/AlertToast';
import type { AlertLevel } from '../components/AlertToast';

// 1. Toast 데이터와 AlertToast 컴포넌트의 Props를 연결합니다.
export interface Toast extends Pick<React.ComponentProps<typeof AlertToast>, 'level' | 'message' | 'duration'> {
  id: number;
}

// 2. Context가 제공할 함수들을 정의합니다.
interface ToastContextType {
  showToast: (message: string, level?: AlertLevel, duration?: number) => void;
}

// 3. Context 생성
const ToastContext = createContext<ToastContextType | undefined>(undefined);

// 4. 고유 ID 생성을 위한 카운터 (토스트가 겹치지 않게 합니다)
let toastIdCounter = 0;

// 5. ToastProvider 컴포넌트 생성 (전역 상태 관리)
export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  // Toast를 스택에 추가하는 함수
  const showToast = useCallback((
    message: string,
    level: AlertLevel = 'info',
    duration: number = 5000
  ) => {
    const newToast: Toast = {
      id: toastIdCounter++,
      message,
      level,
      duration,
    };
    // 새로운 토스트가 추가될 때마다 상태를 업데이트합니다.
    setToasts((prevToasts) => [...prevToasts, newToast]);
  }, []);

  // Toast를 스택에서 제거하는 함수
  const hideToast = useCallback((id: number) => {
    setToasts((prevToasts) => prevToasts.filter((toast) => toast.id !== id));
  }, []);

  // Context 값을 메모이제이션 (성능 최적화)
  const contextValue = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      
      {/* ToastContainer 역할: Context가 직접 토스트 목록을 렌더링합니다. */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toasts.map((toast) => (
          <AlertToast
            key={toast.id}
            level={toast.level}
            message={toast.message}
            duration={toast.duration}
            // AlertToast에서 onClose가 호출되면, hideToast로 상태에서 제거합니다.
            onClose={() => hideToast(toast.id)}
          />
        ))}
      </div>
    </ToastContext.Provider>
  );
};

// 6. useToast Hook 생성 (컴포넌트에서 showToast를 쉽게 호출할 수 있게 합니다)
export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};