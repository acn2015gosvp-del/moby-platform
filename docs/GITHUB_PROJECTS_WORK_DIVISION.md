# 📊 GitHub Projects 보드로 업무 분담 정리하기

이 가이드는 GitHub Projects 보드를 사용하여 두 명이서 업무를 효율적으로 분담하고 추적하는 방법을 안내합니다.

---

## 🎯 Step 1: Projects 보드 생성 (5분)

### 1-1. 보드 생성

1. GitHub 저장소로 이동: https://github.com/acn2015gosvp-del/moby-platform
2. 상단 탭에서 **Projects** 클릭
3. **New project** 버튼 클릭
4. **Board** 템플릿 선택
5. 프로젝트 이름: `MOBY Development Board`
6. **Create** 클릭

### 1-2. 컬럼 구성

기본 컬럼을 다음과 같이 설정:

```
📥 Backlog      (할 일 목록, 우선순위 낮음)
📋 To Do        (이번 주 작업)
🔄 In Progress  (현재 작업 중)
👀 Review       (PR 생성 완료, 리뷰 대기)
✅ Done         (완료된 작업)
```

**컬럼 추가 방법:**
- 보드 오른쪽 상단 **+ Add column** 클릭
- 컬럼 이름 입력 후 **Create column**

---

## 🏷️ Step 2: 라벨 생성 (10분)

### 2-1. 라벨 생성

**Issues** 탭 → **Labels**에서 다음 라벨들을 생성하세요:

#### 우선순위 라벨
- `priority:high` (빨간색) - 즉시 필요
- `priority:medium` (노란색) - 이번 주 내
- `priority:low` (회색) - 나중에

#### 작업 유형 라벨
- `backend` (파란색) - Backend 작업
- `frontend` (초록색) - Frontend 작업
- `bug` (빨간색) - 버그 수정
- `feature` (보라색) - 새 기능
- `documentation` (회색) - 문서 작업
- `testing` (주황색) - 테스트

#### 담당자 라벨
- `assignee:dev-a` (개발자 A)
- `assignee:dev-b` (개발자 B)

**라벨 생성 방법:**
1. **Issues** 탭 → **Labels** 클릭
2. **New label** 클릭
3. 이름, 색상, 설명 입력
4. **Create label** 클릭

---

## 📝 Step 3: 이슈 생성 및 보드에 추가 (15분)

### 3-1. 개발자 A의 작업 이슈 생성

#### 이슈 #10: MQTT 재연결 로직 개선

1. **Issues** 탭 → **New issue** 클릭
2. **Task assignment** 템플릿 선택
3. 다음 내용 입력:

**제목:**
```
[TASK] MQTT 재연결 로직 개선 (exponential backoff)
```

**본문:**
```markdown
## 작업 설명
MQTT 클라이언트에 exponential backoff를 사용한 재연결 로직을 구현합니다.

## 현재 상태
- ✅ 기본 재연결 로직 있음 (`connect_with_retry`)
- ❌ exponential backoff 미구현
- ❌ 재연결 간격이 고정 (5초)

## 작업 항목
- [ ] exponential backoff 구현 (1초 → 2초 → 4초 → 8초 → 16초)
- [ ] 재연결 상태 모니터링 개선
- [ ] 연결 실패 시 큐잉 로직 추가
- [ ] 로깅 개선

## 관련 파일
- `backend/api/services/mqtt_client.py`

## 예상 시간
1일

## 완료 기준
- exponential backoff 동작 확인
- 재연결 로그 명확화
- 연결 실패 시 메시지 큐에 저장

## 담당자
- [x] 개발자 A
```

4. **Labels**: `backend`, `feature`, `priority:high`, `assignee:dev-a` 추가
5. **Assignees**: 개발자 A 선택
6. **Projects**: `MOBY Development Board` 선택, `To Do` 컬럼에 추가
7. **Submit new issue** 클릭

---

#### 이슈 #11: InfluxDB 배치 쓰기 구현

**제목:**
```
[TASK] InfluxDB 배치 쓰기 구현
```

**본문:**
```markdown
## 작업 설명
InfluxDB에 여러 포인트를 배치로 한 번에 쓰는 기능을 구현합니다.

## 현재 상태
- ✅ 기본 쓰기 기능 있음 (`write_point`)
- ❌ 배치 쓰기 없음
- ❌ 실패 시 재시도 없음

## 작업 항목
- [ ] 배치 쓰기 로직 구현
- [ ] 버퍼 크기 설정 (예: 100개 또는 5초마다)
- [ ] 주기적 플러시 로직
- [ ] 쓰기 실패 시 재시도 로직
- [ ] 에러 처리 개선

## 관련 파일
- `backend/api/services/influx_client.py`

## 예상 시간
1일

## 완료 기준
- 여러 포인트를 배치로 한 번에 쓰기
- 메모리 효율적 버퍼링
- 쓰기 실패 시 자동 재시도

## 담당자
- [x] 개발자 A
```

