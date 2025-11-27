# Windows IP 주소 DHCP 복원 스크립트
# 관리자 권한 필요

$InterfaceAlias = "Wi-Fi"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "IP 주소 DHCP 복원" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 관리자 권한 확인
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ 이 스크립트는 관리자 권한이 필요합니다." -ForegroundColor Red
    Write-Host "PowerShell을 관리자 권한으로 실행한 후 다시 시도하세요." -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "네트워크 인터페이스: $InterfaceAlias" -ForegroundColor Green
Write-Host ""

# 고정 IP 주소 제거
Write-Host "고정 IP 주소 제거 중..." -ForegroundColor Yellow
try {
    Remove-NetIPAddress -InterfaceAlias $InterfaceAlias -AddressFamily IPv4 -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "✅ 고정 IP 주소 제거 완료" -ForegroundColor Green
} catch {
    Write-Host "⚠️ IP 주소가 이미 제거되었거나 없습니다." -ForegroundColor Yellow
}

# 고정 게이트웨이 제거
Write-Host "고정 게이트웨이 제거 중..." -ForegroundColor Yellow
try {
    Remove-NetRoute -InterfaceAlias $InterfaceAlias -AddressFamily IPv4 -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "✅ 고정 게이트웨이 제거 완료" -ForegroundColor Green
} catch {
    Write-Host "⚠️ 게이트웨이가 이미 제거되었거나 없습니다." -ForegroundColor Yellow
}

# DHCP 활성화
Write-Host "DHCP 활성화 중..." -ForegroundColor Yellow
try {
    Set-NetIPInterface -InterfaceAlias $InterfaceAlias -Dhcp Enabled -ErrorAction Stop
    Write-Host "✅ DHCP 활성화 완료" -ForegroundColor Green
} catch {
    Write-Host "❌ DHCP 활성화 실패: $_" -ForegroundColor Red
    pause
    exit 1
}

# DNS 서버를 자동으로 설정
Write-Host "DNS 서버 자동 설정 중..." -ForegroundColor Yellow
try {
    Set-DnsClientServerAddress -InterfaceAlias $InterfaceAlias -ResetServerAddresses -ErrorAction Stop
    Write-Host "✅ DNS 서버 자동 설정 완료" -ForegroundColor Green
} catch {
    Write-Host "⚠️ DNS 서버 설정 실패: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ DHCP 복원 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 설정 확인
Write-Host "현재 네트워크 설정 확인:" -ForegroundColor Cyan
Get-NetIPConfiguration -InterfaceAlias $InterfaceAlias | Format-List

Write-Host ""
Write-Host "네트워크 연결을 확인하세요." -ForegroundColor Yellow
Write-Host ""

pause

