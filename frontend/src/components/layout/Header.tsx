/**
 * 헤더 컴포넌트
 * 설비 선택 드롭다운 포함
 */

import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { useDeviceContext } from '@/context/DeviceContext'

function Header() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const { devices, selectedDevice, selectedDeviceId, setSelectedDeviceId, loading: devicesLoading } = useDeviceContext()

  const isActive = (path: string) => {
    return location.pathname === path
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // 설비 목록 페이지에서는 드롭다운 숨김
  const isDeviceListPage = location.pathname === '/' || location.pathname === '/devices'
  const showDeviceSwitcher = !isDeviceListPage && devices.length > 0

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <h1 className="text-2xl font-bold text-blue-600">MOBY</h1>
            <span className="text-sm text-gray-500">Platform</span>
          </Link>

          {/* 설비 선택 드롭다운 */}
          {showDeviceSwitcher && (
            <div className="flex-1 max-w-xs mx-8">
              <label htmlFor="device-select" className="sr-only">
                설비 선택
              </label>
              <select
                id="device-select"
                value={selectedDeviceId || ''}
                onChange={(e) => {
                  const deviceId = e.target.value
                  setSelectedDeviceId(deviceId || null)
                }}
                disabled={devicesLoading}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
              >
                <option value="">설비를 선택하세요</option>
                {devices.map((device) => (
                  <option key={device.device_id} value={device.device_id}>
                    {device.name} {device.category ? `(${device.category})` : ''}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* User Menu */}
          <div className="flex items-center space-x-4">
            {user && (
              <>
                <span className="text-sm text-gray-700">{user.username}</span>
                <button
                  onClick={handleLogout}
                  className="px-3 py-1 text-sm text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
                >
                  로그아웃
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header

