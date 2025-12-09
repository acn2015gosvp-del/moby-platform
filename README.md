# MOBY Platform

**Industrial IoT & Predictive Maintenance Platform**

---

## 📦 프로젝트 개요

MOBY는 산업용 IoT 예측 정비 플랫폼으로, 다양한 센서 데이터를 실시간으로 수집·분석하여 설비의 이상 징후를 조기에 감지하고 자동화된 알림 및 보고서를 제공합니다.

### 핵심 목적

- **실시간 모니터링**: 다중 센서 데이터 수집 및 시각화
- **예측 정비**: ML/LLM 기반 이상 탐지 및 조기 경고
- **자동화된 보고서**: Gemini API를 활용한 일일/주간 보고서 자동 생성
- **통합 알림 시스템**: WebSocket, 이메일, 메신저를 통한 다채널 알림 전송

### 주요 기능

- ✅ **다중 센서 데이터 수집**: 진동, 소리, 온도/습도, 가속도계/자이로스코프
- ✅ **실시간 데이터 파이프라인**: MQTT → FastAPI → InfluxDB → Grafana
- ✅ **Grafana 대시보드 임베딩**: iframe을 통한 실시간 대시보드 표시 및 자동 새로고침
- ✅ **WebSocket 실시간 알림**: FastAPI WebSocket을 통한 실시간 알림 수신 및 토스트 표시
- ✅ **알림 엔진**: 규칙 기반 + ML/LLM 기반 이상 탐지 (벡터 기반 이상 탐지)
- ✅ **LLM 기반 보고서**: Gemini API를 사용한 일일/주간 자동 보고서 생성 및 PDF 다운로드
- ✅ **설비 관리**: 설비 추가/삭제, 상태 모니터링, 실시간 알림
- ✅ **역할 기반 접근 제어 (RBAC)**: 사용자 인증 및 권한 관리
- ✅ **Grafana Webhook 연동**: Grafana Alerting과의 실시간 연동
- ✅ **이메일/메신저 알림**: SMTP 이메일 및 Slack/Telegram 메신저 알림 지원

---

## 🏗️ 시스템 아키텍처

```
┌─────────┐      ┌─────────┐      ┌─────────┐      ┌──────────┐
│ 센서    │ ───> │  MQTT   │ ───> │ FastAPI │ ───> │ InfluxDB │
│ (Edge)  │      │ Broker  │      │ Backend │      │  2.x     │
└─────────┘      └─────────┘      └─────────┘      └──────────┘
                                                           │
                                                           ▼
                                                    ┌──────────┐
                                                    │ Grafana  │
                                                    │ Dashboard│
                                                    └──────────┘
                                                           │
                    ┌──────────────────────────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   Alert Engine       │
         │  (Rule + ML/LLM)     │
         └──────────────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
         ▼                     ▼
    ┌─────────┐         ┌──────────┐
    │WebSocket│         │  Email   │
    │  Alert  │         │ Messenger │
    └─────────┘         └──────────┘
         │
         ▼
    ┌──────────┐
    │ Frontend │
    │  React   │
    └──────────┘
         │
         ▼
    ┌──────────┐
    │  LLM     │
    │ (Gemini) │
    └──────────┘
         │
         ▼
    ┌──────────┐
    │  Report  │
    │  (PDF)   │
    └──────────┘
```

### 데이터 흐름

1. **센서 데이터 수집**: Edge 장치에서 MQTT 브로커로 센서 데이터 전송
2. **데이터 저장**: FastAPI가 MQTT 메시지를 수신하여 InfluxDB에 저장
3. **시각화**: Grafana가 InfluxDB에서 데이터를 읽어 대시보드로 표시
4. **이상 탐지**: Alert Engine이 규칙 기반 및 ML 기반 이상 탐지 수행
5. **실시간 알림**: WebSocket을 통해 프론트엔드로 실시간 알림 전송
6. **보고서 생성**: Gemini API를 사용하여 일일/주간 보고서 자동 생성

---

## 🔧 기술 스택

### Backend

