import React from 'react';

const Header: React.FC = () => {
  return (
    <header className="bg-white shadow-md p-4 flex justify-between items-center">
      {/* (임시) 헤더 제목 */}
      <h1 className="text-2xl font-semibold text-gray-800">
        MOBY Platform
      </h1>

      {/* (임시) 사용자 프로필 */}
      <div>
        <span className="text-gray-600">User: Stark (임시)</span>
      </div>
    </header>
  );
};

export default Header;