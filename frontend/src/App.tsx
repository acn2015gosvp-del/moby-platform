import { Outlet } from 'react-router-dom'
import MainLayout from './components/layout/MainLayout'
import { DeviceProvider } from './context/DeviceContext'
import './App.css'

function App() {
  return (
    <DeviceProvider>
      <MainLayout>
        <Outlet />
      </MainLayout>
    </DeviceProvider>
  )
}

export default App
