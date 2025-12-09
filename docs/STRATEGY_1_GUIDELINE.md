# 📋 전략 1: 기능별 분담 가이드라인

**개발자 A (Backend Core / Data Pipeline)** + **개발자 B (Frontend / Integration / Testing)**

---

## 🎯 역할 정의

### 👤 개발자 A: Backend Core / Data Pipeline Specialist

**주요 책임:**
- Backend 서비스 로직 개발 및 개선
- 데이터 파이프라인 (MQTT → InfluxDB) 구축 및 안정화
- Alert Engine 및 이상 탐지 로직
- API 엔드포인트 설계 및 구현
- 데이터 검증 및 스키마 관리

**핵심 역량:**
- FastAPI, Python
- MQTT, InfluxDB
- 데이터 처리 및 파이프라인 최적화

---

### 👤 개발자 B: Frontend / Integration / Testing Specialist

**주요 책임:**
- React Frontend 개발 (Vite)
- WebSocket 클라이언트 구현
- UI 컴포넌트 개발 (AlertToast, AlertsPanel 등)
- 테스트 코드 작성 및 품질 관리
- API 통합 및 문서화
- 사용자 경험 최적화

**핵심 역량:**
- React, TypeScript/JavaScript
- WebSocket, API 통합
- 테스트 작성 (pytest, React Testing Library)

---

## 📁 파일 소유권 및 책임 영역

### 개발자 A 소유 영역

#### Backend Services
```
backend/api/services/
├── alert_engine.py              ✅ A 소유
├── anomaly_vector_service.py    ✅ A 소유
├── influx_client.py             ✅ A 소유
├── mqtt_client.py               ✅ A 소유
├── llm_client.py                ✅ A 소유 (Backend 관점)
└── alerts_summary.py           ✅ A 소유
```

#### API Routes
```
backend/api/
├── routes_alerts.py             ✅ A 소유
└── routes_sensors.py            ✅ A 소유
```

#### Schemas (Backend 관점)
```
backend/api/services/schemas/
├── alert_request_schema.py      ✅ A 소유
├── alert_schema.py              ✅ A 소유
└── sensor_schema.py             ✅ A 소유
```

#### Core Configuration
```
backend/api/services/schemas/models/core/
├── config.py                    ✅ A 소유
└── logger.py                    ✅ A 소유
```

---

### 개발자 B 소유 영역

#### Frontend (전체)
```
frontend/                        ✅ B 소유 (전체)
├── src/
│   ├── components/
│   ├── pages/
│   ├── services/
│   ├── hooks/
│   ├── context/
│   └── utils/
└── package.json
```

#### Tests
```
backend/tests/                   ✅ B 소유 (전체)
├── test_alert_engine.py
├── test_anomaly_vector_service.py
└── (추가 테스트 파일들)
```

#### Documentation
```
docs/                            ✅ B 소유 (대부분)
├── API_DOCUMENTATION.md         ✅ B 소유
└── (API 통합 관련 문서)
```

---

### 공유 영역 (소통 필수)

다음 영역은 변경 시 반드시 상대방과 논의해야 합니다:

```
backend/main.py                  ⚠️ 공유 (양쪽 모두 수정 가능)
requirements.txt                 ⚠️ 공유 (의존성 추가 시 논의)
.env.example                      ⚠️ 공유
README.md                         ⚠️ 공유
```

**규칙:**
- 공유 영역 수정 전 GitHub Issue 생성 또는 직접 소통
- PR 생성 시 상대방에게 리뷰 요청 필수

---

## 📋 작업 항목 분담

### 개발자 A의 주요 작업 항목

#### Phase 1: Backend 안정화 (1-2주)

**Alert Engine 개선**
- [ ] Alert Engine 단위 테스트 추가 (B와 협업)
- [ ] LLM 요약 실패 시 fallback 메시지 구현
- [ ] 알람 ID 생성 전략 개선 (UUID 사용)
- [ ] 에러 처리 개선 (커스텀 예외 클래스)

**데이터 파이프라인**
- [ ] MQTT 클라이언트 재연결 로직 구현 (exponential backoff)
- [ ] InfluxDB 쓰기 실패 시 버퍼링 및 재전송 로직
- [ ] MQTT 메시지 큐잉 및 재시도 로직
- [ ] InfluxDB 배치 쓰기 최적화

**API 개선**
- [ ] API 엔드포인트에 상세한 docstring 추가
- [ ] 에러 처리 표준화
- [ ] 의존성 주입 패턴 도입 (FastAPI Depends)

**인프라 및 설정**
- [ ] 환경 변수 관리 개선 (.env 파일)
- [ ] 설정 검증 및 기본값 처리
- [ ] 로깅 표준화 (core/logger.py 활용)

