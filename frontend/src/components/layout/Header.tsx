/**
 * 헤더 컴포넌트
 */

import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'

function Header() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const isActive = (path: string) => {
    return location.pathname === path
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
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

