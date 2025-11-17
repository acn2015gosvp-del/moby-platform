import React from 'react';

// isConnected prop 타입 정의
interface HeaderProps {
    isConnected: boolean;
}

// Header 컴포넌트가 isConnected를 받도록 수정
const Header: React.FC<HeaderProps> = ({ isConnected }) => { 
  // 연결 상태에 따라 색상과 텍스트를 결정
  const statusColor = isConnected ? 'bg-green-500' : 'bg-red-500';
  const statusText = isConnected ? 'Connected' : 'Disconnected';
  
  return (
    <header className="bg-white shadow-md p-4 flex justify-between items-center">
      {/* 1. 헤더 제목 */}
      <h1 className="text-2xl font-semibold text-gray-800">
        MOBY Platform
      </h1>

      {/* 2. WS 연결 상태 표시 UI */}
      <div className="flex items-center space-x-3">
        <span className="text-gray-600">WS Status:</span>
        <div className={`w-3 h-3 rounded-full ${statusColor} animate-pulse`} title={`WS Status: ${statusText}`}></div>
        <span className="text-sm text-gray-700 font-medium">{statusText}</span>
      </div>
    </header>
  );
};

export default Header;