**Labels**: `backend`, `feature`, `priority:high`, `assignee:dev-a`

---

#### 이슈 #12: Alert Engine 에러 처리 개선

**제목:**
```
[TASK] Alert Engine 에러 처리 개선
```

**본문:**
```markdown
## 작업 설명
Alert Engine의 에러 처리를 표준화하고 개선합니다.

## 작업 항목
- [ ] 커스텀 예외 클래스 정의 (`backend/api/core/exceptions.py` 생성)
- [ ] 에러 처리 표준화
- [ ] LLM 요약 실패 시 fallback 메시지
- [ ] 알람 ID 생성 전략 개선 (UUID 사용)
- [ ] 로깅 개선

## 관련 파일
- `backend/api/services/alert_engine.py`
- `backend/api/core/exceptions.py` (새로 생성)

## 예상 시간
1일

## 완료 기준
- 모든 에러 경로 처리
- 명확한 에러 메시지
- LLM 실패 시에도 알람 생성 가능

## 담당자
- [x] 개발자 A
```

**Labels**: `backend`, `feature`, `priority:high`, `assignee:dev-a`

---

### 3-2. 개발자 B의 작업 이슈 생성

#### 이슈 #20: React 프로젝트 초기 설정

**제목:**
```
[TASK] React 프로젝트 초기 설정
```

**본문:**
```markdown
## 작업 설명
Vite + React + TypeScript 프로젝트를 초기 설정합니다.

## 작업 항목
- [ ] Vite + React + TypeScript 프로젝트 생성
- [ ] 기본 폴더 구조 생성
  ```
  frontend/src/
  ├── components/
  ├── pages/
  ├── services/
  ├── hooks/
  ├── context/
  └── utils/
  ```
- [ ] 라우팅 설정 (React Router)
- [ ] 기본 스타일링 설정 (CSS/Tailwind)
- [ ] 환경 변수 설정

## 관련 파일
- `frontend/` (새로 생성)

## 예상 시간
1일

## 완료 기준
- 프로젝트 실행 가능
- 기본 라우팅 동작
- 폴더 구조 명확

## 담당자
- [x] 개발자 B
```

**Labels**: `frontend`, `feature`, `priority:high`, `assignee:dev-b`

---

#### 이슈 #21: API 서비스 레이어 구축

**제목:**
```
[TASK] API 서비스 레이어 구축
```

**본문:**
```markdown
## 작업 설명
Frontend에서 Backend API를 호출하기 위한 서비스 레이어를 구축합니다.

## 작업 항목
- [ ] Axios 설정
- [ ] API 베이스 URL 설정
- [ ] 에러 처리 인터셉터
- [ ] Alert API 서비스 함수
  - `getAlerts()`
  - `createAlert(data)`
  - `getAlertById(id)`
- [ ] Sensor API 서비스 함수
  - `getSensorData()`
  - `postSensorData(data)`
- [ ] 타입 정의 (TypeScript)

## 관련 파일
- `frontend/src/services/`

## 예상 시간
1일

## 완료 기준
- API 호출 가능
- 에러 처리 동작
- 타입 안정성 확보

## 담당자
- [x] 개발자 B
```

**Labels**: `frontend`, `feature`, `priority:high`, `assignee:dev-b`

---

#### 이슈 #22: 기본 레이아웃 컴포넌트

**제목:**
```
[TASK] 기본 레이아웃 컴포넌트 개발
```

**본문:**
```markdown
## 작업 설명
애플리케이션의 기본 레이아웃 컴포넌트를 개발합니다.

## 작업 항목
- [ ] Header 컴포넌트
- [ ] Sidebar 컴포넌트
- [ ] MainLayout 컴포넌트
- [ ] 기본 스타일링
- [ ] 반응형 디자인

## 관련 파일
- `frontend/src/components/`

## 예상 시간
1일

## 완료 기준
- 레이아웃 구조 완성
- 반응형 디자인
- 네비게이션 동작

## 담당자
- [x] 개발자 B
```

**Labels**: `frontend`, `feature`, `priority:high`, `assignee:dev-b`

---

## 📊 Step 4: 보드에서 작업 추적하기

### 4-1. 작업 시작 시

1. 이슈를 **To Do**에서 **In Progress**로 드래그
2. 브랜치 생성 및 작업 시작
3. 이슈 코멘트로 진행 상황 업데이트 (선택사항)

**예시 코멘트:**
```
작업 시작했습니다. exponential backoff 로직 구현 중입니다.
```

---

### 4-2. 작업 중간 업데이트

이슈에 코멘트를 남겨 진행 상황을 공유:

```
진행 상황:
- [x] exponential backoff 기본 구조 완료
- [ ] 재연결 상태 모니터링 작업 중
- [ ] 큐잉 로직 구현 예정
```