| 카테고리 | 기술 | 버전 |
|---------|------|------|
| **Framework** | FastAPI | ≥0.104.0 |
| **ASGI Server** | Uvicorn | ≥0.24.0 |
| **Database** | SQLite (SQLAlchemy) | ≥2.0.0 |
| **Time-Series DB** | InfluxDB | 2.x |
| **Message Queue** | MQTT (paho-mqtt) | ≥1.6.1 |
| **LLM** | Google Gemini API | ≥0.3.0 |
| **Validation** | Pydantic | ≥2.0.0 |
| **Authentication** | JWT (python-jose) | ≥3.3.0 |
| **Scheduling** | APScheduler | ≥3.10.0 |
| **PDF Generation** | ReportLab | ≥4.0.0 |
| **Data Analysis** | Pandas, NumPy | ≥2.0.0, ≥1.24.0 |
| **Monitoring** | Prometheus | ≥6.1.0 |

### Frontend

| 카테고리 | 기술 | 버전 |
|---------|------|------|
| **Framework** | React | 19.2.0 |
| **Build Tool** | Vite | 7.2.2 |
| **Language** | TypeScript | 5.9.3 |
| **Routing** | React Router | 7.9.6 |
| **HTTP Client** | Axios | 1.13.2 |
| **Styling** | Tailwind CSS | 4.1.17 |
| **State Management** | React Context API | - |
| **Real-time** | WebSocket (react-toastify) | 11.0.5 |
| **PDF Generation** | html2canvas + jsPDF | 1.4.1, 3.0.4 |
| **Markdown** | marked | 17.0.1 |

### Infrastructure

| 서비스 | 용도 |
|--------|------|
| **Grafana** | 시각화 및 대시보드 |
| **Mosquitto** | MQTT 브로커 |
| **InfluxDB 2.x** | 시계열 데이터베이스 |
| **Docker** | 컨테이너화 및 배포 |

---

## 📁 프로젝트 구조

