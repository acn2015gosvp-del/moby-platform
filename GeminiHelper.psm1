# ===========================================================
# GeminiHelper.psm1 - Gemini API 호출 공통 모듈
# 모든 스크립트에서 Import-Module로 불러와서 사용
# ===========================================================

# Gemini CLI 설정에서 API 키 가져오기
function Get-GeminiApiKey {
    <#
    .SYNOPSIS
    Gemini CLI 설정에서 API 키를 가져옵니다.
    
    .OUTPUTS
    API 키 문자열 또는 $null
    #>
    
    $configPaths = @(
        "$env:USERPROFILE\.gemini\config.json",
        "$env:APPDATA\.gemini\config.json",
        "$env:LOCALAPPDATA\.gemini\config.json"
    )
    
    foreach ($configPath in $configPaths) {
        if (Test-Path $configPath) {
            try {
                $config = Get-Content $configPath -Raw | ConvertFrom-Json
                if ($config.apiKey) {
                    return $config.apiKey
                }
            }
            catch {
                # 다음 경로 시도
                continue
            }
        }
    }
    
    return $null
}

# Gemini API 직접 호출 (Agent 모드 우회)
function Invoke-GeminiApi {
    <#
    .SYNOPSIS
    Gemini API를 직접 호출하여 텍스트 생성
    
    .PARAMETER Prompt
    생성할 텍스트의 프롬프트
    
    .PARAMETER MaxRetries
    재시도 횟수 (기본값: 3)
    
    .PARAMETER DelaySeconds
    재시도 간 대기 시간 (기본값: 5)
    
    .PARAMETER Model
    사용할 모델 (기본값: gemini-1.5-flash)
    
    .PARAMETER Temperature
    생성 온도 (기본값: 0.7)
    
    .PARAMETER MaxTokens
    최대 출력 토큰 (기본값: 8192)
    
    .OUTPUTS
    해시테이블 { Success = $true/$false, Result = "텍스트" 또는 Error = "에러메시지" }
    
    .EXAMPLE
    $result = Invoke-GeminiApi -Prompt "2+2는?"
    if ($result.Success) {
        Write-Host $result.Result
    }
    #>
    
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [string]$Prompt,
        
        [Parameter(Mandatory = $false)]
        [int]$MaxRetries = 3,
        
        [Parameter(Mandatory = $false)]
        [int]$DelaySeconds = 5,
        
        [Parameter(Mandatory = $false)]
        [string]$Model = "gemini-1.5-flash",
        
        [Parameter(Mandatory = $false)]
        [double]$Temperature = 0.7,
        
        [Parameter(Mandatory = $false)]
        [int]$MaxTokens = 8192
    )
    
    # API 키 확인
    $apiKey = Get-GeminiApiKey
    if (-not $apiKey) {
        return @{
            Success = $false
            Error = "Gemini API 키를 찾을 수 없습니다. 'gemini config' 명령으로 API 키를 설정하세요."
        }
    }
    
    $endpoint = "https://generativelanguage.googleapis.com/v1beta/models/${Model}:generateContent"
    
    for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
        try {
            if ($MaxRetries -gt 1) {
                Write-Verbose "시도 $attempt/$MaxRetries..."
            }
            
            # 요청 본문 구성
            $body = @{
                contents = @(
                    @{
                        parts = @(
                            @{
                                text = $Prompt
                            }
                        )
                    }
                )
                generationConfig = @{
                    temperature = $Temperature
                    topK = 40
                    topP = 0.95
                    maxOutputTokens = $MaxTokens
                }
            } | ConvertTo-Json -Depth 10
            
            # API 호출
            $response = Invoke-RestMethod `
                -Uri "$endpoint`?key=$apiKey" `
                -Method Post `
                -ContentType "application/json; charset=utf-8" `
                -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) `
                -TimeoutSec 60 `
                -ErrorAction Stop
            
            # 응답 추출
            if ($response.candidates -and 
                $response.candidates[0].content.parts -and 
                $response.candidates[0].content.parts[0].text) {
                
                $resultText = $response.candidates[0].content.parts[0].text
                
                if ($MaxRetries -gt 1) {
                    Write-Verbose "성공! (응답 길이: $($resultText.Length) 문자)"
                }
                
                return @{
                    Success = $true
                    Result = $resultText
                }
            }
            else {
                throw "Invalid API response structure"
            }
        }
        catch {
            $errorMsg = $_.Exception.Message
            
            if ($MaxRetries -gt 1) {
                Write-Verbose "시도 $attempt 실패: $errorMsg"
            }
            
            if ($attempt -lt $MaxRetries) {
                if ($MaxRetries -gt 1) {
                    Write-Verbose "$DelaySeconds 초 후 재시도..."
                }
                Start-Sleep -Seconds $DelaySeconds
            }
            else {
                return @{
                    Success = $false
                    Error = $errorMsg
                }
            }
        }
    }
}

# Gemini에게 문서 생성 요청 (간편 함수)
function New-GeminiDocument {
    <#
    .SYNOPSIS
    Gemini API를 사용하여 문서 생성
    
    .PARAMETER Topic
    생성할 문서의 주제
    
    .PARAMETER Instructions
    추가 생성 지시사항
    
    .PARAMETER OutputPath
    저장할 파일 경로 (선택사항)
    
    .OUTPUTS
    생성된 문서 텍스트 또는 $null (실패 시)
    
    .EXAMPLE
    $doc = New-GeminiDocument -Topic "Python 기초" -Instructions "초보자용으로 작성"
    
    .EXAMPLE
    New-GeminiDocument -Topic "API 문서" -OutputPath "docs/api.md"
    #>
    
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [string]$Topic,
        
        [Parameter(Mandatory = $false)]
        [string]$Instructions = "",
        
        [Parameter(Mandatory = $false)]
        [string]$OutputPath = ""
    )
    
    # 프롬프트 구성
    $prompt = "주제: $Topic`n`n"
    if ($Instructions) {
        $prompt += "지시사항: $Instructions`n`n"
    }
    $prompt += "위 주제에 대한 상세하고 전문적인 문서를 작성해주세요."
    
    # API 호출
    $result = Invoke-GeminiApi -Prompt $prompt
    
    if ($result.Success) {
        # 파일로 저장 (OutputPath가 지정된 경우)
        if ($OutputPath) {
            $outputDir = Split-Path -Parent $OutputPath
            if ($outputDir -and -not (Test-Path $outputDir)) {
                New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
            }
            
            Set-Content -Path $OutputPath -Value $result.Result -Encoding UTF8
            Write-Verbose "문서 저장: $OutputPath"
        }
        
        return $result.Result
    }
    else {
        Write-Error "문서 생성 실패: $($result.Error)"
        return $null
    }
}

# 함수 Export
Export-ModuleMember -Function @(
    'Get-GeminiApiKey',
    'Invoke-GeminiApi',
    'New-GeminiDocument'
)
