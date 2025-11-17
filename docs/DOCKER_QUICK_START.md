# Docker 빠른 시작 가이드

MOBY Platform을 Docker로 빠르게 시작하는 방법입니다.

## 🚀 빠른 시작

### 1. 환경 변수 설정

```bash
# .env 파일 생성
cp env.example .env

# 필수 환경 변수 편집
nano .env  # 또는 원하는 에디터 사용
```

**최소 필수 설정:**
```env
INFLUX_TOKEN=your-influxdb-token
INFLUX_ORG=WISE
INFLUX_BUCKET=moby-data
SECRET_KEY=your-secret-key-here
```

### 2. 서비스 시작

```bash
# 모든 서비스 시작 (백그라운드)
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 3. 서비스 접속

- **Backend API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **InfluxDB**: http://localhost:8086

### 4. 서비스 중지

```bash
# 서비스 중지 (데이터 유지)
docker-compose stop

# 서비스 중지 및 컨테이너 제거 (데이터 유지)
docker-compose down

# 서비스 중지 및 볼륨까지 제거 (데이터 삭제)
docker-compose down -v
```

## 🔧 개발 환경

개발 환경에서는 코드 변경이 즉시 반영되도록 볼륨 마운트를 사용합니다.

```bash
# 개발 환경용 Docker Compose 사용
docker-compose -f docker-compose.dev.yml up -d
```

## 📊 서비스 관리

### 로그 확인

```bash
# 모든 서비스 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f backend
docker-compose logs -f influxdb
docker-compose logs -f mqtt
```

### 서비스 재시작

```bash
# 특정 서비스 재시작
docker-compose restart backend

# 모든 서비스 재시작
docker-compose restart
```

### 컨테이너 상태 확인

```bash
# 실행 중인 컨테이너 확인
docker-compose ps

# 리소스 사용량 확인
docker stats
```

## 🐛 문제 해결

### 포트 충돌

포트가 이미 사용 중인 경우:

```bash
# 포트 사용 확인 (Windows)
netstat -ano | findstr :8000

# docker-compose.yml에서 포트 변경
ports:
  - "8001:8000"  # 호스트 포트를 8001로 변경
```

### 환경 변수 문제

```bash
# 환경 변수 확인
docker-compose config

# .env 파일 확인
cat .env
```

### 데이터 초기화

```bash
# 모든 데이터 삭제 후 재시작
docker-compose down -v
docker-compose up -d
```

## 📚 추가 정보

- [상세 배포 가이드](./DEPLOYMENT_GUIDE.md)
- [API 문서](./API_DOCUMENTATION.md)