```
moby-platform/
├── backend/                      # FastAPI 백엔드
│   ├── api/                     # API 라우터 및 핵심 모듈
│   │   ├── routes_*.py          # 엔드포인트 정의
│   │   │   ├── routes_auth.py    # 인증 (회원가입, 로그인, 토큰 갱신)
│   │   │   ├── routes_alerts.py  # 알림 (생성, 조회, 확인)
│   │   │   ├── routes_sensors.py # 센서 데이터 수신 및 상태 조회
│   │   │   ├── routes_reports.py # 보고서 생성
│   │   │   ├── routes_health.py  # 헬스체크 및 모니터링
│   │   │   ├── routes_grafana.py # Grafana 연동 및 Webhook
│   │   │   ├── routes_websocket.py # WebSocket 실시간 알림
│   │   │   ├── routes_webhook.py # Webhook 엔드포인트
│   │   │   └── routes_grafana_proxy.py # Grafana API 프록시
│   │   ├── core/                # 공통 모듈
│   │   │   ├── api_exceptions.py # 커스텀 예외 처리
│   │   │   ├── responses.py      # 표준 응답 형식
│   │   │   └── permissions.py   # 권한 관리
│   │   ├── middleware/           # 미들웨어
│   │   │   ├── timing.py         # 응답 시간 측정
│   │   │   ├── rate_limit.py    # Rate Limiting
│   │   │   └── csrf.py          # CSRF 방지
│   │   ├── models/              # 데이터베이스 모델
│   │   │   ├── user.py          # 사용자 모델
│   │   │   ├── role.py          # 역할 및 권한 모델
│   │   │   ├── alert.py         # 알림 모델
│   │   │   └── alert_history.py # 알림 이력 모델
│   │   └── services/            # 비즈니스 로직
│   │       ├── alert_engine.py  # 알림 엔진 (벡터 기반 이상 탐지)
│   │       ├── alert_storage.py # 알림 저장소
│   │       ├── alert_history_service.py # 알림 이력 관리
│   │       ├── alert_priority_service.py # 알림 우선순위 처리
│   │       ├── alert_state_manager.py # 알림 상태 관리
│   │       ├── influx_client.py # InfluxDB 클라이언트
│   │       ├── mqtt_client.py   # MQTT 클라이언트
│   │       ├── mqtt_ai_subscriber.py # MQTT AI 구독자
│   │       ├── report_generator.py # LLM 기반 보고서 생성기
│   │       ├── report_service.py # 보고서 서비스
│   │       ├── pdf_generator.py # PDF 생성기
│   │       ├── llm_client.py    # LLM 클라이언트
│   │       ├── grafana_client.py # Grafana 클라이언트
│   │       ├── websocket_notifier.py # WebSocket 알림 전송
│   │       ├── email_service.py  # 이메일 알림 서비스
│   │       ├── messenger_service.py # 메신저 알림 서비스
│   │       ├── auth_service.py  # 인증 서비스
│   │       ├── database.py      # 데이터베이스 초기화
│   │       ├── scheduler.py      # 스케줄러 (일일 보고서 자동 생성)
│   │       ├── cache.py         # 캐시 관리
│   │       └── schemas/         # Pydantic 스키마
│   │           ├── alert_schema.py
│   │           ├── sensor_schema.py
│   │           ├── user_schema.py
│   │           └── models/       # 설정 및 로거
│   │               └── core/
│   │                   ├── config.py # 환경 설정
│   │                   └── logger.py # 로깅 설정
│   ├── main.py                   # FastAPI 앱 진입점
│   └── tests/                    # 테스트 코드
├── frontend/                     # React/Vite 프론트엔드
│   ├── src/
│   │   ├── components/           # UI 컴포넌트
│   │   │   ├── alerts/           # 알림 관련 컴포넌트
│   │   │   │   ├── AlertsPanel.tsx
│   │   │   │   ├── AlertTicker.tsx
│   │   │   │   ├── AlertToast.tsx
│   │   │   │   └── WebSocketToast.tsx
│   │   │   ├── auth/             # 인증 컴포넌트
│   │   │   │   └── ProtectedRoute.tsx
│   │   │   ├── layout/           # 레이아웃 컴포넌트
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── MainLayout.tsx
│   │   │   └── common/           # 공통 컴포넌트
│   │   │       ├── Button.tsx
│   │   │       ├── Loading.tsx
│   │   │       └── MobyLogo.tsx
│   │   ├── pages/                # 페이지 컴포넌트
│   │   │   ├── Login.tsx         # 로그인 페이지
│   │   │   ├── Register.tsx      # 회원가입 페이지
│   │   │   ├── EquipmentList.tsx # 설비 목록 페이지
│   │   │   ├── Dashboard.tsx     # Grafana 대시보드 임베딩
│   │   │   ├── Alerts.tsx        # 알림 목록 페이지
│   │   │   ├── Sensors.tsx       # 센서 상태 페이지
│   │   │   ├── Reports.tsx       # 보고서 생성 페이지
│   │   │   └── Monitoring.tsx   # 모니터링 페이지
│   │   ├── services/            # API 서비스
│   │   │   ├── api/             # API 클라이언트
│   │   │   │   └── client.ts
│   │   │   ├── auth/            # 인증 서비스
│   │   │   │   └── authService.ts
│   │   │   ├── alerts/           # 알림 서비스
│   │   │   │   └── alertService.ts
│   │   │   ├── sensors/         # 센서 서비스
│   │   │   │   └── sensorService.ts
│   │   │   └── reports/         # 보고서 서비스
│   │   │       └── reportService.ts
│   │   ├── hooks/               # 커스텀 훅
│   │   │   ├── useWebSocket.ts  # WebSocket 연결 훅
│   │   │   └── useImagePreloader.ts
│   │   ├── context/             # React Context
│   │   │   ├── AuthContext.tsx  # 인증 컨텍스트
│   │   │   ├── DeviceContext.tsx # 설비 컨텍스트
│   │   │   ├── WebSocketContext.tsx # WebSocket 컨텍스트
│   │   │   ├── ThemeContext.tsx  # 테마 컨텍스트
│   │   │   └── AlertMuteContext.tsx # 알림 음소거 컨텍스트
│   │   ├── utils/               # 유틸리티 함수
│   │   │   ├── constants.ts     # 상수 정의
│   │   │   ├── grafana.ts      # Grafana 설정 및 API
│   │   │   ├── formatters.ts   # 포맷터
│   │   │   ├── errorHandler.ts # 에러 핸들러
│   │   │   └── pdfGenerator.ts # PDF 생성 유틸리티
│   │   └── types/               # TypeScript 타입 정의
│   │       ├── alert.ts
│   │       ├── auth.ts
│   │       ├── sensor.ts
│   │       └── api.ts
│   ├── public/                  # 정적 파일
│   └── package.json
├── docs/                        # 프로젝트 문서
│   ├── API_DOCUMENTATION.md     # API 상세 문서
│   ├── DEPLOYMENT_GUIDE.md      # 배포 가이드
│   ├── CI_CD_GUIDE.md           # CI/CD 가이드
│   └── ...                      # 기타 문서들
├── docker/                      # Docker 설정
│   └── mosquitto/               # MQTT 브로커 설정
├── scripts/                     # 유틸리티 스크립트
│   ├── edit_env.py              # .env 파일 안전 편집 도구
│   └── check_grafana_embedding.py # Grafana 임베딩 확인
├── docker-compose.yml           # 프로덕션 Docker Compose
├── docker-compose.dev.yml       # 개발 환경 Docker Compose
├── requirements.txt             # Python 의존성
└── env.example                  # 환경 변수 예시 파일
```

