# 📋 현재 프로젝트 상태 기반 업무 분담

**작성일**: 2025-01-XX  
**기준**: 현재 구현된 코드 상태를 기반으로 한 구체적인 작업 분담

---

## 🔍 현재 프로젝트 상태 분석

### ✅ 이미 구현된 것

**Backend Core:**
- ✅ MQTT 클라이언트 기본 구조 (`mqtt_client.py`) - 재연결 로직 일부 구현됨
- ✅ Alert Engine 기본 구조 (`alert_engine.py`)
- ✅ InfluxDB 클라이언트 기본 구조 (`influx_client.py`)
- ✅ LLM 클라이언트 기본 구조 (`llm_client.py`)
- ✅ API 라우터: `/alerts`, `/sensors`
- ✅ FastAPI 앱 설정 및 lifespan 관리

**Tests:**
- ✅ `test_alert_engine.py` (일부)
- ✅ `test_anomaly_vector_service.py` (일부)

### ❌ 아직 없는 것

- ❌ Frontend (전체)
- ❌ MQTT exponential backoff 재연결 (개선 필요)
- ❌ InfluxDB 배치 쓰기
- ❌ 완전한 테스트 커버리지
- ❌ 에러 처리 표준화
- ❌ 로깅 표준화
- ❌ 환경 설정 관리 개선

---

## 👥 구체적인 업무 분담

### 👤 개발자 A: Backend Core / Data Pipeline Specialist

#### 📁 담당 파일 및 디렉토리

```
backend/api/services/
├── mqtt_client.py              ✅ A 소유 (개선 작업)
├── influx_client.py            ✅ A 소유 (개선 작업)
├── alert_engine.py             ✅ A 소유 (개선 작업)
├── anomaly_vector_service.py   ✅ A 소유
├── llm_client.py               ✅ A 소유
├── alerts_summary.py           ✅ A 소유
├── constants.py                ✅ A 소유
└── notifier_stub.py            ✅ A 소유

backend/api/
├── routes_alerts.py            ✅ A 소유
└── routes_sensors.py           ✅ A 소유

backend/api/services/schemas/
├── alert_request_schema.py     ✅ A 소유
├── alert_schema.py              ✅ A 소유
└── sensor_schema.py            ✅ A 소유

backend/api/services/schemas/models/core/
├── config.py                   ✅ A 소유 (개선 작업)
└── logger.py                   ✅ A 소유 (개선 작업)
```

---

#### 🎯 구체적인 작업 목록 (우선순위 순)

### 🔴 높은 우선순위 (1주차)

#### 작업 1: MQTT 재연결 로직 개선
**파일**: `backend/api/services/mqtt_client.py`  
**이슈 번호**: #10  
**예상 시간**: 1일

**현재 상태:**
- ✅ 기본 재연결 로직 있음 (`connect_with_retry`)
- ❌ exponential backoff 미구현
- ❌ 재연결 간격이 고정 (5초)

**작업 내용:**
- [ ] exponential backoff 구현 (1초 → 2초 → 4초 → 8초 → 16초)
- [ ] 재연결 상태 모니터링 개선
- [ ] 연결 실패 시 큐잉 로직 추가 (TODO 주석 참고)
- [ ] 로깅 개선

**완료 기준:**
- exponential backoff 동작 확인
- 재연결 로그 명확화
- 연결 실패 시 메시지 큐에 저장

---

#### 작업 2: InfluxDB 배치 쓰기 구현
**파일**: `backend/api/services/influx_client.py`  
**이슈 번호**: #11  
**예상 시간**: 1일

**현재 상태:**
- ✅ 기본 쓰기 기능 있음 (`write_point`)
- ❌ 배치 쓰기 없음
- ❌ 실패 시 재시도 없음

**작업 내용:**
- [ ] 배치 쓰기 로직 구현
- [ ] 버퍼 크기 설정 (예: 100개 또는 5초마다)
- [ ] 주기적 플러시 로직
- [ ] 쓰기 실패 시 재시도 로직
- [ ] 에러 처리 개선

**완료 기준:**
- 여러 포인트를 배치로 한 번에 쓰기
- 메모리 효율적 버퍼링
- 쓰기 실패 시 자동 재시도

---

#### 작업 3: Alert Engine 에러 처리 개선
**파일**: `backend/api/services/alert_engine.py`  
**이슈 번호**: #12  
**예상 시간**: 1일

**현재 상태:**
- ✅ 기본 로직 구현됨
- ❌ 에러 처리 표준화 필요
- ❌ LLM 요약 실패 시 fallback 없음

**작업 내용:**
- [ ] 커스텀 예외 클래스 정의 (`backend/api/core/exceptions.py` 생성)
- [ ] 에러 처리 표준화
- [ ] LLM 요약 실패 시 fallback 메시지
- [ ] 알람 ID 생성 전략 개선 (UUID 사용)
- [ ] 로깅 개선

