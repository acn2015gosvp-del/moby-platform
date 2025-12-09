#!/bin/bash
# 커밋 요약 생성 스크립트 (Bash)
# 사용법: ./scripts/generate_commit_summary.sh [commit-hash]

COMMIT_HASH=${1:-HEAD}
OUTPUT_FILE="COMMIT_SUMMARY.md"

echo "📝 커밋 요약 생성 중..."

# 최근 커밋 정보 가져오기
HASH=$(git log -1 --pretty=format:"%H" $COMMIT_HASH)
AUTHOR=$(git log -1 --pretty=format:"%an" $COMMIT_HASH)
EMAIL=$(git log -1 --pretty=format:"%ae" $COMMIT_HASH)
DATE=$(git log -1 --pretty=format:"%ad" --date=iso $COMMIT_HASH)
SUBJECT=$(git log -1 --pretty=format:"%s" $COMMIT_HASH)
BODY=$(git log -1 --pretty=format:"%b" $COMMIT_HASH)

# 변경된 파일 목록
CHANGED_FILES=$(git diff-tree --no-commit-id --name-status -r $HASH)

# 통계 정보
STATS=$(git show --stat $HASH)

# 요약 생성
cat > $OUTPUT_FILE << EOF
# 📋 커밋 작업 요약

**커밋 해시**: \`$HASH\`  
**작성자**: $AUTHOR  
**날짜**: $DATE  
**제목**: $SUBJECT

---

## 📝 작업 내용

$BODY

---

## 📁 변경된 파일

\`\`\`
$CHANGED_FILES
\`\`\`

---

## 📊 통계

\`\`\`
$STATS
\`\`\`

---

## ✅ 체크리스트

- [ ] 코드 리뷰 완료
- [ ] 테스트 통과
- [ ] 문서 업데이트 (필요 시)
- [ ] 팀원 공유 완료

---

**생성 시간**: $(date '+%Y-%m-%d %H:%M:%S')
EOF

echo "✅ 요약이 생성되었습니다: $OUTPUT_FILE"
echo ""
echo "팀원과 공유하려면:"
echo "  - GitHub PR에 첨부"
echo "  - 팀 채팅에 공유"
echo "  - 이슈 코멘트에 첨부"

