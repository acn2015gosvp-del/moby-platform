/**
 * 라우터 설정
 */

import { createBrowserRouter } from 'react-router-dom'
import App from './App'
import Dashboard from './pages/Dashboard'
import Alerts from './pages/Alerts'
import Sensors from './pages/Sensors'
import Login from './pages/Login'
import Register from './pages/Register'
import ProtectedRoute from './components/auth/ProtectedRoute'

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/register',
    element: <Register />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <App />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: 'alerts',
        element: <Alerts />,
      },
      {
        path: 'sensors',
        element: <Sensors />,
      },
    ],
  },
])