**완료 기준:**
- 모든 에러 경로 처리
- 명확한 에러 메시지
- LLM 실패 시에도 알람 생성 가능

---

### 🟡 중간 우선순위 (2주차)

#### 작업 4: 환경 설정 관리 개선
**파일**: `backend/api/services/schemas/models/core/config.py`  
**이슈 번호**: #13  
**예상 시간**: 1일

**현재 상태:**
- ✅ 기본 설정 구조 있음
- ❌ 하드코딩된 기본값 ("your-api-key" 등)
- ❌ .env 파일 지원 없음

**작업 내용:**
- [ ] .env 파일 지원 추가
- [ ] 설정 검증 로직
- [ ] 환경별 설정 분리 (dev, staging, prod)
- [ ] 기본값 처리 개선

**완료 기준:**
- .env 파일로 설정 관리
- 설정 검증 동작
- 환경별 분리 가능

---

#### 작업 5: 로깅 표준화
**파일**: `backend/api/services/schemas/models/core/logger.py`  
**이슈 번호**: #14  
**예상 시간**: 1일

**현재 상태:**
- ✅ 기본 logger 있음
- ❌ 로깅 표준화 필요
- ❌ `alerts_summary.py`에 `print` 사용 중

**작업 내용:**
- [ ] 로깅 설정 통일
- [ ] 로그 레벨 관리
- [ ] 로그 포맷 표준화
- [ ] `alerts_summary.py`의 `print` 제거
- [ ] 파일 로깅 설정 (선택사항)

**완료 기준:**
- 모든 모듈에서 일관된 로깅
- 로그 레벨 적절히 사용
- 디버깅 용이

---

#### 작업 6: API 엔드포인트 개선
**파일**: `backend/api/routes_*.py`  
**이슈 번호**: #15  
**예상 시간**: 2일

**현재 상태:**
- ✅ 기본 엔드포인트 있음
- ❌ docstring 부족
- ❌ 에러 응답 표준화 필요

**작업 내용:**
- [ ] 모든 엔드포인트에 상세한 docstring 추가
- [ ] 에러 응답 표준화
- [ ] 응답 모델 명확화
- [ ] 의존성 주입 패턴 도입 (FastAPI Depends)

**완료 기준:**
- Swagger 문서 완성
- 일관된 에러 응답
- 코드 품질 향상

---

### 🟢 낮은 우선순위 (3주차 이후)

#### 작업 7: 성능 최적화
**이슈 번호**: #16  
**예상 시간**: 2일

- [ ] async/await 활용
- [ ] 데이터베이스 쿼리 최적화
- [ ] 캐싱 전략 (필요 시)

---

### 👤 개발자 B: Frontend / Integration / Testing Specialist

#### 📁 담당 파일 및 디렉토리

```
frontend/                       ✅ B 소유 (전체, 새로 생성)
├── src/
│   ├── components/
│   ├── pages/
│   ├── services/
│   ├── hooks/
│   ├── context/
│   └── utils/
└── package.json

backend/tests/                  ✅ B 소유 (전체)
├── test_alert_engine.py        ✅ B 소유 (확장)
├── test_anomaly_vector_service.py ✅ B 소유 (확장)
└── (새 테스트 파일들)

docs/                           ✅ B 소유 (대부분)
└── API_DOCUMENTATION.md         ✅ B 소유 (새로 생성)
```

---

#### 🎯 구체적인 작업 목록 (우선순위 순)

### 🔴 높은 우선순위 (1주차)

#### 작업 1: React 프로젝트 초기 설정
**디렉토리**: `frontend/` (새로 생성)  
**이슈 번호**: #20  
**예상 시간**: 1일

**작업 내용:**
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

**완료 기준:**
- 프로젝트 실행 가능
- 기본 라우팅 동작
- 폴더 구조 명확

---

#### 작업 2: API 서비스 레이어 구축
**디렉토리**: `frontend/src/services/`  
**이슈 번호**: #21  
**예상 시간**: 1일

**작업 내용:**
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

**완료 기준:**
- API 호출 가능
- 에러 처리 동작
- 타입 안정성 확보

---

#### 작업 3: 기본 레이아웃 컴포넌트
**디렉토리**: `frontend/src/components/`  
**이슈 번호**: #22  
**예상 시간**: 1일

**작업 내용:**
- [ ] Header 컴포넌트
- [ ] Sidebar 컴포넌트
- [ ] MainLayout 컴포넌트
- [ ] 기본 스타일링
- [ ] 반응형 디자인

**완료 기준:**
- 레이아웃 구조 완성
- 반응형 디자인
- 네비게이션 동작

---

### 🟡 중간 우선순위 (2주차)

#### 작업 4: AlertToast 컴포넌트 개발
**디렉토리**: `frontend/src/components/`  
**이슈 번호**: #23  
**예상 시간**: 2일

