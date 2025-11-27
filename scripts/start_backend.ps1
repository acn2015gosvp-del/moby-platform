# FastAPI 백엔드 서버 시작 스크립트
# --host 0.0.0.0 옵션을 사용하여 외부 접속 허용

Write-Host "🚀 FastAPI 백엔드 서버를 시작합니다..." -ForegroundColor Green
Write-Host "📍 호스트: 0.0.0.0 (모든 네트워크 인터페이스에서 접속 가능)" -ForegroundColor Yellow
Write-Host "📍 포트: 8000" -ForegroundColor Yellow
Write-Host ""

# 방화벽 규칙 확인
$firewallRule = Get-NetFirewallRule -DisplayName "FastAPI Port 8000" -ErrorAction SilentlyContinue
if (-not $firewallRule) {
    Write-Host "⚠️  방화벽 규칙이 없습니다. 8000번 포트를 열어주세요." -ForegroundColor Yellow
    Write-Host "   다음 명령어를 실행하세요:" -ForegroundColor Yellow
    Write-Host "   netsh advfirewall firewall add rule name=`"FastAPI Port 8000`" dir=in action=allow protocol=TCP localport=8000" -ForegroundColor Cyan
    Write-Host ""
}

# 서버 시작
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

