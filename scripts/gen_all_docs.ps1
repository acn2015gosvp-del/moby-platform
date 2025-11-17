# ===========================================================
# gen_all_docs.ps1 - MOBY 전체 문서 자동 생성 스크립트
# Gemini CLI로 주요 아키텍처/리뷰 문서를 한번에 생성
# ===========================================================

$ErrorActionPreference = "Stop"

# 출력 디렉토리 확인
$DocsDir = "docs"
if (-not (Test-Path $DocsDir)) {
    New-Item -ItemType Directory -Path $DocsDir | Out-Null
}

# 생성할 문서 목록
$tasks = @(
    @{
        file = "ARCHITECTURE_OVERVIEW.md"
        prompt = "MOBY 플랫폼의 전체 시스템 아키텍처 문서를 생성해줘. 구성 요소, 데이터 흐름, 백엔드/프론트엔드까지 모두 포함해서 전체 아키텍처 설명."
    },
    @{
        file = "BACKEND_SERVICES_REVIEW.md"
        prompt = "backend/api/services 전체 구조를 설명하고 개선점을 제안해줘. 모듈 책임, 디렉토리 구조, 관심사 분리 기준 등을 포함."
    },
    @{
        file = "ALERT_ENGINE_REVIEW.md"
        prompt = "alert_engine.py + anomaly_vector_service.py 전체 구조를 분석하고 리팩토링 개선점을 제안해줘. 문제점과 문서화 확인, 테스트 케이스도 포함."
    },
    @{
        file = "DATA_PIPELINE_OVERVIEW.md"
        prompt = "센서 → MQTT → FastAPI → InfluxDB → Grafana 전체 데이터 파이프라인을 아키텍처 문서 형태로 설명해줘."
    }
)

# 실행
Write-Host "🚀 Gemini CLI를 사용하여 전체 문서를 자동 생성합니다..."
Write-Host "----------------------------------------"

foreach ($task in $tasks) {
    $filePath = Join-Path $DocsDir $task.file
    Write-Host "`n📄 생성 중: $($task.file)"

    try {
        # Gemini CLI에 파일 쓰기 도구 사용하지 말고 출력만 생성하도록 지시
        # (write_file, run_shell_command 도구가 등록되지 않은 문제 해결)
        $EnhancedPrompt = "$($task.prompt)`n`nIMPORTANT: Do NOT use any file writing tools (like write_file) or shell command tools (like run_shell_command). Only output the document content as text. The script will automatically save it to a file."
        
        # Gemini CLI 실행 후 결과 캡처
        $output = gemini "$EnhancedPrompt" --output-format text 2>&1
        
        # 에러가 있어도 출력이 있으면 파일로 저장
        if ($output) {
            Set-Content -Path $filePath -Value $output -Encoding UTF8
            Write-Host "✅ 완료 → $filePath"
        } else {
            Write-Host "⚠️ 경고: 출력이 없습니다."
        }
    }
    catch {
        Write-Host "❌ 오류 발생: $($_.Exception.Message)"
    }
}

Write-Host "`n🎉 모든 문서 생성 완료!"