---

## 🚀 설치 및 실행 가이드

### 사전 요구사항

- **Python**: 3.9 이상
- **Node.js**: 18 이상 및 npm/yarn
- **InfluxDB**: 2.x
- **MQTT Broker**: Mosquitto 등
- **Grafana**: 대시보드 시각화 (선택사항)
- **Google Gemini API 키**: 보고서 생성 기능 사용 시 (필수)

### 1. 저장소 클론

```bash
git clone https://github.com/your-org/moby-platform.git
cd moby-platform
```

### 2. 백엔드 설정

#### 가상 환경 생성 및 활성화

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 의존성 설치

```bash
pip install -r requirements.txt
```

#### 환경 변수 설정

`env.example` 파일을 참고하여 `.env` 파일을 생성하고 다음 내용을 설정하세요:

```env
# MQTT 설정
MQTT_HOST=localhost
MQTT_PORT=1883

# InfluxDB 설정
INFLUX_URL=http://localhost:8086
INFLUX_TOKEN=your_influxdb_api_token_here
INFLUX_ORG=your_organization_name
INFLUX_BUCKET=your_bucket_name_for_sensors

# Grafana 설정 (선택사항)
GRAFANA_URL=http://192.168.80.183:8080
GRAFANA_API_KEY=your-grafana-api-key-here
GRAFANA_ORG_ID=1

# Gemini API 설정 (보고서 생성용)
GEMINI_API_KEY=your-gemini-api-key-here

# 인증 설정
SECRET_KEY=your-secret-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 환경 설정
ENVIRONMENT=dev
LOG_LEVEL=INFO
DEBUG=false

# 이메일 알림 설정 (선택사항)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_TO_EMAILS=recipient1@example.com,recipient2@example.com
```

**참고**: `env.example` 파일을 복사하여 `.env` 파일을 만들 수 있습니다:

```bash
# Windows
copy env.example .env

# Linux/Mac
cp env.example .env
```

#### 백엔드 서버 실행

```bash
# ⚠️ 중요: 프로젝트 루트 디렉토리에서 실행해야 합니다!
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면 다음 주소에서 API 문서를 확인할 수 있습니다:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. 프론트엔드 설정

#### 의존성 설치

```bash
cd frontend
npm install  # 또는 yarn install
```

#### 환경 변수 설정 (선택사항)

프론트엔드에서 환경 변수를 사용하려면 `.env` 파일을 생성하세요:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_GRAFANA_BASE_URL=http://192.168.80.183:8080
VITE_GRAFANA_API_KEY=your-grafana-api-key
```

#### 개발 서버 실행

```bash
npm run dev  # 또는 yarn dev
```

프론트엔드가 실행되면 다음 주소에서 접근할 수 있습니다:
- **개발 서버**: http://localhost:5173

### 4. Docker를 사용한 실행 (선택사항)

#### 프로덕션 환경

