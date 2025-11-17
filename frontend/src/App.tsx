import { Routes, Route } from 'react-router-dom';
import MainLayout from './components/MainLayout';

// (임시) 렌더링될 페이지 컴포넌트
const DashboardPage = () => <div>대시보드 페이지</div>;
const AlertsPage = () => <div>알림 목록 페이지</div>;

function App() {
  return (
    <Routes>
      {/* MainLayout을 부모 Route로 사용합니다.
        이 안에 중첩된 Route(DashboardPage, AlertsPage)들은
        MainLayout의 <Outlet /> 위치에 렌더링됩니다.
      */}
      <Route path="/" element={<MainLayout />}>
        {/* path="/" (홈) 경로일 때 <Outlet>에 DashboardPage를 표시 
          'index' prop은 부모의 경로와 정확히 일치할 때를 의미합니다.
        */}
        <Route index element={<DashboardPage />} />

        {/* path="/alerts" 경로일 때 <Outlet>에 AlertsPage를 표시 */}
        <Route path="alerts" element={<AlertsPage />} />

        {/* (향후 다른 페이지들 추가...) */}
      </Route>

      {/* (로그인 페이지 등 레이아웃이 없는 페이지는 여기에 별도 추가) */}
    </Routes>
  );
}

export default App;