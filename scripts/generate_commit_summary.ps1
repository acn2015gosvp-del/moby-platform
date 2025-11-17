# 커밋 요약 생성 스크립트 (PowerShell)
# 사용법: .\scripts\generate_commit_summary.ps1

param(
    [string]$CommitHash = "HEAD",
    [string]$OutputFile = "COMMIT_SUMMARY.md"
)

Write-Host "📝 커밋 요약 생성 중..." -ForegroundColor Cyan

# 최근 커밋 정보 가져오기
$commitInfo = git log -1 --pretty=format:"%H|%an|%ae|%ad|%s|%b" --date=iso $CommitHash
$commitParts = $commitInfo -split '\|'

$hash = $commitParts[0]
$author = $commitParts[1]
$email = $commitParts[2]
$date = $commitParts[3]
$subject = $commitParts[4]
$body = $commitParts[5]

# 변경된 파일 목록
$changedFiles = git diff-tree --no-commit-id --name-status -r $hash

# 통계 정보
$stats = git show --stat $hash

# 요약 생성
$summary = @"
# 📋 커밋 작업 요약

**커밋 해시**: \`$hash\`  
**작성자**: $author  
**날짜**: $date  
**제목**: $subject

---

## 📝 작업 내용

$body

---

## 📁 변경된 파일

\`\`\`
$changedFiles
\`\`\`

---

## 📊 통계

\`\`\`
$stats
\`\`\`

---

## ✅ 체크리스트

- [ ] 코드 리뷰 완료
- [ ] 테스트 통과
- [ ] 문서 업데이트 (필요 시)
- [ ] 팀원 공유 완료

---

**생성 시간**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
"@

# 파일로 저장
$summary | Out-File -FilePath $OutputFile -Encoding UTF8

Write-Host "✅ 요약이 생성되었습니다: $OutputFile" -ForegroundColor Green
Write-Host ""
Write-Host "팀원과 공유하려면:" -ForegroundColor Yellow
Write-Host "  - GitHub PR에 첨부" -ForegroundColor Yellow
Write-Host "  - 팀 채팅에 공유" -ForegroundColor Yellow
Write-Host "  - 이슈 코멘트에 첨부" -ForegroundColor Yellow

