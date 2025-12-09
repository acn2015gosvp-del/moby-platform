# 프론트엔드 400 오류 진단 스크립트

Write-Host "=== 프론트엔드 400 오류 진단 ===" -ForegroundColor Yellow
Write-Host ""

# 1. 포트 확인
Write-Host "1. 포트 5173 상태:" -ForegroundColor Cyan
$port5173 = netstat -ano | Select-String ":5173"
if ($port5173) {
    Write-Host "   ✅ 포트 5173이 열려있습니다" -ForegroundColor Green
    $port5173 | Select-Object -First 3
} else {
    Write-Host "   ❌ 포트 5173이 열려있지 않습니다" -ForegroundColor Red
    Write-Host "   → 프론트엔드 서버를 시작하세요: cd frontend && npm run dev" -ForegroundColor Yellow
}

Write-Host ""

# 2. 백엔드 포트 확인
Write-Host "2. 백엔드 포트 8000 상태:" -ForegroundColor Cyan
$port8000 = netstat -ano | Select-String ":8000"
if ($port8000) {
    Write-Host "   ✅ 포트 8000이 열려있습니다" -ForegroundColor Green
} else {
    Write-Host "   ❌ 포트 8000이 열려있지 않습니다" -ForegroundColor Red
    Write-Host "   → 백엔드 서버를 시작하세요" -ForegroundColor Yellow
}

Write-Host ""

# 3. 프론트엔드 서버 응답 확인
Write-Host "3. 프론트엔드 서버 응답 확인:" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    Write-Host "   ✅ 프론트엔드 서버 응답: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ 프론트엔드 서버 응답 실패: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# 4. 백엔드 API 응답 확인
Write-Host "4. 백엔드 API 응답 확인:" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    Write-Host "   ✅ 백엔드 API 응답: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️ 백엔드 API 응답 실패 (정상일 수 있음): $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== 진단 완료 ===" -ForegroundColor Yellow
Write-Host ""
Write-Host "💡 해결 방법:" -ForegroundColor Cyan
Write-Host "   1. 프론트엔드 서버 재시작: cd frontend && npm run dev" -ForegroundColor White
Write-Host "   2. 브라우저 캐시 삭제: Ctrl+Shift+Delete" -ForegroundColor White
Write-Host "   3. 하드 리프레시: Ctrl+Shift+R" -ForegroundColor White
Write-Host "   4. 브라우저 콘솔 확인: F12 > Console 탭" -ForegroundColor White

