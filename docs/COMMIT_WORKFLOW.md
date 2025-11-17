# 📝 커밋 및 작업 공유 워크플로우

팀원과 효율적으로 작업 내용을 공유하기 위한 가이드입니다.

---

## 🎯 목표

- 커밋할 때마다 작업 내용을 명확하게 정리
- 팀원이 변경 사항을 쉽게 이해할 수 있도록
- PR 생성 시 자동으로 요약 포함

---

## 📋 방법 1: 커밋 메시지 템플릿 사용

### 설정 방법

1. Git 설정에 커밋 메시지 템플릿 추가:

```bash
git config commit.template .gitmessage
```

2. 커밋 시 템플릿이 자동으로 열립니다.

### 커밋 메시지 작성 예시

```
feat(a): MQTT 재시도/로그 전략 구현

Exponential backoff를 사용한 재연결 로직과 메시지 큐잉 시스템을 구현했습니다.

주요 변경 사항:
- Exponential backoff 재연결 로직 구현 (1초 → 2초 → 4초 → 8초 → 16초)
- 메시지 큐잉 시스템 추가 (최대 1000개, 자동 재시도)
- 재연결 상태 모니터링 개선
- 상세한 로깅 추가
- 자동 재연결 기능 구현

테스트:
- [x] 로컬 테스트 완료
- [x] 연결 끊김 시나리오 테스트 완료
- [ ] 통합 테스트 필요

관련 이슈:
Closes #10

팀원 공유 사항:
- MQTT 연결이 끊겨도 메시지가 손실되지 않습니다
- 재연결 시 자동으로 큐의 메시지를 발송합니다
- 로그를 통해 연결 상태를 모니터링할 수 있습니다
```

---

## 📋 방법 2: 커밋 요약 스크립트 사용

### 사용 방법

**Windows (PowerShell):**
```powershell
.\scripts\generate_commit_summary.ps1
```

**Linux/Mac (Bash):**
```bash
chmod +x scripts/generate_commit_summary.sh
./scripts/generate_commit_summary.sh
```

### 특정 커밋 요약 생성

```bash
# 특정 커밋 해시로 요약 생성
.\scripts\generate_commit_summary.ps1 -CommitHash abc1234
```

### 생성된 요약 파일

`COMMIT_SUMMARY.md` 파일이 생성되며, 다음 내용이 포함됩니다:
- 커밋 정보 (해시, 작성자, 날짜)
- 작업 내용
- 변경된 파일 목록
- 통계 정보

### 공유 방법

1. **GitHub PR에 첨부**
   - PR 설명에 `COMMIT_SUMMARY.md` 내용 복사/붙여넣기

2. **팀 채팅에 공유**
   - 슬랙/디스코드에 요약 내용 공유

3. **이슈 코멘트에 첨부**
   - 관련 이슈에 코멘트로 공유

---

## 📋 방법 3: PR 템플릿 사용

### 사용 방법

1. PR 생성 시 GitHub에서 자동으로 템플릿이 표시됩니다.
2. 템플릿에 따라 작업 내용을 작성합니다.

### PR 템플릿 작성 예시

```markdown
## 📋 작업 요약

MQTT 재시도/로그 전략을 구현하여 데이터 파이프라인의 장애 허용성을 높였습니다.

### 주요 변경 사항
- Exponential backoff 재연결 로직 구현
- 메시지 큐잉 시스템 추가
- 재연결 상태 모니터링 개선
- 상세한 로깅 추가

### 작업 배경
MQTT 연결이 끊겼을 때 메시지 손실을 방지하고, 자동으로 재연결하는 기능이 필요했습니다.

## 🔗 관련 이슈
Closes #10

## 📝 변경 사항 상세
- `mqtt_client.py`: 재연결 로직 및 큐잉 시스템 구현
- 로깅 개선: 연결 상태, 메시지 발송 상태 상세 로그

## 🧪 테스트
- [x] 로컬 테스트 완료
- [x] 연결 끊김 시나리오 테스트 완료
- [x] 큐잉 동작 확인 완료

## 💬 리뷰어에게
특히 `_process_message_queue` 메서드의 스레드 안전성과 큐 크기 제한 로직을 확인해주세요.
```

---

## 🔄 권장 워크플로우

### 1. 작업 시작 전
```bash
# 이슈 확인 및 브랜치 생성
git checkout -b feature/a-mqtt-retry-strategy
```

### 2. 작업 중
- 작은 단위로 자주 커밋
- 커밋 메시지에 작업 내용 명확히 작성

### 3. 작업 완료 후
```bash
# 1. 최종 커밋
git add .
git commit  # 템플릿 사용

# 2. 요약 생성 (선택사항)
.\scripts\generate_commit_summary.ps1

# 3. 푸시
git push origin feature/a-mqtt-retry-strategy

# 4. PR 생성
# GitHub에서 PR 생성 시 템플릿 자동 표시
```

### 4. PR 생성 후
- PR 설명에 작업 요약 작성
- `COMMIT_SUMMARY.md` 내용 포함 (생성한 경우)
- 팀원에게 리뷰 요청

---

## 💡 커밋 메시지 작성 팁

### 좋은 예

```
feat(a): MQTT exponential backoff 재연결 구현

연결 실패 시 재시도 간격을 지수적으로 증가시키는 로직을 구현했습니다.

주요 변경 사항:
- connect_with_retry 메서드에 exponential backoff 추가
- initial_delay=1초, backoff_factor=2.0으로 설정
- 최대 delay 60초로 제한

테스트:
- [x] 재연결 시나리오 테스트 완료
- [x] delay 간격 확인 완료

관련 이슈:
Closes #10

팀원 공유 사항:
- 재연결 시 서버 부하를 줄이기 위해 exponential backoff 사용
- 연결이 복구되면 자동으로 큐의 메시지 발송
```

### 나쁜 예

```
수정
```

```
MQTT 개선
```

```
버그 수정
```

---

## 📊 커밋 메시지 타입

가이드에 따라 다음 타입을 사용하세요:

- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 포맷팅
- `refactor`: 코드 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드 설정 등

---

## ✅ 체크리스트: 커밋 전

- [ ] 커밋 메시지에 작업 내용 명확히 작성
- [ ] 주요 변경 사항 나열
- [ ] 관련 이슈 번호 포함
- [ ] 테스트 완료 여부 확인
- [ ] 팀원 공유 사항 작성

---

## 🚀 빠른 시작

1. **커밋 템플릿 설정:**
```bash
git config commit.template .gitmessage
```

2. **커밋:**
```bash
git commit  # 템플릿이 자동으로 열림
```

3. **요약 생성 (선택사항):**
```bash
.\scripts\generate_commit_summary.ps1
```

4. **PR 생성 시 템플릿 사용**

---

**이제 커밋할 때마다 작업 내용을 체계적으로 정리할 수 있습니다!** 📝