#### Phase 2: 기능 확장 (3-4주)

- [ ] 새로운 센서 타입 지원
- [ ] Alert 규칙 확장
- [ ] 성능 최적화 (async/await 활용)
- [ ] 모니터링 및 헬스체크 API

---

### 개발자 B의 주요 작업 항목

#### Phase 1: Frontend 초기 설정 (1주)

**프로젝트 설정**
- [ ] React + Vite 프로젝트 초기화
- [ ] TypeScript 설정
- [ ] 기본 폴더 구조 생성
- [ ] 라우팅 설정 (React Router)

**기본 컴포넌트**
- [ ] 레이아웃 컴포넌트
- [ ] 네비게이션 컴포넌트
- [ ] 기본 스타일링 (CSS/Tailwind)

#### Phase 2: API 통합 및 핵심 기능 (2-3주)

**API 통합**
- [ ] Axios 설정 및 API 서비스 레이어
- [ ] Alert API 통합
- [ ] Sensor API 통합
- [ ] 에러 처리 및 재시도 로직

**WebSocket 클라이언트**
- [ ] WebSocket 연결 관리
- [ ] 실시간 Alert 수신
- [ ] 재연결 로직

**Alert UI 컴포넌트**
- [ ] AlertToast 컴포넌트 (알림 토스트)
- [ ] AlertsPanel 컴포넌트 (알림 목록)
- [ ] Alert 상세 모달
- [ ] 애니메이션 (fade-in/out)

#### Phase 3: 테스트 및 품질 관리 (지속적)

**테스트 작성**
- [ ] Backend 단위 테스트 (A와 협업)
- [ ] Backend 통합 테스트
- [ ] Frontend 컴포넌트 테스트
- [ ] E2E 테스트 (선택사항)

**문서화**
- [ ] API 사용 가이드 작성
- [ ] 컴포넌트 문서화
- [ ] 통합 가이드 작성

---

## 🔄 일일 워크플로우

### 아침 체크인 (10분)

**공유 사항:**
1. 어제 완료한 작업
2. 오늘 계획한 작업
3. 블로커 또는 도움이 필요한 것

**예시:**
```
개발자 A: "어제 MQTT 재연결 로직 구현했고, 오늘은 InfluxDB 배치 쓰기 작업할 예정. 
          API 스펙 변경이 필요하면 알려줘."

개발자 B: "어제 AlertToast 컴포넌트 만들었고, 오늘은 API 통합할 예정. 
          Alert API 응답 형식 확인이 필요해."
```

### 작업 중

**독립 작업:**
- 각자 브랜치에서 개발
- 작은 단위로 자주 커밋 (1-2시간마다)

**의존성 발생 시:**
- 즉시 소통 (슬랙/디스코드)
- GitHub Issue 생성하여 추적

**예시 시나리오:**
```
개발자 B: "Alert API 응답에 `timestamp` 필드가 필요한데 추가 가능해?"
개발자 A: "네, routes_alerts.py 수정해서 추가할게. 30분 후 PR 올릴게."
```

### 저녁 체크아웃 (10분)

**공유 사항:**
1. 완료한 작업
2. PR 생성 (있는 경우)
3. 내일 계획

**PR 생성 시:**
- 상대방에게 리뷰 요청
- 관련 이슈 링크
- 변경 사항 요약

---

## 🌿 브랜치 전략

### 브랜치 네이밍

```
feature/a-{작업명}    # 개발자 A의 기능 작업
feature/b-{작업명}    # 개발자 B의 기능 작업
fix/a-{버그명}        # 개발자 A의 버그 수정
fix/b-{버그명}        # 개발자 B의 버그 수정
```

**예시:**
- `feature/a-mqtt-reconnection`
- `feature/b-alert-toast-component`
- `fix/a-influxdb-batch-write`

### 작업 플로우

1. **최신 코드 가져오기**
```bash
git checkout main
git pull origin main
```

2. **새 브랜치 생성**
```bash
# 개발자 A
git checkout -b feature/a-mqtt-reconnection

# 개발자 B
git checkout -b feature/b-alert-toast-component
```

3. **작업 및 커밋**
```bash
git add .
git commit -m "feat(a): MQTT 재연결 로직 구현"
```

4. **푸시 및 PR 생성**
```bash
git push origin feature/a-mqtt-reconnection
# GitHub에서 PR 생성, 개발자 B에게 리뷰 요청
```

5. **리뷰 및 병합**
- 상대방이 리뷰
- 승인 후 `main`에 병합
- 브랜치 삭제

---

## 🚨 충돌 방지 규칙

### 1. 파일 수정 전 확인

**공유 영역 수정 시:**
- GitHub Issue 생성 또는 직접 소통
- 변경 사항 미리 공유

