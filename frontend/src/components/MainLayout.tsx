import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';   // 1. import
import Sidebar from './Sidebar'; // 2. import

const MainLayout: React.FC = () => {
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar: 실제 컴포넌트로 교체 */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header: 실제 컴포넌트로 교체 */}
        <Header />

        {/* Page Content: Outlet */}
        <main className="flex-1 p-6 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default MainLayout;