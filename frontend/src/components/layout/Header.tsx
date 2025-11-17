/**
 * 헤더 컴포넌트
 */

import { Link, useLocation } from 'react-router-dom'

function Header() {
  const location = useLocation()

  const isActive = (path: string) => {
    return location.pathname === path
  }

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <h1 className="text-2xl font-bold text-blue-600">MOBY</h1>
            <span className="text-sm text-gray-500">Platform</span>
          </Link>

          {/* Navigation */}
          <nav className="flex items-center space-x-6">
            <Link
              to="/"
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/')
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              대시보드
            </Link>
            <Link
              to="/alerts"
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/alerts')
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              알림
            </Link>
            <Link
              to="/sensors"
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/sensors')
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              센서
            </Link>
          </nav>

          {/* User Menu (향후 구현) */}
          <div className="flex items-center space-x-4">
            <div className="w-8 h-8 bg-gray-300 rounded-full"></div>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header

