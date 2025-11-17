# MOBY Platform

Industrial IoT & Predictive Maintenance Platform

## 📦 프로젝트 개요

MOBY는 산업용 IoT 예측 정비 플랫폼입니다. 다양한 센서 데이터를 수집하고 분석하여 이상 징후를 감지하고 알림을 제공합니다.

### 주요 기능

- **다중 센서 데이터 수집**: 진동, 소리, 온도/습도, 가속도계/자이로스코프, 사이클 카운트
- **실시간 데이터 파이프라인**: MQTT → FastAPI → InfluxDB
- **Grafana 대시보드**: 시계열 데이터 시각화
- **알림 엔진**: 규칙 기반 + ML/LLM 기반 이상 탐지
- **LLM 기반 보고서**: 일일/주간 자동 보고서 생성
- **웹 프론트엔드**: React/Vite 기반 알림 및 대시보드 UI

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
│   │   └── services/    # 비즈니스 로직
│   │       ├── alert_engine.py
│   │       ├── influx_client.py
│   │       ├── mqtt_client.py
│   │       └── llm_client.py
│   ├── main.py          # FastAPI 앱 진입점
│   └── tests/           # 테스트 코드
├── frontend/            # React/Vite 프론트엔드 (예정)
├── docs/                # 프로젝트 문서
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
`.env` 파일을 생성하고 다음 내용을 설정하세요:
```env
MQTT_HOST=localhost
MQTT_PORT=1883
INFLUX_URL=http://localhost:8086
INFLUX_TOKEN=your-token
INFLUX_ORG=your-org
OPENAI_API_KEY=your-api-key
```

5. 서버 실행
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면 다음 주소에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 테스트

```bash
pytest
```

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

**예시:**
```
feat: 센서 데이터 수신 엔드포인트 추가

POST /sensors/data 엔드포인트를 추가하여
Edge 장치로부터 센서 데이터를 수신할 수 있도록 구현했습니다.
```

## 📝 API 문서

API 문서는 Swagger UI를 통해 확인할 수 있습니다:
- 개발 서버 실행 후: http://localhost:8000/docs

## 🔧 기술 스택

- **Backend**: FastAPI, Python
- **Database**: InfluxDB 2.x
- **Message Queue**: MQTT (paho-mqtt)
- **LLM**: OpenAI API
- **Frontend**: React, Vite (예정)
- **Visualization**: Grafana

## 📄 라이선스

[라이선스 정보를 추가하세요]

## 👥 팀

[팀원 정보를 추가하세요]

## 📞 문의

[문의 방법을 추가하세요]

