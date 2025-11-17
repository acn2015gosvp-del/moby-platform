/**
 * 메인 대시보드 페이지
 */

function Dashboard() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6 text-gray-800">대시보드</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">센서 상태</h2>
          <p className="text-gray-600">센서 상태 정보가 여기에 표시됩니다.</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">최근 알림</h2>
          <p className="text-gray-600">최근 알림이 여기에 표시됩니다.</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">통계</h2>
          <p className="text-gray-600">통계 정보가 여기에 표시됩니다.</p>
        </div>
      </div>
    </div>
  )
}

export default Dashboard

