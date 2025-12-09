/**
 * 사이드바 컴포넌트
 * 설비 중심 구조에 맞게 deviceId를 포함한 경로로 이동
 */

import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { useDeviceContext } from '@/context/DeviceContext'
import { useAuth } from '@/context/AuthContext'

interface SidebarItem {
  subPath: string
  label: string
  icon?: React.ReactNode
}

// 아이콘 컴포넌트들
const DashboardIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
)

const AlertsIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
  </svg>
)

const MonitoringIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    {/* 반원형 게이지 외곽선 */}
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M12 20C7.58172 20 4 16.4183 4 12C4 7.58172 7.58172 4 12 4"
    />
    {/* 게이지 바늘 (중간 정도 위치) */}
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M12 12L16 8"
    />
    {/* 중심점 */}
    <circle cx="12" cy="12" r="1.5" fill="currentColor" />
  </svg>
)

const ReportsIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
)

const menuItems: SidebarItem[] = [
  { subPath: 'dashboard', label: '운영관리', icon: <DashboardIcon /> },
  { subPath: 'alerts', label: '알림', icon: <AlertsIcon /> },
  { subPath: 'monitoring', label: '모니터링', icon: <MonitoringIcon /> },
  { subPath: 'reports', label: '보고서', icon: <ReportsIcon /> },
]

function Sidebar() {
  const location = useLocation()
  const navigate = useNavigate()
  const params = useParams<{ deviceId?: string }>()
  const { devices, selectedDeviceId } = useDeviceContext()
  const { user, logout } = useAuth()

  // 현재 선택된 설비
  const deviceId = params.deviceId || selectedDeviceId

  const isListActive = location.pathname === '/' || location.pathname === '/devices'

  const isActive = (subPath: string) => {
    if (!deviceId || subPath === '') return false
    return location.pathname === `/devices/${deviceId}/${subPath}`
  }

  const selectedDeviceName =
    devices.find((d) => d.device_id === deviceId)?.name || (deviceId ? deviceId : '')

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="w-64 bg-background-surface border-r border-border min-h-screen flex flex-col justify-between">
      <div className="px-4 pt-8 pb-4 space-y-6">
        {/* 설비 목록 메뉴 (항상 표시) */}
        <nav className="space-y-2">
          <Link
            to="/devices"
            className={`relative flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
              isListActive
                ? 'bg-primary/10 text-primary font-medium'
                : 'text-text-secondary hover:bg-white/5 hover:text-white'
            }`}
          >
            <svg
              className="w-6 h-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <rect x="3" y="3" width="7" height="7" strokeLinecap="round" strokeLinejoin="round" />
              <rect x="14" y="3" width="7" height="7" strokeLinecap="round" strokeLinejoin="round" />
              <rect x="3" y="14" width="7" height="7" strokeLinecap="round" strokeLinejoin="round" />
              <rect x="14" y="14" width="7" height="7" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span className="text-xl">설비 목록</span>
          </Link>
        </nav>

        {/* 선택된 설비 이름 표시 */}
        {selectedDeviceName && (
          <div className="px-4 py-3 rounded-lg bg-background-main border border-border text-sm text-text-secondary">
            선택된 설비
            <div className="mt-1 text-base font-medium text-text-primary truncate">
              {selectedDeviceName}
            </div>
          </div>
        )}

        {/* 설비별 메뉴 (설비 선택 시에만 활성화) */}
        {deviceId && (
          <div>
            <nav className="space-y-2">
              {menuItems
                .filter((item) => item.subPath !== '')
                .map((item) => {
                  const path = `/devices/${deviceId}/${item.subPath}`
                  const active = isActive(item.subPath)
                  return (
                    <Link
                      key={item.subPath}
                      to={path}
                      className={`relative flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                        active
                          ? 'bg-primary/10 text-primary font-medium'
                          : 'text-text-secondary hover:bg-white/5 hover:text-white'
                      }`}
                    >
                      {active && (
                        <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-l-lg" />
                      )}
                      {item.icon}
                      <span className="text-xl">{item.label}</span>
                    </Link>
                  )
                })}
            </nav>
          </div>
        )}
      </div>

      {/* 하단 로그아웃 (사이드바 맨 아래 고정) */}
      {user && (
        <div className="p-4 border-t border-border">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center px-3 py-2 text-sm text-text-secondary hover:text-primary hover:bg-background-main rounded-lg transition-colors"
          >
            <span className="mr-2">↩</span>
            <span>로그아웃</span>
          </button>
        </div>
      )}
    </aside>
  )
}

export default Sidebar

