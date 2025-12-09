# MOBY Platform 배포 가이드

이 문서는 MOBY Platform을 프로덕션 환경에 배포하는 방법을 설명합니다.

## 📋 목차

1. [사전 요구사항](#사전-요구사항)
2. [Docker를 사용한 배포](#docker를-사용한-배포)
3. [수동 배포](#수동-배포)
4. [환경 설정](#환경-설정)
5. [모니터링 및 로깅](#모니터링-및-로깅)
6. [트러블슈팅](#트러블슈팅)

---

## 사전 요구사항

### 필수 소프트웨어

- **Docker** 20.10 이상
- **Docker Compose** 2.0 이상
- **Git** (소스 코드 클론용)

### 시스템 요구사항

- **CPU**: 최소 2 코어 (권장: 4 코어)
- **메모리**: 최소 4GB RAM (권장: 8GB)
- **디스크**: 최소 20GB 여유 공간
- **네트워크**: 인터넷 연결 (의존성 다운로드용)

---

## Docker를 사용한 배포

### 1. 저장소 클론

```bash
git clone <repository-url>
cd moby-platform
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cp env.example .env

# .env 파일 편집 (필수 값 설정)
nano .env
```

**필수 환경 변수:**
- `INFLUX_TOKEN`: InfluxDB 관리자 토큰
- `INFLUX_ORG`: InfluxDB 조직 이름
- `INFLUX_BUCKET`: InfluxDB 버킷 이름
- `OPENAI_API_KEY`: OpenAI API 키 (LLM 기능 사용 시)
- `SECRET_KEY`: JWT 토큰 서명용 시크릿 키
- `GRAFANA_API_KEY`: Grafana API 키 (Grafana 연동 사용 시)

### 3. Docker Compose로 서비스 시작

```bash
# 모든 서비스 빌드 및 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 특정 서비스만 시작
docker-compose up -d backend influxdb mqtt
```

### 4. 서비스 상태 확인

```bash
# 모든 컨테이너 상태 확인
docker-compose ps

# 특정 서비스 로그 확인
docker-compose logs backend
docker-compose logs influxdb
docker-compose logs mqtt
```

### 5. 서비스 접속 확인

- **Backend API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **InfluxDB UI**: http://localhost:8086
- **MQTT Broker**: localhost:1883

---

## 수동 배포

Docker를 사용하지 않는 경우 수동으로 배포할 수 있습니다.

### Backend 배포

#### 1. Python 환경 설정

```bash
# Python 3.12 설치 확인
python3.12 --version

# 가상 환경 생성
python3.12 -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

#### 2. 환경 변수 설정

```bash
# .env 파일 생성 및 편집
cp env.example .env
nano .env
```

#### 3. 데이터베이스 초기화

```bash
# SQLite 데이터베이스는 자동으로 생성됩니다
# InfluxDB는 별도로 설치 및 설정 필요
```

#### 4. 애플리케이션 실행

```bash
# 개발 모드
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드 (Gunicorn 사용 권장)
pip install gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend 배포

#### 1. Node.js 환경 설정

```bash
# Node.js 20 이상 설치 확인
node --version

# 의존성 설치
cd frontend
npm install
```

#### 2. 환경 변수 설정

```bash
# frontend/.env 파일 생성
VITE_API_URL=http://localhost:8000
```

#### 3. 빌드 및 실행

```bash
# 개발 모드
npm run dev

# 프로덕션 빌드
npm run build

# 프로덕션 서버 실행 (예: serve)
npm install -g serve
serve -s dist -l 5173
```

---

## 환경 설정

### 개발 환경

```bash
# .env 파일
ENVIRONMENT=dev
DEBUG=true
LOG_LEVEL=DEBUG
```

### 프로덕션 환경

```bash
# .env 파일
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### 환경별 설정 파일

프로젝트는 환경별 `.env.{environment}` 파일을 지원합니다:

- `.env.dev`: 개발 환경
- `.env.prod`: 프로덕션 환경
- `.env.test`: 테스트 환경

---

## 모니터링 및 로깅

### 로그 위치

- **Backend 로그**: `logs/moby.log` (프로덕션), `logs/moby-debug.log` (개발)
- **Docker 로그**: `docker-compose logs`

### 헬스체크

```bash
# Backend 헬스체크
curl http://localhost:8000/

# Docker 컨테이너 헬스체크
docker-compose ps
```

### 모니터링

- **Grafana**: http://localhost:3000
- **InfluxDB**: http://localhost:8086
- **API 문서**: http://localhost:8000/docs

---

## 트러블슈팅

### 일반적인 문제

#### 1. 포트 충돌

```bash
# 포트 사용 확인
netstat -tulpn | grep :8000  # Linux
lsof -i :8000  # Mac
netstat -ano | findstr :8000  # Windows

# docker-compose.yml에서 포트 변경
ports:
  - "8001:8000"  # 호스트 포트 변경
```

#### 2. 환경 변수 로드 실패

```bash
# .env 파일 위치 확인
# 프로젝트 루트에 있어야 함

# 환경 변수 확인
docker-compose config
```

#### 3. 데이터베이스 연결 실패

```bash
# InfluxDB 상태 확인
docker-compose logs influxdb

# InfluxDB 토큰 확인
# .env 파일의 INFLUX_TOKEN이 올바른지 확인
```

#### 4. MQTT 연결 실패

```bash
# MQTT Broker 상태 확인
docker-compose logs mqtt

# MQTT 포트 확인
# .env 파일의 MQTT_HOST와 MQTT_PORT 확인
```

### 로그 확인

```bash
# 모든 서비스 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f backend
docker-compose logs -f influxdb
docker-compose logs -f mqtt

# 최근 100줄만 확인
docker-compose logs --tail=100 backend
```

### 컨테이너 재시작

```bash
# 특정 서비스 재시작
docker-compose restart backend

# 모든 서비스 재시작
docker-compose restart

# 서비스 중지 및 시작
docker-compose down
docker-compose up -d
```

---

## 프로덕션 배포 체크리스트

- [ ] 환경 변수 설정 완료 (`.env` 파일)
- [ ] Docker 및 Docker Compose 설치 확인
- [ ] 포트 충돌 확인 (8000, 1883, 8086, 3000)
- [ ] 방화벽 설정 확인
- [ ] SSL/TLS 인증서 설정 (HTTPS 사용 시)
- [ ] 데이터베이스 백업 설정
- [ ] 로그 로테이션 설정
- [ ] 모니터링 도구 설정
- [ ] 헬스체크 엔드포인트 확인
- [ ] API 문서 접근 제한 (프로덕션)

---

## 추가 리소스

- [API 문서](./API_DOCUMENTATION.md)
- [README](../README.md)
- [기여 가이드](../CONTRIBUTING.md)

---

**문의사항이나 문제가 있으면 이슈를 생성해주세요.**

