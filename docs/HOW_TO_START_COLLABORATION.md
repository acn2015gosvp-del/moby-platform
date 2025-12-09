# 🚀 협업 시작하기: 단계별 가이드

이 문서는 두 명이서 실제로 협업을 시작하는 **구체적인 단계**를 안내합니다.

---

## 📋 Step 1: GitHub Projects 보드 생성 (5분)

### 1-1. Projects 보드 생성

1. GitHub 저장소로 이동: https://github.com/acn2015gosvp-del/moby-platform
2. 상단 탭에서 **Projects** 클릭
3. **New project** 버튼 클릭
4. **Board** 템플릿 선택
5. 프로젝트 이름: `MOBY Development Board`
6. **Create** 클릭

### 1-2. 컬럼 추가

기본 컬럼에 다음을 추가/수정:

```
📥 Backlog      (기본)
📋 To Do        (기본)
🔄 In Progress  (기본)
👀 Review       (기본)
✅ Done         (기본)
```

### 1-3. 라벨 생성

**Issues** 탭 → **Labels**에서 다음 라벨 생성:

**우선순위:**
- `priority:high` (빨간색)
- `priority:medium` (노란색)
- `priority:low` (회색)

**작업 유형:**
- `backend` (파란색)
- `frontend` (초록색)
- `bug` (빨간색)
- `feature` (보라색)

**담당자:**
- `assignee:dev-a` (개발자 A)
- `assignee:dev-b` (개발자 B)

---

## 📝 Step 2: 첫 작업 이슈 생성 (10분)

### 2-1. 개발자 A의 첫 이슈 생성

1. **Issues** 탭 → **New issue** 클릭
2. **Task assignment** 템플릿 선택
3. 다음 내용 입력:

**제목:**
```
[TASK] MQTT 재연결 로직 구현
```

**내용:**
```markdown
## 작업 설명
MQTT 클라이언트에 exponential backoff를 사용한 재연결 로직을 구현합니다.

## 작업 항목
- [ ] exponential backoff 재연결 로직 구현
- [ ] 연결 상태 모니터링
- [ ] 재연결 시도 횟수 제한 (최대 5회)
- [ ] 로깅 추가

## 관련 파일
- `backend/api/services/mqtt_client.py`

## 예상 시간
1일

## 담당자
- [x] 개발자 A
```

4. **Labels**: `backend`, `feature`, `priority:high`, `assignee:dev-a` 추가
5. **Assignees**: 개발자 A 선택
6. **Projects**: `MOBY Development Board` 선택, `To Do` 컬럼에 추가
7. **Submit new issue** 클릭

### 2-2. 개발자 B의 첫 이슈 생성

동일한 방식으로:

**제목:**
```
[TASK] React 프로젝트 초기 설정
```

**내용:**
```markdown
## 작업 설명
Vite + React + TypeScript 프로젝트를 초기 설정합니다.

## 작업 항목
- [ ] Vite + React 프로젝트 생성
- [ ] TypeScript 설정
- [ ] 기본 폴더 구조 생성
- [ ] 라우팅 설정 (React Router)
- [ ] 기본 스타일링 설정

## 관련 파일
- `frontend/` (새로 생성)

## 예상 시간
1일

## 담당자
- [x] 개발자 B
```

4. **Labels**: `frontend`, `feature`, `priority:high`, `assignee:dev-b` 추가
5. **Assignees**: 개발자 B 선택
6. **Projects**: `MOBY Development Board` 선택, `To Do` 컬럼에 추가
7. **Submit new issue** 클릭

---

## 🌿 Step 3: 브랜치 생성 및 작업 시작 (5분)

### 3-1. 최신 코드 가져오기

**양쪽 모두 실행:**
```bash
git checkout main
git pull origin main
```

### 3-2. 새 브랜치 생성

**개발자 A:**
```bash
git checkout -b feature/a-mqtt-reconnection
```

**개발자 B:**
```bash
git checkout -b feature/b-react-setup
```

### 3-3. 작업 시작

각자 할당된 작업을 시작합니다.

---

## 💻 Step 4: 작업 중 워크플로우

### 4-1. 작은 단위로 커밋

**예시 (개발자 A):**
```bash
# 작업 중간에 커밋
git add backend/api/services/mqtt_client.py
git commit -m "feat(a): MQTT 재연결 로직 기본 구조 추가"
```

**예시 (개발자 B):**
```bash
# 작업 중간에 커밋
git add frontend/
git commit -m "feat(b): React 프로젝트 초기 설정"
```

### 4-2. 작업 완료 후 푸시

```bash
git push origin feature/a-mqtt-reconnection
# 또는
git push origin feature/b-react-setup
```

### 4-3. PR 생성

1. GitHub 저장소로 이동
2. **Pull requests** 탭 클릭
3. **New pull request** 클릭
4. base: `main` ← compare: `feature/a-mqtt-reconnection` 선택
5. PR 제목 및 설명 작성:

**제목:**
```
feat(a): MQTT 재연결 로직 구현
```

**설명:**
```markdown
## 변경 사항
- exponential backoff를 사용한 재연결 로직 구현
- 최대 5회 재시도 후 실패 처리
- 재연결 로그 추가

## 관련 이슈
Closes #10

## 테스트
- [ ] MQTT 연결 끊김 시 자동 재연결 확인
- [ ] 재연결 로그 확인
```

6. **Reviewers**: 개발자 B 선택 (리뷰 요청)
7. **Labels**: `backend`, `feature` 추가
8. **Create pull request** 클릭

