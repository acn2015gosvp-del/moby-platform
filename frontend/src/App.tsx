import { Routes, Route } from 'react-router-dom';
import MainLayout from './components/MainLayout';
// useToast와 ToastProvider는 ToastContext.tsx에서 임포트되어야 합니다.
import { useToast, ToastProvider } from './context/ToastContext'; 
// 1. 새로 생성한 AlertPage 컴포넌트를 import 합니다.
import AlertsPage from './pages/AlertsPage'; 

// 렌더링될 페이지 컴포넌트

const DashboardPage = () => {
    const { showToast } = useToast(); 

    // 토스트 테스트를 위한 임시 버튼이 있는 대시보드 페이지
    return (
        <div className="p-6">
            <h1 className="text-3xl font-bold mb-4">대시보드</h1>
            <p className="text-gray-600">주요 센서 데이터를 실시간으로 모니터링합니다.</p>
            <div className="mt-4 space-x-2">
                <button
                    onClick={() => showToast('새로운 알림이 성공적으로 전송되었습니다.')}
                    className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded"
                >
                    Success Toast
                </button>
                <button
                    onClick={() => showToast( '데이터 파이프라인에 오류가 감지되었습니다.', 'critical', 7000)}
                    className="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded"
                >
                    Error Toast
                </button>
            </div>
        </div>
    );
};

// 2. AlertsPage의 임시 정의는 삭제되었습니다.

function App() {
    return (
        <ToastProvider> 
            <Routes>
                <Route path="/" element={<MainLayout />}>
                    <Route index element={<DashboardPage />} />
                    
                    {/* 3. 새로 import한 AlertsPage를 라우터에 연결합니다. */}
                    <Route path="alerts" element={<AlertsPage />} /> 
                </Route>
            </Routes>
        </ToastProvider> 
    );
}

export default App;