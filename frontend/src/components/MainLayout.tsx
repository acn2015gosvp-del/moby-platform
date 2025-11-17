import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';
import useWebSocket from '../hooks/useWebSocket'; 

// .env 파일의 API URL을 가져옵니다. (없으면 기본값 사용)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'; 


const MainLayout: React.FC = () => {
  // ESLint/TS 오류 해결을 위해 명시적인 무시 주석을 추가합니다.
  // 이 훅 호출이 곧 WebSocket 연결을 시작하고 유지합니다.
  // eslint-disable-next-line @typescript-eslint/no-unused-vars 
  const { isConnected } = useWebSocket(API_BASE_URL); 

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header에 isConnected 상태를 전달합니다. */}
        <Header isConnected={isConnected} /> 

        <main className="flex-1 p-6 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default MainLayout;