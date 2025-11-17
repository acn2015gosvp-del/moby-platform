import React from 'react';
import { NavLink } from 'react-router-dom';

const Sidebar: React.FC = () => {
  // NavLink의 active/pending 상태에 따라 스타일을 동적으로 적용
  const getNavLinkClass = ({ isActive }: { isActive: boolean; }) =>
    `block py-2.5 px-4 rounded transition duration-200 hover:bg-gray-700 ${
      isActive ? 'bg-gray-900 text-white' : 'text-gray-300'
    }`;

  return (
    <div className="w-64 bg-gray-800 text-white p-4 h-full">
      <h2 className="text-xl font-bold mb-4">Navigation</h2>
      <nav>
        <ul>
          <li>
            <NavLink to="/" className={getNavLinkClass}>
              대시보드
            </NavLink>
          </li>
          <li>
            <NavLink to="/alerts" className={getNavLinkClass}>
              알림 목록
            </NavLink>
          </li>
          {/* (향후 다른 메뉴 추가...) */}
        </ul>
      </nav>
    </div>
  );
};

export default Sidebar;