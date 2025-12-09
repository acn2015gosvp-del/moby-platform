# ===========================================================
# extract_todos.ps1 - 문서에서 개선점/TODO 추출하여 통합
# 각 문서의 "개선점 / TODO" 섹션만 모아서 TODO_IMPROVEMENTS.md 생성
# ===========================================================

$ErrorActionPreference = "Stop"

# PowerShell 콘솔 인코딩을 UTF-8로 설정 (한글 깨짐 방지)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$DocsDir = "docs"
$OutputFile = Join-Path $DocsDir "TODO_IMPROVEMENTS.md"

# 주요 문서 목록
$SourceDocs = @(
    "ARCHITECTURE_OVERVIEW.md",
    "BACKEND_SERVICES_OVERVIEW.md",
    "BACKEND_SERVICES_REVIEW.md",
    "ALERT_ENGINE_DESIGN_REVIEW.md",
    "ALERT_ENGINE_REVIEW.md",
    "DATA_PIPELINE_OVERVIEW.md",
    "DATA_PIPELINE_MQTT_INFLUX_GRAFANA.md",
    "TODO_MOBY_BACKEND.md"
)

Write-Host "📋 문서에서 개선점/TODO 추출 중..."
Write-Host "----------------------------------------"

$allTodos = @()

foreach ($doc in $SourceDocs) {
    $docPath = Join-Path $DocsDir $doc
    
    if (-not (Test-Path $docPath)) {
        Write-Host "⚠️  파일 없음: $doc"
        continue
    }
    
    Write-Host "📄 처리 중: $doc"
    
    $extracted = $false
    
    # TODO_MOBY_BACKEND.md는 전체 내용 사용
    if ($doc -eq "TODO_MOBY_BACKEND.md") {
        try {
            $content = Get-Content -Path $docPath -Raw -Encoding UTF8
            if ($content) {
                $allTodos += "`n---`n## 📄 출처: $doc`n$content`n"
                $extracted = $true
            }
        }
        catch {
            Write-Host "   ❌ 파일 읽기 오류: $($_.Exception.Message)"
        }
    }
    else {
        # 개선점 섹션 추출
        try {
            $lines = Get-Content -Path $docPath -Encoding UTF8
            $inSection = $false
            $sectionLines = @()
            
            # 간단한 문자열 포함 검사 사용 (정규 표현식 인코딩 문제 방지)
            for ($i = 0; $i -lt $lines.Count; $i++) {
                $line = $lines[$i]
                
                if (-not $inSection) {
                    # 섹션 시작 찾기 - 문자열 포함 검사
                    $lineLower = $line.ToLower()
                    if (($line -match "^##\s*" -or $line -match "^#\s+") -and 
                        ($lineLower -like "*개선*" -or 
                         $lineLower -like "*todo*" -or 
                         $lineLower -like "*improvement*")) {
                        $inSection = $true
                        $sectionLines = @($line)
                    }
                }
                elseif ($inSection) {
                    # 다음 주요 섹션(## 숫자) 시작하면 종료
                    if ($line -match "^##\s+\d+") {
                        $lineLower = $line.ToLower()
                        # 개선/TODO 관련이 아니면 종료
                        if ($lineLower -notlike "*개선*" -and 
                            $lineLower -notlike "*todo*" -and 
                            $lineLower -notlike "*improvement*") {
                            break
                        }
                    }
                    $sectionLines += $line
                }
            }
            
            if ($sectionLines.Count -gt 0) {
                $section = $sectionLines -join "`n"
                if ($section.Trim().Length -gt 20) {
                    $allTodos += "`n---`n## 📄 출처: $doc`n$section`n"
                    $extracted = $true
                    Write-Host "   ✅ 섹션 추출 완료"
                }
            }
        }
        catch {
            Write-Host "   ❌ 파일 읽기 오류: $($_.Exception.Message)"
        }
    }
    
    if (-not $extracted) {
        Write-Host "   ℹ️  개선점 섹션을 찾을 수 없음"
    }
}