**작업 내용:**
- [ ] AlertToast 컴포넌트 구현
- [ ] 애니메이션 (fade-in/out)
- [ ] 다양한 Alert 레벨 스타일 (info, warning, error, critical)
- [ ] 자동 사라짐 기능
- [ ] 클릭 이벤트 처리
- [ ] 토스트 스택 관리 (여러 알림 동시 표시)

**완료 기준:**
- Alert 표시 동작
- 부드러운 애니메이션
- 반응형 디자인

---

#### 작업 5: WebSocket 클라이언트 구현
**디렉토리**: `frontend/src/services/`  
**이슈 번호**: #24  
**예상 시간**: 2일

**작업 내용:**
- [ ] WebSocket 연결 관리
- [ ] 실시간 Alert 수신
- [ ] 재연결 로직
- [ ] 에러 처리
- [ ] Context API로 상태 관리
- [ ] Hook 생성 (`useWebSocket`)

**완료 기준:**
- 실시간 Alert 수신
- 연결 끊김 시 자동 재연결
- 안정적인 연결 유지

---

#### 작업 6: Backend 테스트 확장
**디렉토리**: `backend/tests/`  
**이슈 번호**: #25  
**예상 시간**: 2일

**작업 내용:**
- [ ] `test_alert_engine.py` 확장
  - 다양한 임계값 시나리오 테스트
  - LLM 요약 실패 시나리오 테스트
  - 에러 처리 경로 테스트
- [ ] `test_mqtt_client.py` 생성
- [ ] `test_influx_client.py` 생성
- [ ] 통합 테스트 추가
- [ ] 테스트 커버리지 확인

**완료 기준:**
- 주요 기능 테스트 커버
- 테스트 자동 실행
- 커버리지 70% 이상

---

### 🟢 낮은 우선순위 (3주차 이후)

#### 작업 7: AlertsPanel 컴포넌트 개발
**이슈 번호**: #26  
**예상 시간**: 2일

- [ ] AlertsPanel 컴포넌트 구현
- [ ] Alert 목록 표시
- [ ] 필터링 기능
- [ ] 정렬 기능
- [ ] 페이지네이션

---

#### 작업 8: API 문서화
**이슈 번호**: #27  
**예상 시간**: 1일

- [ ] API 사용 가이드 작성
- [ ] 컴포넌트 문서화
- [ ] 통합 가이드 작성

---

## 🤝 공동 작업 (양쪽 모두 참여)

### 작업 9: API 통합 테스트
**이슈 번호**: #30  
**예상 시간**: 1일

**담당:**
- 개발자 A: Backend 준비 및 수정
- 개발자 B: Frontend 통합 및 테스트

**작업 내용:**
- [ ] Frontend-Backend 통합 테스트
- [ ] API 스펙 검증
- [ ] 에러 시나리오 테스트
- [ ] 성능 테스트

---

## 📅 주간 작업 계획 예시

### Week 1

**개발자 A:**
- 월: MQTT 재연결 로직 개선 (#10)
- 화: InfluxDB 배치 쓰기 (#11)
- 수: Alert Engine 에러 처리 (#12)
- 목: 환경 설정 개선 (#13)
- 금: 로깅 표준화 (#14)

**개발자 B:**
- 월: React 프로젝트 설정 (#20)
- 화: API 서비스 레이어 (#21)
- 수: 기본 레이아웃 (#22)
- 목: AlertToast 컴포넌트 시작 (#23)
- 금: AlertToast 컴포넌트 완료 (#23)

### Week 2

**개발자 A:**
- API 엔드포인트 개선 (#15)

**개발자 B:**
- WebSocket 클라이언트 (#24)
- Backend 테스트 확장 (#25)

**공동:**
- API 통합 테스트 (#30)

---

## 🚨 주의사항

### 공유 영역 (소통 필수)

다음 파일 수정 시 반드시 상대방과 논의:

- `backend/main.py` - 양쪽 모두 수정 가능
- `requirements.txt` - 의존성 추가 시 논의
- `.env.example` - 환경 변수 추가 시 논의
- `README.md` - 문서 업데이트 시 논의

### API 스펙 변경

- Backend API 변경 시: 개발자 A가 이슈 생성 → 개발자 B 확인
- Frontend 요구사항: 개발자 B가 이슈 생성 → 개발자 A 확인

---

## ✅ 체크리스트: 작업 시작 전

### 개발자 A
- [ ] GitHub Projects 보드 확인
- [ ] 이슈 #10, #11, #12 생성
- [ ] 브랜치 생성: `feature/a-mqtt-reconnection`
- [ ] 작업 시작

### 개발자 B
- [ ] GitHub Projects 보드 확인
- [ ] 이슈 #20, #21, #22 생성
- [ ] 브랜치 생성: `feature/b-react-setup`
- [ ] 작업 시작

---

**이제 구체적인 작업을 시작하세요!** 🚀

각 작업은 GitHub Issue로 생성하고, Projects 보드에서 추적하세요.

