/**
 * 사이드바 컴포넌트
 */

import { Link, useLocation } from 'react-router-dom'

interface SidebarItem {
  path: string
  label: string
  icon?: string
}

const menuItems: SidebarItem[] = [
  { path: '/', label: '운영관리', icon: '📊' },
  { path: '/alerts', label: '알림', icon: '🚨' },
  { path: '/monitoring', label: '모니터링', icon: '📈' },
  { path: '/equipment', label: '설비 목록', icon: '🏭' },
  { path: '/reports', label: '보고서', icon: '📄' },
]

function Sidebar() {
  const location = useLocation()

  const isActive = (path: string) => {
    if (path === '/monitoring') {
      // 모니터링 페이지는 /monitoring으로 시작하는 모든 경로에서 활성화
      return location.pathname.startsWith('/monitoring')
    }
    return location.pathname === path
  }

  return (
    <aside className="w-64 bg-white shadow-sm border-r min-h-screen">
      <div className="p-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">메뉴</h2>
        <nav className="space-y-2">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                isActive(item.path)
                  ? 'bg-blue-100 text-blue-700 font-medium'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              {item.icon && <span className="text-xl">{item.icon}</span>}
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>
      </div>
    </aside>
  )
}

export default Sidebar