**예시:**
```
개발자 A: "main.py에 새로운 라우터 추가해야 하는데 괜찮아?"
개발자 B: "네, 문제없어. PR 올리면 리뷰할게."
```

### 2. API 스펙 변경

**변경 전:**
- GitHub Issue 생성
- 변경 사항 문서화
- 상대방 확인 후 진행

**변경 후:**
- API 문서 업데이트
- Frontend 통합 테스트 (B 담당)

### 3. 의존성 추가

**requirements.txt 수정 시:**
- 변경 사유 설명
- 버전 명시
- 상대방 확인

---

## 📊 작업 추적

### GitHub Issues 활용

**이슈 생성 규칙:**
- 모든 작업은 이슈로 생성
- 라벨 사용: `backend`, `frontend`, `bug`, `feature`
- 담당자 할당
- Projects 보드에 추가

**이슈 템플릿:**
- 기능 요청: `feature_request.md`
- 버그 리포트: `bug_report.md`
- 작업 할당: `task_assignment.md`

### 주간 목표 설정

**매주 월요일:**
- 이번 주 목표 설정
- 작업 항목 이슈 생성
- 우선순위 결정

**매주 금요일:**
- 완료 사항 정리
- 다음 주 계획
- 개선점 논의

---

## 💡 효율성 향상 팁

### 1. 작은 단위로 작업

**나쁜 예:**
```
"Alert 시스템 전체 구현" (너무 큼)
```

**좋은 예:**
```
"Alert API 엔드포인트 구현"
"AlertToast 컴포넌트 구현"
"Alert API 통합"
```

### 2. 자주 커밋 및 PR

- 하루 1-2회 PR 생성 목표
- 작은 변경이라도 PR로 관리
- 빠른 피드백 루프

### 3. 명확한 커밋 메시지

**형식:**
```
<type>(<scope>): <subject>

<body>
```

**예시:**
```
feat(a): MQTT 재연결 로직 구현

exponential backoff를 사용한 재연결 로직을 추가했습니다.
연결 실패 시 최대 5회까지 재시도하며, 재시도 간격은
1초, 2초, 4초, 8초, 16초로 증가합니다.

Closes #123
```

### 4. 정기적 동기화

- 하루 2-3회 `main` 브랜치 pull
- 충돌 발생 시 즉시 해결
- 작은 충돌이라도 미루지 않기

### 5. 문서화 습관

- 코드 변경 시 관련 문서도 업데이트
- API 변경 시 즉시 문서화
- 복잡한 로직은 주석 추가

---

## 📞 소통 채널

### 코드 리뷰
- **GitHub PR 코멘트**: 코드 관련 논의
- **리뷰 시간**: 24시간 이내 목표

### 일반 논의
- **GitHub Discussions**: 아키텍처, 설계 논의
- **GitHub Issues**: 작업 추적 및 논의

### 긴급 사항
- **직접 연락**: 블로커 발생 시 즉시 소통
- **슬랙/디스코드**: 실시간 소통 (선택사항)

### 정기 회의
- **일일 스탠드업**: 아침 10분 (선택사항)
- **주간 회고**: 금요일 오후 30분

---

## ✅ 체크리스트: 새 기능 시작 전

### 개발자 A
- [ ] 관련 이슈 생성
- [ ] API 스펙 확인 (B와 논의 필요 시)
- [ ] 브랜치 생성
- [ ] 작업 시작

### 개발자 B
- [ ] 관련 이슈 생성
- [ ] API 스펙 확인 (A와 논의 필요 시)
- [ ] 브랜치 생성
- [ ] 작업 시작

---

## 🎯 성공 지표

### 일일 목표
- **커밋**: 각자 최소 1회
- **PR**: 1-2일마다 1개
- **리뷰**: 24시간 이내

### 주간 목표
- **완료된 이슈**: 각자 3-5개
- **코드 리뷰**: 각자 3-5개
- **충돌 해결**: 즉시 (1시간 이내)

---

## 📚 참고 문서

- 전체 협업 전략: [TEAM_COLLABORATION.md](TEAM_COLLABORATION.md)
- 빠른 시작: [QUICK_START_COLLABORATION.md](QUICK_START_COLLABORATION.md)
- GitHub Projects 설정: [GITHUB_PROJECTS_SETUP.md](GITHUB_PROJECTS_SETUP.md)
- 주간 계획 템플릿: [WEEKLY_PLANNING.md](WEEKLY_PLANNING.md)
- 일일 스탠드업: [DAILY_STANDUP.md](DAILY_STANDUP.md)
- Backend TODO: [TODO_MOBY_BACKEND.md](../TODO_MOBY_BACKEND.md)

---

**마지막 업데이트**: 2025-01-XX