---

### 4-3. PR 생성 시

1. 작업 완료 후 PR 생성
2. PR 설명에 이슈 번호 링크: `Closes #10`
3. 이슈를 **In Progress**에서 **Review**로 이동

**PR 설명 예시:**
```markdown
## 변경 사항
- exponential backoff를 사용한 재연결 로직 구현
- 최대 5회 재시도 후 실패 처리
- 재연결 로그 추가

## 관련 이슈
Closes #10
```

---

### 4-4. 리뷰 완료 및 병합

1. PR 승인 후 병합
2. 이슈가 자동으로 **Done** 컬럼으로 이동 (PR에 `Closes #10` 포함 시)
3. 이슈가 자동으로 닫힘

---

## 🎨 Step 5: 보드 커스터마이징

### 5-1. 필터 설정

보드에서 특정 담당자나 라벨만 보기:

1. 보드 상단 **Filter** 클릭
2. **Assignee**: 개발자 A 또는 개발자 B 선택
3. **Labels**: `backend` 또는 `frontend` 선택

### 5-2. 그룹화 설정

보드를 담당자별로 그룹화:

1. 보드 상단 **⚙️ Settings** 클릭
2. **Group by**: `Assignee` 선택
3. 각 담당자의 작업을 한눈에 확인 가능

### 5-3. 자동화 규칙 (선택사항)

GitHub Actions를 사용하여 자동화:

1. 보드 **⚙️ Settings** → **Workflows**
2. 자동화 규칙 추가:
   - PR 생성 시 → `Review` 컬럼으로 이동
   - PR 병합 시 → `Done` 컬럼으로 이동

---

## 📋 Step 6: 주간 작업 계획 세우기

### 6-1. 월요일 아침

1. **To Do** 컬럼 확인
2. 이번 주 작업 계획
3. 각자 담당 작업을 **In Progress**로 이동

### 6-2. 매일 저녁

1. 완료한 작업 확인
2. **Done** 컬럼 정리
3. 내일 작업 계획

### 6-3. 금요일 오후

1. 주간 회고
2. 다음 주 계획 수립
3. **Done** 컬럼의 이슈들 확인 및 정리

---

## 💡 보드 활용 팁

### 1. 시각적 추적
- 각 컬럼의 이슈 개수로 진행 상황 파악
- 색상 라벨로 작업 유형 구분

### 2. 우선순위 관리
- `priority:high` 라벨로 긴급 작업 표시
- **To Do** 컬럼에서 우선순위별로 정렬

### 3. 담당자별 필터
- 개발자 A: `assignee:dev-a` 필터
- 개발자 B: `assignee:dev-b` 필터

### 4. 주간 목표 설정
- 매주 월요일 **To Do** 컬럼에 목표 작업 추가
- 금요일 **Done** 컬럼에서 완료 확인

---

## 📊 예시 보드 구조

```
┌─────────────────────────────────────────────────────────────┐
│  MOBY Development Board                                     │
├─────────────┬─────────────┬─────────────┬─────────────┬─────┤
│  To Do      │ In Progress │   Review    │    Done     │     │
├─────────────┼─────────────┼─────────────┼─────────────┼─────┤
│             │             │             │             │     │
│ #10 MQTT    │ #12 Alert   │ #11 Influx  │ #20 React   │     │
│ 재연결      │ Engine      │ 배치 쓰기   │ 설정        │     │
│ (A, high)   │ (A, high)   │ (A, high)   │ (B, high)   │     │
│             │             │             │             │     │
│ #21 API     │ #22 레이아웃│             │             │     │
│ 서비스      │ (B, high)   │             │             │     │
│ (B, high)   │             │             │             │     │
│             │             │             │             │     │
└─────────────┴─────────────┴─────────────┴─────────────┴─────┘
```

---

## ✅ 체크리스트: 보드 설정 완료

- [ ] Projects 보드 생성
- [ ] 컬럼 구성 (Backlog, To Do, In Progress, Review, Done)
- [ ] 라벨 생성 (우선순위, 작업 유형, 담당자)
- [ ] 개발자 A 작업 이슈 3개 생성 (#10, #11, #12)
- [ ] 개발자 B 작업 이슈 3개 생성 (#20, #21, #22)
- [ ] 모든 이슈를 보드에 추가
- [ ] 담당자 할당
- [ ] 라벨 추가

---

## 🚀 다음 단계

보드 설정이 완료되면:

1. 각자 담당 작업을 **In Progress**로 이동
2. 브랜치 생성 및 작업 시작
3. 작업 완료 후 PR 생성
4. 리뷰 및 병합
5. **Done** 컬럼으로 이동 확인

---

**이제 보드에서 업무를 효율적으로 추적할 수 있습니다!** 📊

질문이 있으면 GitHub Discussions나 이슈 코멘트로 남겨주세요.

