# Mosquitto 설정 파일 업데이트 스크립트
# 관리자 권한으로 실행 필요

$configPath = "C:\Program Files\mosquitto\mosquitto.conf"

# 관리자 권한 확인
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "이 스크립트는 관리자 권한이 필요합니다." -ForegroundColor Red
    Write-Host "PowerShell을 관리자 권한으로 실행한 후 다시 시도하세요." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "또는 다음 명령을 관리자 권한 PowerShell에서 실행하세요:" -ForegroundColor Yellow
    Write-Host "  Add-Content -Path `"$configPath`" -Value `"`nlistener 1883`" -Encoding UTF8" -ForegroundColor Cyan
    Write-Host "  Add-Content -Path `"$configPath`" -Value `"allow_anonymous true`" -Encoding UTF8" -ForegroundColor Cyan
    exit 1
}

# 파일 존재 확인
if (-not (Test-Path $configPath)) {
    Write-Host "설정 파일을 찾을 수 없습니다: $configPath" -ForegroundColor Red
    exit 1
}

# 현재 내용 읽기
$content = Get-Content $configPath -Raw

# listener 1883 추가
if ($content -notmatch "listener 1883") {
    Add-Content -Path $configPath -Value "`nlistener 1883" -Encoding UTF8
    Write-Host "✓ Added: listener 1883" -ForegroundColor Green
} else {
    Write-Host "○ Already exists: listener 1883" -ForegroundColor Yellow
}

# allow_anonymous true 추가
if ($content -notmatch "allow_anonymous true") {
    Add-Content -Path $configPath -Value "allow_anonymous true" -Encoding UTF8
    Write-Host "✓ Added: allow_anonymous true" -ForegroundColor Green
} else {
    Write-Host "○ Already exists: allow_anonymous true" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "설정 파일 업데이트 완료: $configPath" -ForegroundColor Green
Write-Host "Mosquitto 서비스를 재시작하세요." -ForegroundColor Yellow

