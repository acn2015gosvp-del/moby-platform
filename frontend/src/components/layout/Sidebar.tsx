/**
 * 사이드바 컴포넌트
 * 설비 중심 구조에 맞게 deviceId를 포함한 경로로 이동
 */

import { Link, useLocation, useParams } from 'react-router-dom'
import { useDeviceContext } from '@/context/DeviceContext'

interface SidebarItem {
  subPath: string
  label: string
  icon?: string
}

const menuItems: SidebarItem[] = [
  { subPath: 'dashboard', label: '운영관리', icon: '📊' },
  { subPath: 'alerts', label: '알림', icon: '🚨' },
  { subPath: 'monitoring', label: '모니터링', icon: '📈' },
  { subPath: 'reports', label: '보고서', icon: '📄' },
]

function Sidebar() {
  const location = useLocation()
  const params = useParams<{ deviceId?: string }>()
  const { selectedDeviceId } = useDeviceContext()

  // 설비 목록 페이지에서는 사이드바 숨김
  const isDeviceListPage = location.pathname === '/' || location.pathname === '/devices'
  if (isDeviceListPage) {
    return null
  }

  // deviceId가 없으면 사이드바 숨김
  const deviceId = params.deviceId || selectedDeviceId
  if (!deviceId) {
    return null
  }

  const isActive = (subPath: string) => {
    return location.pathname === `/devices/${deviceId}/${subPath}`
  }

  return (
    <aside className="w-64 bg-white shadow-sm border-r min-h-screen">
      <div className="p-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">메뉴</h2>
        <nav className="space-y-2">
          {menuItems.map((item) => {
            const path = `/devices/${deviceId}/${item.subPath}`
            return (
              <Link
                key={item.subPath}
                to={path}
                className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive(item.subPath)
                    ? 'bg-blue-100 text-blue-700 font-medium'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                {item.icon && <span className="text-xl">{item.icon}</span>}
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>
      </div>
    </aside>
  )
}

export default Sidebar