# 추출된 내용이 있는지 확인
if ($allTodos.Count -eq 0 -or ($allTodos -join "").Trim().Length -eq 0) {
    Write-Host "`n⚠️  추출된 개선점/TODO 섹션이 없습니다."
    Write-Host "   문서들을 확인하거나 수동으로 정리해주세요."
    exit 1
}

# Gemini CLI를 사용하여 정리된 TODO 문서 생성
Write-Host "`n🤖 Gemini CLI로 통합 TODO 문서 생성 중..."
Write-Host "----------------------------------------"

$Prompt = @"
다음은 MOBY 플랫폼의 여러 문서에서 추출한 개선점과 TODO 항목들입니다.
이들을 카테고리별로 정리하고, 중복을 제거하며, 우선순위를 고려하여 체계적으로 정리해주세요.

출처별로 구분되어 있으므로, 같은 내용이 중복되어 있을 수 있습니다.
중복은 제거하되, 출처 정보는 유지해주세요.

형식:
- 카테고리별로 섹션을 나누기 (예: 아키텍처, 백엔드 서비스, Alert Engine, 데이터 파이프라인, 테스트 등)
- 각 항목은 체크박스 형식으로 ([ ])
- 출처 문서명을 각 항목 옆에 표시 (예: [ARCHITECTURE_OVERVIEW.md])
- 우선순위가 높은 항목은 맨 위로 배치

추출된 내용:
$($allTodos -join "`n`n")

IMPORTANT: Do NOT use any file writing tools (like write_file) or shell command tools (like run_shell_command). Only output the organized TODO document content as markdown text.
"@

try {
    $result = gemini "$Prompt" --output-format text 2>&1
    
    # 에러 메시지만 포함된 경우 확인
    if ($result -match "Error|오류|error" -and $result.Length -lt 200) {
        Write-Host "⚠️  Gemini CLI에서 오류가 발생했을 수 있습니다."
        Write-Host "   결과: $result"
        Write-Host "`n⚠️  추출된 원본 내용을 그대로 저장합니다."
        
        # 원본 내용 저장
        $header = @"
# MOBY Platform 개선 포인트 통합 TODO

> 이 문서는 여러 아키텍처/리뷰 문서에서 추출한 개선점과 TODO 항목입니다.
> Gemini CLI 정리 과정에서 오류가 발생하여 원본 추출 내용을 그대로 표시합니다.
> 
> **최종 업데이트**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
> 
> **생성 스크립트**: `./scripts/extract_todos.ps1`

---

"@
        $finalContent = $header + "`n" + ($allTodos -join "`n`n")
    }
    else {
        # 정상 응답인 경우
        $header = @"
# MOBY Platform 개선 포인트 통합 TODO

> 이 문서는 여러 아키텍처/리뷰 문서에서 추출한 개선점과 TODO 항목을 통합하여 정리한 것입니다.
> 
> **최종 업데이트**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
> 
> **생성 스크립트**: `./scripts/extract_todos.ps1`

---

"@
        $finalContent = $header + "`n" + $result
    }
    
    Set-Content -Path $OutputFile -Value $finalContent -Encoding UTF8
    
    Write-Host "✅ TODO 문서 생성 완료!"
    Write-Host "📌 저장 위치: $OutputFile"
}
catch {
    Write-Host "❌ 오류 발생: $($_.Exception.Message)"
    Write-Host "⚠️  추출된 원본 내용을 저장합니다."
    
    # 에러가 발생해도 추출된 내용은 저장
    $header = @"
# MOBY Platform 개선 포인트 통합 TODO

> 이 문서는 여러 아키텍처/리뷰 문서에서 추출한 개선점과 TODO 항목입니다.
> Gemini CLI 정리 과정에서 오류가 발생하여 원본 추출 내용을 그대로 표시합니다.
> 
> **최종 업데이트**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
> 
> **생성 스크립트**: `./scripts/extract_todos.ps1`
> 
> **오류**: $($_.Exception.Message)

---

"@
    $finalContent = $header + "`n" + ($allTodos -join "`n`n")
    Set-Content -Path $OutputFile -Value $finalContent -Encoding UTF8
    Write-Host "📌 저장 위치: $OutputFile"
}

Write-Host ""
Write-Host "✨ 스크립트 실행 완료"