```bash
# 환경 변수 설정
cp env.example .env
# .env 파일 편집 (필수 값 설정)

# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

#### 개발 환경

```bash
# 개발 환경용 Docker Compose 사용 (코드 변경 즉시 반영)
docker-compose -f docker-compose.dev.yml up -d
```

---

## ✨ 변경 사항 및 구현 기능

### 🎯 핵심 구현 기능

#### 1. 인증 및 권한 관리
- ✅ JWT 기반 인증 시스템
- ✅ 역할 기반 접근 제어 (RBAC): Admin, User, Viewer
- ✅ 회원가입, 로그인, 토큰 갱신
- ✅ 사용자 관리 (관리자 전용)

#### 2. 센서 데이터 관리
- ✅ REST API를 통한 센서 데이터 수신
- ✅ MQTT 브로커를 통한 실시간 데이터 수집
- ✅ InfluxDB에 시계열 데이터 저장
- ✅ 센서 상태 조회 및 모니터링

#### 3. 알림 시스템
- ✅ **벡터 기반 이상 탐지**: L2 norm 계산을 통한 이상 탐지
- ✅ **규칙 기반 알림**: 임계값 기반 알림 생성
- ✅ **ML/LLM 기반 알림 요약**: Gemini API를 활용한 알림 요약 생성
- ✅ **알림 상태 관리**: pending → acknowledged → resolved
- ✅ **WebSocket 실시간 알림**: 프론트엔드로 실시간 알림 전송
- ✅ **이메일 알림**: SMTP를 통한 이메일 알림 전송
- ✅ **메신저 알림**: Slack, Telegram 알림 지원
- ✅ **Grafana Webhook 연동**: Grafana Alerting과의 실시간 연동

#### 4. 보고서 생성
- ✅ **LLM 기반 보고서 생성**: Gemini API를 사용한 자동 보고서 생성
- ✅ **일일/주간 보고서**: 기간별 보고서 생성
- ✅ **PDF 다운로드**: ReportLab을 사용한 PDF 생성
- ✅ **자동 스케줄링**: APScheduler를 통한 일일 보고서 자동 생성

#### 5. Grafana 연동
- ✅ **대시보드 임베딩**: iframe을 통한 Grafana 대시보드 표시
- ✅ **Grafana API 프록시**: CORS 문제 해결을 위한 프록시 서버
- ✅ **Grafana Webhook 수신**: Grafana Alerting 알림 수신 및 처리
- ✅ **데이터 소스 관리**: Grafana 데이터 소스 생성 및 관리

#### 6. 실시간 통신
- ✅ **WebSocket 서버**: FastAPI WebSocket을 통한 실시간 통신
- ✅ **WebSocket 클라이언트**: React에서 WebSocket 연결 및 알림 수신
- ✅ **연결 관리**: 자동 재연결 및 연결 상태 관리

#### 7. 모니터링 및 헬스체크
- ✅ **시스템 헬스체크**: 전체 시스템 상태 확인
- ✅ **서비스별 헬스체크**: MQTT, InfluxDB, Database, Grafana 상태 확인
- ✅ **Kubernetes 프로브**: Liveness 및 Readiness 프로브 지원
- ✅ **Prometheus 메트릭**: 성능 메트릭 수집

#### 8. 보안 및 성능
- ✅ **Rate Limiting**: 요청 제한 미들웨어
- ✅ **CSRF 방지**: 프로덕션 환경에서 CSRF 보호
- ✅ **응답 시간 측정**: 요청 응답 시간 모니터링
- ✅ **캐시 관리**: 센서 상태 등 자주 조회되는 데이터 캐싱

### 📝 주요 변경 사항

#### 2025년 주요 개선사항

1. **웹서버 구현 완료**
   - ✅ FastAPI 백엔드 API 완전 구현
   - ✅ React 프론트엔드 완전 구현
   - ✅ WebSocket 실시간 알림 시스템 구축
   - ✅ Grafana 대시보드 임베딩 완료

2. **인증 및 권한 시스템**
   - ✅ JWT 기반 인증 구현
   - ✅ 역할 기반 접근 제어 (RBAC) 구현
   - ✅ 사용자 관리 API 구현

3. **알림 시스템 고도화**
   - ✅ 벡터 기반 이상 탐지 엔진 구현
   - ✅ Grafana Webhook 연동 완료
   - ✅ 다채널 알림 전송 (WebSocket, 이메일, 메신저)

4. **보고서 생성 시스템**
   - ✅ Gemini API 통합 완료
   - ✅ PDF 생성 기능 구현
   - ✅ 자동 스케줄링 구현

5. **프론트엔드 개선**
   - ✅ TypeScript 엄격 모드 적용
   - ✅ 컴포넌트 구조 최적화
   - ✅ WebSocket 실시간 알림 UI 구현

---

## 📚 API 명세

### 인증 API (`/auth`)

| Method | Endpoint | 기능 설명 | Request Body/Params | Response |
|--------|----------|-----------|-------------------|----------|
| POST | `/auth/register` | 회원가입 | `UserCreate` (email, username, password) | `SuccessResponse[UserResponse]` |
| POST | `/auth/login` | 로그인 | `UserLogin` (email, password) | `SuccessResponse[Token]` |
| GET | `/auth/me` | 현재 사용자 정보 조회 | - (JWT 토큰 필요) | `SuccessResponse[UserResponse]` |
| POST | `/auth/refresh` | 토큰 갱신 | - (JWT 토큰 필요) | `SuccessResponse[Token]` |
| GET | `/auth/permissions` | 현재 사용자 권한 조회 | - (JWT 토큰 필요) | `SuccessResponse[dict]` |
| GET | `/auth/users` | 사용자 목록 조회 (관리자 전용) | `skip`, `limit` (쿼리 파라미터) | `SuccessResponse[List[UserResponse]]` |
| PATCH | `/auth/users/{user_id}/role` | 사용자 역할 변경 (관리자 전용) | `user_id` (경로), `new_role` (쿼리) | `SuccessResponse[UserResponse]` |

### 알림 API (`/alerts`)

| Method | Endpoint | 기능 설명 | Request Body/Params | Response |
|--------|----------|-----------|-------------------|----------|
| POST | `/alerts/evaluate` | 알림 생성 및 평가 | `AlertRequest` (vector, threshold, sensor_id 등) | `SuccessResponse[AlertPayloadModel]` |
| POST | `/alerts/evaluate-legacy` | 알림 생성 및 평가 (레거시 형식) | `AlertRequest` | `SuccessResponse[AlertResponse]` |
| GET | `/alerts/latest` | 최신 알림 목록 조회 | `limit`, `sensor_id`, `level` (쿼리 파라미터) | `SuccessResponse[List[AlertPayloadModel]]` |
| GET | `/alerts/unchecked` | 미확인 알림 목록 조회 | `limit` (쿼리 파라미터) | `SuccessResponse[List[Dict]]` |
| POST | `/alerts/check` | 알림 확인 처리 | `alert_id` (경로 파라미터) | `SuccessResponse[Dict]` |
| DELETE | `/alerts/all` | 전체 알림 삭제 | - (관리자 권한 필요) | `SuccessResponse[Dict]` |

### 센서 API (`/sensors`)

| Method | Endpoint | 기능 설명 | Request Body/Params | Response |
|--------|----------|-----------|-------------------|----------|
| POST | `/sensors/data` | 센서 데이터 수신 | `SensorData` (device_id, temperature, humidity 등) | `SuccessResponse[SensorDataResponse]` |
| GET | `/sensors/status` | 센서 상태 조회 | - | `SuccessResponse[SensorStatusResponse]` |

### 보고서 API (`/reports`)

| Method | Endpoint | 기능 설명 | Request Body/Params | Response |
|--------|----------|-----------|-------------------|----------|
| POST | `/reports/generate` | 보고서 생성 | `ReportRequest` (period_start, period_end, equipment 등), `format` (쿼리: json/pdf) | `SuccessResponse[ReportResponse]` 또는 `FileResponse` (PDF) |

### 헬스체크 API (`/health`)

| Method | Endpoint | 기능 설명 | Request Body/Params | Response |
|--------|----------|-----------|-------------------|----------|
| GET | `/health` | 시스템 헬스체크 | - | `SuccessResponse[HealthResponse]` |
| GET | `/health/liveness` | Liveness 프로브 | - | `SuccessResponse` |
| GET | `/health/readiness` | Readiness 프로브 | - | `SuccessResponse` |

### Grafana API (`/grafana`)

| Method | Endpoint | 기능 설명 | Request Body/Params | Response |
|--------|----------|-----------|-------------------|----------|
| GET | `/grafana/health` | Grafana 연결 상태 확인 | - | `SuccessResponse` |
| POST | `/grafana/datasources` | 데이터 소스 생성 | `DatasourceCreateRequest` | `SuccessResponse` |
| GET | `/grafana/datasources/{name}` | 데이터 소스 조회 | `name` (경로 파라미터) | `SuccessResponse` |
| POST | `/grafana/dashboards` | 대시보드 생성 | `DashboardCreateRequest` | `SuccessResponse` |
| POST | `/grafana/webhook/alert` | Grafana Webhook 수신 (알림) | `Dict[str, Any]` (Grafana Webhook 형식) | `SuccessResponse` |
| POST | `/grafana/webhook/grafana` | Grafana Webhook 수신 (별칭) | `Dict[str, Any]` (Grafana Webhook 형식) | `SuccessResponse` |

### Grafana 프록시 API (`/api/proxy-grafana`)

| Method | Endpoint | 기능 설명 | Request Body/Params | Response |
|--------|----------|-----------|-------------------|----------|
| GET | `/api/proxy-grafana/dashboard/{dashboard_uid}` | Grafana 대시보드 정보 조회 (프록시) | `dashboard_uid` (경로), `org_id` (쿼리) | `SuccessResponse[Dict]` |
| GET | `/api/proxy-grafana/health` | Grafana 서버 상태 확인 (프록시) | - | `SuccessResponse[Dict]` |

### WebSocket API

| Method | Endpoint | 기능 설명 | Request Body/Params | Response |
|--------|----------|-----------|-------------------|----------|
| WebSocket | `/ws` | WebSocket 실시간 알림 연결 | - | JSON 메시지 (실시간) |
| WebSocket | `/ws/alerts` | WebSocket 실시간 알림 연결 (별칭) | - | JSON 메시지 (실시간) |

### Webhook API (`/api`)

| Method | Endpoint | 기능 설명 | Request Body/Params | Response |
|--------|----------|-----------|-------------------|----------|
| POST | `/api/webhook/grafana` | Grafana Webhook 수신 (명세서 요구사항) | `Dict[str, Any]` (Grafana Webhook 형식) | `SuccessResponse` |

### 테스트 API

| Method | Endpoint | 기능 설명 | Request Body/Params | Response |
|--------|----------|-----------|-------------------|----------|
| POST | `/test-alert` | WebSocket 알림 전송 테스트 | `alert_type`, `message` (쿼리 파라미터) | `Dict` |

---

## 🧪 테스트

### 백엔드 테스트

```bash
pytest
```

### 프론트엔드 테스트

```bash
cd frontend
npm run build  # TypeScript 컴파일 및 빌드 검증
npm run lint   # ESLint 검사
```

---

## 🔄 CI/CD

프로젝트는 GitHub Actions를 통해 자동화된 CI/CD 파이프라인을 사용합니다:

- **Frontend Tests**: TypeScript 컴파일 및 린트 검사
- **Backend Tests**: pytest를 통한 단위 테스트
- **Code Linting**: 코드 스타일 검사
- **Security Scan**: 보안 취약점 검사
- **Docker Build**: Docker 이미지 빌드 및 푸시

자세한 내용은 [CI/CD 가이드](docs/CI_CD_GUIDE.md)를 참고하세요.

---

## 📝 문서

### API 문서
- **상세 문서**: [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)
- **Swagger UI**: http://localhost:8000/docs (개발 서버 실행 후)
- **ReDoc**: http://localhost:8000/redoc

### 추가 가이드
- **보고서 생성 가이드**: [docs/REPORT_GENERATION_GUIDE.md](docs/REPORT_GENERATION_GUIDE.md)
- **모니터링 가이드**: [docs/MONITORING_GUIDE.md](docs/MONITORING_GUIDE.md)
- **데이터베이스 마이그레이션**: [docs/DATABASE_MIGRATION.md](docs/DATABASE_MIGRATION.md)
- **CI/CD 가이드**: [docs/CI_CD_GUIDE.md](docs/CI_CD_GUIDE.md)
- **Grafana 임베딩 가이드**: [docs/GRAFANA_EMBEDDING_SETUP.md](docs/GRAFANA_EMBEDDING_SETUP.md)
- **배포 가이드**: [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)

---

## 🤝 협업 가이드

프로젝트에 기여하고 싶으시다면 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고해주세요.

### 브랜치 전략

- `main`: 프로덕션 배포용 브랜치
- `develop`: 개발 통합 브랜치
- `feature/*`: 새로운 기능 개발
- `fix/*`: 버그 수정
- `docs/*`: 문서 작업

### 커밋 메시지 규칙

커밋 메시지는 다음 형식을 따릅니다:

```
<type>: <subject>

<body>

<footer>
```

**Type 종류:**
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 포맷팅
- `refactor`: 코드 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드 설정 등

---

## 📄 라이선스

[라이선스 정보를 추가하세요]

---

## 👥 팀

[팀원 정보를 추가하세요]

---

## 📞 문의

[문의 방법을 추가하세요]
