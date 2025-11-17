import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { getAlerts } from '../services/alertApi';
import type { Alert } from '../types/api';
import { FiFilter, FiCalendar, FiSearch, FiArrowUp, FiArrowDown, FiChevronLeft, FiChevronRight } from 'react-icons/fi'; // 1. 페이지네이션 아이콘 추가

// 2. 상수 정의
const ALERTS_PER_PAGE = 5; // 페이지당 알림 개수
type AlertLevel = 'info' | 'warning' | 'error' | 'critical';
const ALL_LEVELS: AlertLevel[] = ['critical', 'error', 'warning', 'info'];

const AlertsPage: React.FC = () => {
    // 3. 상태 정의
    // (모든 린팅 주석은 기능적 사용으로 인해 제거했습니다. 만약 다시 발생하면 주석을 복원하십시오.)
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [activeLevels, setActiveLevels] = useState<Set<AlertLevel>>(new Set(ALL_LEVELS));
    
    // 4. 페이지네이션 상태 추가
    const [currentPage, setCurrentPage] = useState(1);
    const [sortBy, setSortBy] = useState<'timestamp' | 'level'>('timestamp');
    const [sortDirection, setSortDirection] = useState<'desc' | 'asc'>('desc');

    // 5. API 호출 로직 (useEffect 내)
    useEffect(() => {
        const fetchAlerts = async () => {
            try {
                setLoading(true);
                const data = await getAlerts(); 
                setAlerts(data);
                setError(null);
            } catch (e) {
                console.error("Failed to fetch alerts", e);
                setError("알림 목록을 불러오는 데 실패했습니다."); 
            } finally {
                setLoading(false);
            }
        };

        fetchAlerts();
    }, []);

    // 6. 레벨 필터 토글 함수 및 정렬 핸들러 (이전과 동일)
    const handleLevelToggle = useCallback((level: AlertLevel) => {
        setActiveLevels(prevLevels => {
            const newLevels = new Set(prevLevels);
            if (newLevels.has(level)) {
                newLevels.delete(level);
            } else {
                newLevels.add(level);
            }
            return newLevels;
        });
        setCurrentPage(1); // 필터 변경 시 1페이지로 이동
    }, []);

    const handleSortChange = (key: 'timestamp' | 'level') => {
        if (sortBy === key) {
            setSortDirection(prev => (prev === 'desc' ? 'asc' : 'desc'));
        } else {
            setSortBy(key);
            setSortDirection('desc');
        }
        setCurrentPage(1); // 정렬 변경 시 1페이지로 이동
    };


    // 7. 필터링, 정렬, 페이지네이션 적용 (useMemo 로직 확장)
    const processedAlerts = useMemo(() => {
        // Step 1: 검색어 필터링
        let results = alerts;
        if (searchTerm) {
            const lowerCaseSearch = searchTerm.toLowerCase();
            results = alerts.filter(alert => 
                alert.message.toLowerCase().includes(lowerCaseSearch) ||
                alert.sensor_id.toLowerCase().includes(lowerCaseSearch)
            );
        }

        // Step 2: 레벨 필터링
        if (activeLevels.size > 0 && activeLevels.size < ALL_LEVELS.length) {
            results = results.filter(alert => activeLevels.has(alert.level));
        }

        // Step 3: 정렬 로직 적용
        const sortedResults = [...results].sort((a, b) => {
            let comparison = a[sortBy] > b[sortBy] ? 1 : a[sortBy] < b[sortBy] ? -1 : 0;
            return sortDirection === 'asc' ? comparison : -comparison;
        });
        
        return sortedResults;
    }, [alerts, searchTerm, activeLevels, sortBy, sortDirection]);
    
    // 8. 현재 페이지에 표시될 알림 계산
    const totalPages = Math.ceil(processedAlerts.length / ALERTS_PER_PAGE);
    
    const currentAlerts = useMemo(() => {
        const startIndex = (currentPage - 1) * ALERTS_PER_PAGE;
        const endIndex = startIndex + ALERTS_PER_PAGE;
        return processedAlerts.slice(startIndex, endIndex);
    }, [processedAlerts, currentPage]);


    // 9. 로딩 및 에러 상태 표시
    if (loading) {
        return <div className="text-center p-6 text-lg">알림 목록을 불러오는 중입니다...</div>;
    }

    if (error) {
        return <div className="text-center p-6 text-red-600 font-bold">오류: {error}</div>;
    }

    // 10. 페이지네이션 버튼 핸들러
    const goToPage = (page: number) => {
        if (page >= 1 && page <= totalPages) {
            setCurrentPage(page);
        }
    };


    // 11. 컴포넌트 렌더링
    return (
        <div>
            <h1 className="text-3xl font-bold mb-6 text-gray-800">알림 목록</h1>
            
            {/* 필터 및 검색 영역 */}
            <div className="bg-white shadow-lg rounded-lg p-4 mb-6">
                <div className="flex space-x-4 items-center mb-4">
                    {/* 검색 input */}
                    <div className="flex items-center space-x-2 border rounded px-3 py-1">
                        <FiSearch className="text-gray-400" />
                        <input 
                            type="text" 
                            placeholder="알림 검색" 
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="text-sm focus:ring-0 focus:border-0 outline-none" 
                        />
                    </div>
                    
                    {/* 필터 버튼 (레벨 토글 UI) */}
                    <div className="flex items-center space-x-2">
                        <FiFilter className="text-gray-400" />
                        {ALL_LEVELS.map(level => (
                            <button
                                key={level}
                                onClick={() => handleLevelToggle(level)}
                                className={`
                                    text-xs font-medium py-1 px-3 rounded-full transition 
                                    ${activeLevels.has(level) 
                                        ? 'bg-blue-600 text-white hover:bg-blue-700' 
                                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}
                                    ${level === 'critical' && activeLevels.has(level) && 'bg-red-600'}
                                `}
                            >
                                {level.toUpperCase()}
                            </button>
                        ))}
                    </div>
                    
                    {/* 정렬 버튼 */}
                    <button 
                        className="flex items-center text-sm text-gray-600 hover:text-gray-900 border rounded px-3 py-1 ml-auto"
                        onClick={() => handleSortChange('timestamp')}
                    >
                        <FiCalendar className="mr-1" /> 
                        날짜 정렬
                        {/* 정렬 방향 표시 */}
                        {sortBy === 'timestamp' && (
                            sortDirection === 'desc' 
                                ? <FiArrowDown className="ml-1 h-3 w-3" />
                                : <FiArrowUp className="ml-1 h-3 w-3" />
                        )}
                    </button>
                </div>
            </div>

            {/* 알림 목록 테이블 */}
            <div className="bg-white shadow-lg rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4">총 {processedAlerts.length}개의 필터링된 알림 (전체: {alerts.length}개)</h2>
                
                {currentAlerts.length === 0 ? (
                    <p className="text-gray-500">{searchTerm || activeLevels.size < ALL_LEVELS.length ? '필터링된 결과가 없습니다.' : '표시할 알림이 없습니다.'}</p>
                ) : (
                    <ul className="space-y-4">
                        {currentAlerts.map((alert) => (
                            <li key={alert.id} className="border-b pb-2">
                                <p className="font-medium text-gray-800">
                                    [{alert.level.toUpperCase()}] {alert.message}
                                </p>
                                <p className="text-xs text-gray-500">
                                    센서 ID: {alert.sensor_id} | 시간: {new Date(alert.timestamp).toLocaleString()}
                                </p>
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            {/* 12. 페이지네이션 컨트롤 */}
            {totalPages > 1 && (
                <div className="flex justify-center mt-6 space-x-2">
                    <button
                        onClick={() => goToPage(currentPage - 1)}
                        disabled={currentPage === 1}
                        className="p-2 border rounded-full text-gray-600 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <FiChevronLeft className="h-5 w-5" />
                    </button>

                    {/* 페이지 번호 표시 */}
                    <span className="flex items-center px-4 font-semibold text-gray-700">
                        페이지 {currentPage} / {totalPages}
                    </span>

                    <button
                        onClick={() => goToPage(currentPage + 1)}
                        disabled={currentPage === totalPages}
                        className="p-2 border rounded-full text-gray-600 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <FiChevronRight className="h-5 w-5" />
                    </button>
                </div>
            )}
        </div>
    );
};

export default AlertsPage;