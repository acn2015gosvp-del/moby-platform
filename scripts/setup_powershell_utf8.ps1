# PowerShell UTF-8 인코딩 설정 스크립트
# 이 스크립트를 실행하면 PowerShell의 기본 출력 인코딩이 UTF-8로 설정됩니다.

Write-Host "PowerShell UTF-8 인코딩 설정" -ForegroundColor Cyan
Write-Host "=" * 50

# 현재 인코딩 확인
Write-Host "`n현재 인코딩:" -ForegroundColor Yellow
Write-Host "  OutputEncoding: $([Console]::OutputEncoding.EncodingName)"
Write-Host "  InputEncoding: $([Console]::InputEncoding.EncodingName)"

# UTF-8로 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'

Write-Host "`n✅ UTF-8 인코딩으로 설정되었습니다." -ForegroundColor Green
Write-Host "`n참고: 이 설정은 현재 세션에만 적용됩니다." -ForegroundColor Yellow
Write-Host "영구적으로 적용하려면 PowerShell 프로필에 다음을 추가하세요:" -ForegroundColor Yellow
Write-Host ""
Write-Host '  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8' -ForegroundColor Cyan
Write-Host '  [Console]::InputEncoding = [System.Text.Encoding]::UTF8' -ForegroundColor Cyan
Write-Host '  $PSDefaultParameterValues[''*:Encoding''] = ''utf8''' -ForegroundColor Cyan
Write-Host ""

# PowerShell 프로필 경로 확인
$profilePath = $PROFILE.CurrentUserAllHosts
Write-Host "PowerShell 프로필 경로: $profilePath" -ForegroundColor Cyan

if (-not (Test-Path $profilePath)) {
    Write-Host "`n프로필 파일이 없습니다. 생성할까요? (Y/N)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq 'Y' -or $response -eq 'y') {
        New-Item -Path $profilePath -ItemType File -Force | Out-Null
        Add-Content -Path $profilePath -Value @"
# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
`$PSDefaultParameterValues['*:Encoding'] = 'utf8'
"@
        Write-Host "✅ 프로필 파일이 생성되었습니다." -ForegroundColor Green
    }
} else {
    Write-Host "`n프로필 파일이 이미 존재합니다." -ForegroundColor Yellow
    Write-Host "수동으로 UTF-8 설정을 추가하세요." -ForegroundColor Yellow
}

