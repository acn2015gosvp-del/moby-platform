# Windows IP 주소 고정 설정 스크립트
# 관리자 권한 필요

# 현재 네트워크 설정
$InterfaceAlias = "Wi-Fi"
$StaticIP = "192.168.80.192"
$SubnetPrefix = 24  # 255.255.255.0
$Gateway = "192.168.80.1"
$DNS1 = "164.124.101.2"
$DNS2 = "8.8.8.8"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "IP 주소 고정 설정" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 관리자 권한 확인
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ 이 스크립트는 관리자 권한이 필요합니다." -ForegroundColor Red
    Write-Host "PowerShell을 관리자 권한으로 실행한 후 다시 시도하세요." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "방법: 시작 메뉴에서 'PowerShell' 검색 → 우클릭 → '관리자 권한으로 실행'" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "현재 네트워크 인터페이스: $InterfaceAlias" -ForegroundColor Green
Write-Host "설정할 IP 주소: $StaticIP" -ForegroundColor Green
Write-Host "서브넷 마스크: /$SubnetPrefix (255.255.255.0)" -ForegroundColor Green
Write-Host "게이트웨이: $Gateway" -ForegroundColor Green
Write-Host "DNS 서버: $DNS1, $DNS2" -ForegroundColor Green
Write-Host ""

# 인터페이스 존재 확인
$interface = Get-NetAdapter -Name $InterfaceAlias -ErrorAction SilentlyContinue
if (-not $interface) {
    Write-Host "❌ 네트워크 인터페이스 '$InterfaceAlias'를 찾을 수 없습니다." -ForegroundColor Red
    Write-Host ""
    Write-Host "사용 가능한 인터페이스 목록:" -ForegroundColor Yellow
    Get-NetAdapter | Select-Object Name, InterfaceDescription | Format-Table
    pause
    exit 1
}

Write-Host "네트워크 인터페이스 확인 완료" -ForegroundColor Green
Write-Host ""

# 기존 IP 주소 제거 (DHCP로 설정된 경우)
Write-Host "기존 IP 설정 제거 중..." -ForegroundColor Yellow
try {
    Remove-NetIPAddress -InterfaceAlias $InterfaceAlias -AddressFamily IPv4 -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "✅ 기존 IP 설정 제거 완료" -ForegroundColor Green
} catch {
    Write-Host "⚠️ 기존 IP 설정이 없거나 이미 제거되었습니다." -ForegroundColor Yellow
}

# 기존 게이트웨이 제거
Write-Host "기존 게이트웨이 설정 제거 중..." -ForegroundColor Yellow
try {
    Remove-NetRoute -InterfaceAlias $InterfaceAlias -AddressFamily IPv4 -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "✅ 기존 게이트웨이 설정 제거 완료" -ForegroundColor Green
} catch {
    Write-Host "⚠️ 기존 게이트웨이 설정이 없거나 이미 제거되었습니다." -ForegroundColor Yellow
}

# 고정 IP 주소 설정
Write-Host ""
Write-Host "고정 IP 주소 설정 중..." -ForegroundColor Yellow
try {
    New-NetIPAddress -InterfaceAlias $InterfaceAlias -IPAddress $StaticIP -PrefixLength $SubnetPrefix -DefaultGateway $Gateway -ErrorAction Stop
    Write-Host "✅ IP 주소 설정 완료: $StaticIP" -ForegroundColor Green
} catch {
    Write-Host "❌ IP 주소 설정 실패: $_" -ForegroundColor Red
    pause
    exit 1
}

# DNS 서버 설정
Write-Host "DNS 서버 설정 중..." -ForegroundColor Yellow
try {
    Set-DnsClientServerAddress -InterfaceAlias $InterfaceAlias -ServerAddresses $DNS1, $DNS2 -ErrorAction Stop
    Write-Host "✅ DNS 서버 설정 완료: $DNS1, $DNS2" -ForegroundColor Green
} catch {
    Write-Host "❌ DNS 서버 설정 실패: $_" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ IP 주소 고정 설정 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 설정 확인
Write-Host "현재 네트워크 설정 확인:" -ForegroundColor Cyan
Get-NetIPConfiguration -InterfaceAlias $InterfaceAlias | Format-List

Write-Host ""
Write-Host "네트워크 연결을 확인하세요." -ForegroundColor Yellow
Write-Host "인터넷이 연결되지 않으면 DNS 서버 주소를 확인하거나 라우터 설정을 확인하세요." -ForegroundColor Yellow
Write-Host ""

pause

