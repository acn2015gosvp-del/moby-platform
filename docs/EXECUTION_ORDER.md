# 🚀 MOBY Platform 실행 순서 가이드

이 문서는 MOBY Platform을 처음부터 실행하는 전체 순서를 안내합니다.

## 📋 사전 준비사항

### 필수 설치 항목
- Python 3.9 이상
- Node.js 18 이상 및 npm
- (선택) MQTT Broker (Mosquitto) - 센서 데이터 수신 시 필요
- (선택) InfluxDB 2.x - 시계열 데이터 저장 시 필요

---

## 🔧 1단계: 환경 변수 설정

### 1-1. `.env` 파일 생성

프로젝트 루트 디렉토리에서:

```bash
# Windows
copy env.example .env

# Linux/Mac
cp env.example .env
```

### 1-2. `.env` 파일 편집

필수 설정 항목:
- `GEMINI_API_KEY`: 보고서 생성 기능 사용 시 필수
- `SECRET_KEY`: 프로덕션 환경에서 반드시 변경 (최소 32자 이상)
- `INFLUX_TOKEN`, `INFLUX_ORG`: InfluxDB 사용 시 필요

선택 설정 항목:
- `MQTT_HOST`, `MQTT_PORT`: MQTT Broker 주소 (기본값: localhost:1883)
- `INFLUX_URL`: InfluxDB 주소 (기본값: http://localhost:8086)
- `ENVIRONMENT`: 환경 설정 (dev/debug/production)

**참고**: MQTT나 InfluxDB가 없어도 웹 서버는 정상 실행됩니다. 단, 해당 기능은 사용할 수 없습니다.

---

## 📦 2단계: 백엔드 의존성 설치

### 2-1. 가상 환경 생성 및 활성화

```bash
# 프로젝트 루트 디렉토리에서
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2-2. Python 패키지 설치

```bash
# 프로젝트 루트 디렉토리에서
pip install -r requirements.txt
```

---

## 📦 3단계: 프론트엔드 의존성 설치

### 3-1. 프론트엔드 디렉토리로 이동

```bash
cd frontend
```

### 3-2. npm 패키지 설치

```bash
npm install
```

### 3-3. 프로젝트 루트로 복귀

```bash
cd ..
```

---

## 🗄️ 4단계: 데이터베이스 초기화 (선택사항)

### 4-1. 데이터베이스 테이블 생성

```bash
# 프로젝트 루트 디렉토리에서
python scripts/migrate_db.py
```

**참고**: 백엔드 서버 시작 시 자동으로 테이블이 생성되므로 이 단계는 선택사항입니다.

---

## 🖥️ 5단계: 백엔드 서버 실행

### 5-1. 프로젝트 루트 디렉토리 확인

**⚠️ 중요**: 반드시 프로젝트 루트 디렉토리(`moby-platform/`)에서 실행해야 합니다!

```bash
# 현재 위치 확인
pwd  # Linux/Mac
cd   # Windows (현재 경로 표시)
```

### 5-2. 백엔드 서버 시작

```bash
# 개발 모드 (코드 변경 시 자동 재시작)
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 또는 프로덕션 모드
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 5-3. 백엔드 서버 확인

브라우저에서 다음 URL을 확인:
- **API 문서**: http://localhost:8000/docs
- **헬스 체크**: http://localhost:8000/health
- **루트 엔드포인트**: http://localhost:8000/

**정상 실행 시 예상 로그:**
```
INFO:     Application starting up: Validating configuration...
INFO:     ✅ Configuration validation passed.
INFO:     Initializing database and MQTT client...
INFO:     🔄 MQTT connection attempt 1/3. Host: localhost:1883
⚠️  MQTT 연결 실패 시에도 웹 서버는 정상 실행됩니다.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 🎨 6단계: 프론트엔드 서버 실행

### 6-1. 새 터미널 창 열기

백엔드 서버가 실행 중인 터미널과 **별도로** 새 터미널을 엽니다.

### 6-2. 프론트엔드 디렉토리로 이동

```bash
cd frontend
```

### 6-3. 개발 서버 시작

```bash
npm run dev
```

### 6-4. 프론트엔드 서버 확인

브라우저에서 다음 URL을 확인:
- **프론트엔드**: http://localhost:5173

**정상 실행 시 예상 로그:**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

---

## ✅ 실행 확인 체크리스트

### 백엔드 확인
- [ ] http://localhost:8000/health 접속 시 JSON 응답 확인
- [ ] http://localhost:8000/docs 접속 시 Swagger UI 표시 확인
- [ ] 터미널에 에러 메시지 없음 확인

### 프론트엔드 확인
- [ ] http://localhost:5173 접속 시 웹 페이지 표시 확인
- [ ] 브라우저 콘솔에 에러 없음 확인
- [ ] 로그인 페이지 또는 메인 페이지 정상 표시 확인

### 통합 확인
- [ ] 프론트엔드에서 백엔드 API 호출 정상 작동
- [ ] 인증 기능 정상 작동 (로그인/회원가입)
- [ ] 센서 데이터 조회 기능 정상 작동

---

## 🔍 문제 해결

### 백엔드 서버가 시작되지 않는 경우

1. **포트 충돌 확인**
   ```bash
   # Windows
   netstat -ano | findstr ":8000"
   
   # Linux/Mac
   lsof -i :8000
   ```

2. **환경 변수 확인**
   - `.env` 파일이 프로젝트 루트에 있는지 확인
   - 필수 환경 변수가 설정되어 있는지 확인

3. **가상 환경 활성화 확인**
   ```bash
   # 가상 환경이 활성화되어 있는지 확인
   which python  # Linux/Mac
   where python  # Windows
   ```

### 프론트엔드 서버가 시작되지 않는 경우

1. **포트 충돌 확인**
   ```bash
   # Windows
   netstat -ano | findstr ":5173"
   
   # Linux/Mac
   lsof -i :5173
   ```

2. **의존성 재설치**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

### MQTT 연결 실패

**MQTT 연결 실패는 정상입니다!** MQTT Broker가 실행되지 않아도 웹 서버는 정상 작동합니다.

- MQTT Broker가 없어도 웹 서버는 정상 실행됩니다
- 센서 데이터 수신 기능만 사용할 수 없습니다
- 다른 기능(인증, 보고서 생성 등)은 정상 작동합니다

MQTT Broker를 실행하려면:
```bash
# Mosquitto 설치 후
mosquitto -c mosquitto.conf
```

### InfluxDB 연결 실패

**InfluxDB 연결 실패도 정상입니다!** InfluxDB가 없어도 웹 서버는 정상 작동합니다.

- InfluxDB가 없어도 웹 서버는 정상 실행됩니다
- 시계열 데이터 저장/조회 기능만 사용할 수 없습니다
- 다른 기능은 정상 작동합니다

---

## 📝 실행 순서 요약

```bash
# 1. 환경 변수 설정
copy env.example .env  # Windows
# .env 파일 편집

# 2. 백엔드 의존성 설치
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 3. 프론트엔드 의존성 설치
cd frontend
npm install
cd ..

# 4. 백엔드 서버 실행 (터미널 1)
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 5. 프론트엔드 서버 실행 (터미널 2)
cd frontend
npm run dev
```

---

## 🎯 빠른 시작 (이미 설치된 경우)

의존성이 이미 설치되어 있다면:

```bash
# 터미널 1: 백엔드
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 터미널 2: 프론트엔드
cd frontend && npm run dev
```

---

## 📚 추가 참고 자료

- [빠른 시작 가이드](QUICK_START.md)
- [API 문서](API_DOCUMENTATION.md)
- [배포 가이드](DEPLOYMENT_GUIDE.md)
- [문제 해결 가이드](TROUBLESHOOTING.md)

