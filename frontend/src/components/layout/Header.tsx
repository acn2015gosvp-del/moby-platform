/**
 * 헤더 컴포넌트
 * 로고와 설비 선택 드롭다운 표시
 */

import { Link, useLocation } from 'react-router-dom'
import { useDeviceContext } from '@/context/DeviceContext'
import MobyLogo from '@/components/common/MobyLogo'
import { useTheme } from '@/context/ThemeContext'
import { useAlertMute } from '@/context/AlertMuteContext'

function Header() {
  const location = useLocation()
  const { devices, selectedDeviceId, setSelectedDeviceId, loading: devicesLoading } = useDeviceContext()
  const { theme, toggleTheme } = useTheme()
  const { isMuted, toggleMute } = useAlertMute()

  // 설비 목록 페이지에서는 드롭다운 숨김
  const isDeviceListPage = location.pathname === '/' || location.pathname === '/devices'
  const showDeviceSwitcher = !isDeviceListPage && devices.length > 0

  return (
    <header className="bg-background-surface border-b border-border w-full">
      <div className="w-full px-4">
        <div className="flex items-center justify-between h-20">
          {/* 로고 + MOBY 텍스트 영역 */}
          <div className="flex items-center space-x-8 flex-1">
            <Link to="/" className="flex items-center space-x-4">
              <div className="flex items-center mt-8">
                <MobyLogo
                  width={70}
                  height={106}
                  fill="currentColor"
                  className="text-primary"
                />
              </div>
              <h1 className="text-[32px] leading-none font-bold text-primary tracking-wide">
                MOBY
              </h1>
            </Link>
          </div>

          <div className="flex items-center gap-4">
            {/* 설비 선택 드롭다운 */}
            {showDeviceSwitcher && (
              <div className="w-72 flex-shrink-0">
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
                  className="w-full px-4 py-2 border border-border rounded-lg bg-background-main text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-background-surface disabled:text-text-secondary disabled:cursor-not-allowed"
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

            {/* 알림 음소거 토글 */}
            <button
              type="button"
              onClick={toggleMute}
              className={`p-2 rounded-lg border transition-colors ${
                isMuted
                  ? 'border-danger bg-danger/10 text-danger'
                  : 'border-border bg-background-main text-text-secondary hover:text-primary hover:border-primary'
              }`}
              title={isMuted ? '알림 효과 켜기' : '알림 효과 끄기'}
            >
              {isMuted ? (
                // 음소거 아이콘 (빨간색)
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="w-5 h-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.617.793L4.383 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.383l4-3.617a1 1 0 011.617.793zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                // 알림 아이콘
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="w-5 h-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
                </svg>
              )}
            </button>

            {/* 다크 모드 토글 */}
            <button
              type="button"
              onClick={toggleTheme}
              className="p-2 rounded-lg border border-border bg-background-main text-text-secondary hover:text-primary hover:border-primary transition-colors"
              title={theme === 'dark' ? '라이트 모드' : '다크 모드'}
            >
              {theme === 'dark' ? (
                // 해 아이콘 (라이트 모드로 전환)
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="w-5 h-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                // 달 아이콘 (다크 모드로 전환)
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="w-5 h-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header

