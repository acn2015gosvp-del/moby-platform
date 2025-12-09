# ================================================
#  gen_docs.ps1 - Gemini CLI 문서 자동 생성 스크립트
# ================================================
param(
    [string]$Prompt
)

if (-not $Prompt) {
    Write-Host "❌ Prompt가 필요합니다."
    Write-Host "예: ./scripts/gen_docs.ps1 '전체 아키텍처 문서 작성해줘'"
    exit 1
}

$DocsDir = "docs"
if (-not (Test-Path $DocsDir)) {
    New-Item -ItemType Directory -Path $DocsDir | Out-Null
}

$Timestamp = (Get-Date -Format "yyyyMMdd_HHmmss")
$OutputFile = "$DocsDir/GEMINI_DOC_$Timestamp.md"

Write-Host "📄 문서를 생성 중... (Gemini CLI 실행)"
Write-Host "----------------------------------------"

# Gemini CLI에 파일 쓰기 도구 사용하지 말고 출력만 생성하도록 지시
# (write_file 도구가 등록되지 않은 문제 해결)
$EnhancedPrompt = "$Prompt`n`nIMPORTANT: Do NOT use any file writing tools (like write_file). Only output the document content as text. The script will automatically save it to a file."

# Gemini CLI 실행 후 결과 캡처
# --output-format text를 명시적으로 지정
$Result = gemini "$EnhancedPrompt" --output-format text 2>&1

# 에러가 있으면 표시하되, 정상 출력은 파일로 저장
if ($LASTEXITCODE -eq 0 -and $Result) {
    Set-Content -Path $OutputFile -Value $Result -Encoding UTF8
    Write-Host "✅ 문서 생성 완료!"
    Write-Host "📌 저장 위치: $OutputFile"
} else {
    Write-Host "⚠️ 경고: 일부 오류가 발생했지만 출력을 저장했습니다."
    if ($Result) {
        Set-Content -Path $OutputFile -Value $Result -Encoding UTF8
        Write-Host "📌 저장 위치: $OutputFile"
    }
}
