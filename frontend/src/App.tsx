import { Routes, Route } from 'react-router-dom';
import MainLayout from './components/MainLayout';
import AlertToast from './components/AlertToast'; // 작업 4: 토스트 import

// (임시) 렌더링될 페이지 컴포넌트

// 작업 4: 테스트를 위해 대시보드 페이지에 토스트 예제 추가
const DashboardPage = () => (
  <div>
    대시보드 페이지
    
    {/* 임시 토스트 추가 (테스트용) */}
    <div className="mt-4 space-y-2">
      <AlertToast
        level="info"
        message="새로운 정보가 감지되었습니다."
        onClose={() => alert('닫기 클릭!')}
      />
      <AlertToast
        level="warning"
        message="센서 임계값에 근접했습니다."
        onClose={() => alert('닫기 클릭!')}
      />
      <AlertToast
        level="error"
        message="센서 연결이 끊어졌습니다."
        onClose={() => alert('닫기 클릭!')}
      />
      <AlertToast
        level="critical"
        message="시스템 과부하 발생. 즉시 점검 필요."
        onClose={() => alert('닫기 클릭!')}
      />
    </div>
  </div>
);

const AlertsPage = () => <div>알림 목록 페이지</div>;

// 작업 3: MainLayout 기반의 라우팅 구조
function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        {/* '/' 경로일 때 DashboardPage를 <Outlet>에 표시 */}
        <Route index element={<DashboardPage />} />

        {/* '/alerts' 경로일 때 AlertsPage를 <Outlet>에 표시 */}
        <Route path="alerts" element={<AlertsPage />} />
      </Route>
    </Routes>
  );
}

export default App;