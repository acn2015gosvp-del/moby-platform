/**
 * 라우터 설정
 */

import { createBrowserRouter } from 'react-router-dom'
import App from './App'
import Dashboard from './pages/Dashboard'
import Alerts from './pages/Alerts'
import Sensors from './pages/Sensors'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
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

