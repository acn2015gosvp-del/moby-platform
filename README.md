# MOBY Platform

Industrial IoT & Predictive Maintenance Platform

## 📦 프로젝트 개요

MOBY는 산업용 IoT 예측 정비 플랫폼입니다. 다양한 센서 데이터를 수집하고 분석하여 이상 징후를 감지하고 알림을 제공합니다.

### 주요 기능

- **다중 센서 데이터 수집**: 진동, 소리, 온도/습도, 가속도계/자이로스코프, 사이클 카운트
- **실시간 데이터 파이프라인**: MQTT → FastAPI → InfluxDB
- **Grafana 대시보드**: 시계열 데이터 시각화
- **알림 엔진**: 규칙 기반 + ML/LLM 기반 이상 탐지
- **LLM 기반 보고서**: Gemini API를 사용한 일일/주간 자동 보고서 생성
- **웹 프론트엔드**: React/Vite 기반 알림, 대시보드, 보고서 UI

## 🏗️ 시스템 아키텍처

```
센서 → MQTT → FastAPI → InfluxDB → Grafana → Alert Engine → LLM → Frontend
```

## 📁 프로젝트 구조

```
moby-platform/
├── backend/              # FastAPI 백엔드
│   ├── api/             # API 라우터
│   │   ├── routes_*.py  # 엔드포인트 정의
│   │   ├── core/        # 공통 모듈 (예외, 응답)
│   │   └── services/    # 비즈니스 로직
│   │       ├── alert_engine.py
│   │       ├── influx_client.py
│   │       ├── mqtt_client.py
│   │       ├── llm_client.py
│   │       └── schemas/ # 데이터 모델
│   ├── main.py          # FastAPI 앱 진입점
│   └── tests/           # 테스트 코드
├── frontend/            # React/Vite 프론트엔드
│   ├── src/
│   │   ├── components/  # UI 컴포넌트
│   │   ├── pages/       # 페이지 컴포넌트
│   │   ├── services/    # API 서비스
│   │   ├── hooks/       # 커스텀 훅
│   │   └── types/       # TypeScript 타입
│   └── package.json
├── docs/                # 프로젝트 문서
│   ├── API_DOCUMENTATION.md
│   ├── BACKEND_WORK_STATUS.md
│   └── FRONTEND_TEMPLATE_REQUIREMENTS.md
└── scripts/             # 유틸리티 스크립트
```

## 🚀 시작하기

### 사전 요구사항

- Python 3.9 이상
- InfluxDB 2.x
- MQTT Broker (Mosquitto 등)
- OpenAI API 키 (LLM 기능 사용 시)

### 설치

1. 저장소 클론
```bash
git clone https://github.com/your-org/moby-platform.git
cd moby-platform
```

2. 가상 환경 생성 및 활성화
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정
`env.example` 파일을 참고하여 `.env` 파일을 생성하고 다음 내용을 설정하세요:
```env
MQTT_HOST=localhost
MQTT_PORT=1883
INFLUX_URL=http://localhost:8086
INFLUX_TOKEN=your-token
INFLUX_ORG=your-org
OPENAI_API_KEY=your-api-key
ENVIRONMENT=dev
LOG_LEVEL=INFO
DEBUG=false
```

**참고**: `env.example` 파일을 복사하여 `.env` 파일을 만들 수 있습니다:
```bash
cp env.example .env
```

5. 서버 실행
```bash
# ⚠️ 중요: 프로젝트 루트 디렉토리에서 실행해야 합니다!
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
```

서버가 실행되면 다음 주소에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

**참고**: 상세한 실행 가이드는 [빠른 시작 가이드](docs/QUICK_START.md)를 참고하세요.

## 🧪 테스트

```bash
pytest
```

## 🤝 협업 가이드

프로젝트에 기여하고 싶으시다면 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고해주세요.

### 팀 협업 전략
두 명이서 효율적으로 협업하기 위한 전략은 [docs/TEAM_COLLABORATION.md](docs/TEAM_COLLABORATION.md)를 참고하세요.

**전략 1: 기능별 분담 (추천)**
- 상세 가이드라인: [docs/STRATEGY_1_GUIDELINE.md](docs/STRATEGY_1_GUIDELINE.md)
- 작업 할당 예시: [docs/STRATEGY_1_WORK_ASSIGNMENT.md](docs/STRATEGY_1_WORK_ASSIGNMENT.md)
- 빠른 시작: [docs/QUICK_START_COLLABORATION.md](docs/QUICK_START_COLLABORATION.md)

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

**예시:**
```
feat: 센서 데이터 수신 엔드포인트 추가

POST /sensors/data 엔드포인트를 추가하여
Edge 장치로부터 센서 데이터를 수신할 수 있도록 구현했습니다.
```

## 🚢 배포

Docker를 사용한 배포 방법은 다음 문서를 참고하세요:
- **빠른 시작**: [Docker 빠른 시작 가이드](docs/DOCKER_QUICK_START.md)
- **상세 가이드**: [배포 가이드](docs/DEPLOYMENT_GUIDE.md)

### 빠른 시작 (Docker)

```bash
# 환경 변수 설정
cp env.example .env
# .env 파일 편집 (필수 값 설정)

# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 개발 환경

```bash
# 개발 환경용 Docker Compose 사용 (코드 변경 즉시 반영)
docker-compose -f docker-compose.dev.yml up -d
```

## 📝 문서

### API 문서
- **상세 문서**: [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)
- **Swagger UI**: http://localhost:8001/docs (개발 서버 실행 후)
- **ReDoc**: http://localhost:8001/redoc

### 추가 가이드
- **보고서 생성 가이드**: [docs/REPORT_GENERATION_GUIDE.md](docs/REPORT_GENERATION_GUIDE.md)
- **모니터링 가이드**: [docs/MONITORING_GUIDE.md](docs/MONITORING_GUIDE.md)
- **데이터베이스 마이그레이션**: [docs/DATABASE_MIGRATION.md](docs/DATABASE_MIGRATION.md)

## 🔧 기술 스택

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **Database**: InfluxDB 2.x
- **Message Queue**: MQTT (paho-mqtt)
- **LLM**: OpenAI API
- **Validation**: Pydantic
- **Logging**: Python logging (표준화됨)

### Frontend
- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite
- **Routing**: React Router
- **HTTP Client**: Axios
- **Styling**: Tailwind CSS
- **State Management**: React Context API

### Infrastructure
- **Visualization**: Grafana
- **Message Broker**: Mosquitto (MQTT)
- **Time Series DB**: InfluxDB 2.x

## 📄 라이선스

[라이선스 정보를 추가하세요]

## 👥 팀

[팀원 정보를 추가하세요]

## 📞 문의

[문의 방법을 추가하세요]