### 4-4. Projects 보드 업데이트

1. 생성한 PR이 이슈와 연결되면 자동으로 Projects 보드에 반영됩니다
2. 수동으로 업데이트하려면:
   - 이슈에서 **Projects** 클릭
   - `In Progress` → `Review`로 이동

---

## 👀 Step 5: 코드 리뷰 (24시간 이내)

### 5-1. 리뷰어가 할 일

1. **Pull requests** 탭에서 PR 확인
2. **Files changed** 탭에서 변경 사항 확인
3. 코드 리뷰:
   - 좋은 점 코멘트
   - 개선 제안
   - 질문
4. 승인 또는 수정 요청

### 5-2. 리뷰 코멘트 예시

**좋은 예:**
```
좋은 구현입니다! 다만 재연결 간격이 너무 짧을 수 있어서, 
최소 간격을 2초로 늘리는 게 어떨까요?
```

**나쁜 예:**
```
이거 잘못됐어요
```

### 5-3. PR 작성자가 할 일

1. 리뷰 코멘트 확인
2. 필요한 수정 사항 반영
3. 커밋 및 푸시 (자동으로 PR에 반영됨)
4. 리뷰어에게 알림

---

## ✅ Step 6: PR 병합

### 6-1. 승인 후 병합

1. 리뷰어가 **Approve** 클릭
2. PR 작성자가 **Merge pull request** 클릭
3. **Confirm merge** 클릭
4. 브랜치 삭제 (선택사항)

### 6-2. Projects 보드 업데이트

- PR이 병합되면 연결된 이슈가 자동으로 `Done` 컬럼으로 이동
- 이슈가 자동으로 닫힘 (PR 설명에 `Closes #10` 포함 시)

---

## 📅 Step 7: 일일 워크플로우

### 아침 (10분)

**슬랙/디스코드 또는 GitHub Discussions에서:**

```
개발자 A: "안녕! 어제 MQTT 재연결 로직 구현했고, 
          오늘은 InfluxDB 배치 쓰기 작업할 예정이야."

개발자 B: "안녕! 어제 React 프로젝트 설정했고, 
          오늘은 API 서비스 레이어 만들 예정이야."
```

### 작업 중

- 각자 브랜치에서 작업
- 1-2시간마다 커밋
- 막히면 즉시 질문

### 저녁 (10분)

```
개발자 A: "오늘 InfluxDB 배치 쓰기 완료했고, PR 올렸어. 리뷰 부탁!"

개발자 B: "오늘 API 서비스 레이어 완료했고, PR 올렸어. 리뷰 부탁!"
```

---

## 🎯 실제 예시: 첫 주 작업 플랜

### 월요일

**개발자 A:**
- [ ] 이슈 #10 생성: MQTT 재연결 로직
- [ ] 브랜치 생성: `feature/a-mqtt-reconnection`
- [ ] 작업 시작

**개발자 B:**
- [ ] 이슈 #20 생성: React 프로젝트 설정
- [ ] 브랜치 생성: `feature/b-react-setup`
- [ ] 작업 시작

### 화요일

**개발자 A:**
- [ ] MQTT 재연결 로직 완료
- [ ] PR 생성 (#11)
- [ ] 개발자 B에게 리뷰 요청

**개발자 B:**
- [ ] React 프로젝트 설정 완료
- [ ] PR 생성 (#21)
- [ ] 개발자 A에게 리뷰 요청

### 수요일

**개발자 A:**
- [ ] PR #21 리뷰
- [ ] 다음 작업 이슈 생성: InfluxDB 배치 쓰기
- [ ] 새 브랜치에서 작업 시작

**개발자 B:**
- [ ] PR #11 리뷰
- [ ] 다음 작업 이슈 생성: API 서비스 레이어
- [ ] 새 브랜치에서 작업 시작

---

## 💡 핵심 원칙

### 1. 작은 단위로 작업
- 큰 작업은 여러 이슈로 분할
- 하루에 1-2개 작업 완료 목표

### 2. 자주 커밋 및 PR
- 하루 1-2회 PR 생성
- 작은 변경이라도 PR로 관리

### 3. 즉시 소통
- 막히면 바로 질문
- API 변경은 미리 논의

### 4. 상호 리뷰
- 모든 PR은 리뷰 필수
- 24시간 이내 리뷰 목표

### 5. 정기적 동기화
- 하루 2-3회 `main` 브랜치 pull
- 충돌 즉시 해결

---

## 🚨 문제 발생 시

### 충돌 발생

```bash
git checkout main
git pull origin main
git checkout feature/a-mqtt-reconnection
git rebase main
# 충돌 해결
git push origin feature/a-mqtt-reconnection --force-with-lease
```

### 작업 방향이 불명확할 때

1. GitHub Issue에 질문 코멘트 작성
2. 또는 직접 소통
3. 명확해지면 작업 재개

### 리뷰가 지연될 때

- 친절하게 리마인더
- 긴급하지 않으면 기다리기
- 긴급하면 직접 연락

---

## ✅ 체크리스트: 첫 협업 시작 전

- [ ] GitHub Projects 보드 생성
- [ ] 라벨 생성
- [ ] 첫 이슈 2개 생성 (각자 1개씩)
- [ ] 브랜치 생성
- [ ] 작업 시작!

---

**이제 시작하세요!** 🚀

질문이 있으면 GitHub Discussions나 이슈 코멘트로 남겨주세요.

