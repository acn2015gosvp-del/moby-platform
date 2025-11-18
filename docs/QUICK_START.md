# 🚀 MOBY Platform 빠른 시작 가이드

실제로 웹 서버를 실행해서 눈으로 확인하는 방법입니다.

---

## 📋 사전 준비

### 1. 환경 변수 확인

`.env` 파일이 있는지 확인하고, 없으면 생성하세요:

```bash
# .env 파일이 없으면
copy env.example .env
```

**최소 필수 설정 (.env 파일):**
```env
# 인증 (필수)
SECRET_KEY=your-secret-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# MQTT (기본값으로도 동작)
MQTT_HOST=localhost
MQTT_PORT=1883

# InfluxDB (실제 값이 없어도 서버는 실행됨, 일부 기능만 제한)
INFLUX_URL=http://localhost:8086
INFLUX_TOKEN=your-token
INFLUX_ORG=WISE
INFLUX_BUCKET=moby-data

# 환경 설정
ENVIRONMENT=dev
DEBUG=false
LOG_LEVEL=INFO
```

---

## 🎯 실행 순서

### Step 1: Backend 서버 실행

**터미널 1을 열고:**

```bash
# ⚠️ 중요: 프로젝트 루트 디렉토리에서 실행해야 합니다!
# backend 디렉토리가 아닌 moby-platform 디렉토리에서 실행하세요.

# 프로젝트 루트 디렉토리로 이동
cd C:\Users\USER\projects\moby-platform

# Backend 서버 실행 (포트 8001)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
```

**성공 메시지:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**확인 방법:**
브라우저에서 http://localhost:8001 접속 → `{"status":"ok","message":"MOBY backend running"}` 표시되면 성공!

**API 문서 확인:**
http://localhost:8001/docs 접속 → Swagger UI가 표시되면 성공!

---

### Step 2: Frontend 서버 실행

**새 터미널 2를 열고:**

```bash
# Frontend 디렉토리로 이동
cd frontend

# 의존성 설치 (처음 한 번만 실행)
npm install

# 개발 서버 실행
npm run dev
```

**성공 메시지:**
```
  VITE v7.2.2  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**확인 방법:**
브라우저에서 **http://localhost:3000** 접속 → 로그인 페이지가 표시되면 성공!

---

### Step 3: 웹 애플리케이션 사용

**1. 회원가입**
- **http://localhost:3000** 접속
- "회원가입" 클릭
- 이메일, 사용자명, 비밀번호 입력
- "회원가입" 버튼 클릭

**2. 로그인**
- 회원가입 후 자동으로 로그인 페이지로 이동
- 이메일과 비밀번호 입력
- "로그인" 버튼 클릭

**3. 대시보드 확인**
- 로그인 성공 후 대시보드 페이지로 이동
- 센서 상태, 최근 알림, 통계 정보 확인

**4. 센서 페이지 확인**
- 왼쪽 메뉴에서 "센서" 클릭
- 센서 상태 카드 확인
- "새로고침" 버튼으로 데이터 갱신

**5. 알림 페이지 확인**
- 왼쪽 메뉴에서 "알림" 클릭
- 알림 목록 확인
- 레벨 필터링 테스트

---

## 🔍 확인할 수 있는 기능

### Backend API

**브라우저에서 직접 확인:**
- http://localhost:8000 - 루트 엔드포인트
- http://localhost:8000/docs - Swagger API 문서
- http://localhost:8000/redoc - ReDoc API 문서
- http://localhost:8000/health - 헬스체크
- http://localhost:8000/metrics - Prometheus 메트릭

**API 테스트:**
- Swagger UI에서 직접 API 호출 테스트 가능
- 각 엔드포인트의 요청/응답 예제 확인 가능

### Frontend

**페이지:**
- http://localhost:3000/login - 로그인 페이지
- http://localhost:3000/register - 회원가입 페이지
- http://localhost:3000/ - 대시보드 (센서 상태, 최근 알림, 통계)
- http://localhost:3000/sensors - 센서 관리 (실시간 상태)
- http://localhost:3000/alerts - 알림 관리 (최신 알림 목록)

**기능:**
- 실시간 데이터 갱신 (30초마다 자동)
- 필터링 및 검색
- 반응형 디자인 (모바일/태블릿/데스크톱)

---

## ⚠️ 주의사항

### Backend 서버 실행 시

**MQTT 연결 오류가 나도 괜찮습니다:**
- MQTT Broker가 실행 중이 아니어도 서버는 정상 작동합니다
- 일부 기능만 제한됩니다 (센서 데이터 수신)

**InfluxDB 연결 오류가 나도 괜찮습니다:**
- InfluxDB가 실행 중이 아니어도 서버는 정상 작동합니다
- 센서 상태 조회 기능만 제한됩니다

**중요:** 인증 기능은 SQLite 데이터베이스를 사용하므로 별도 설정 없이 동작합니다!

### Frontend 서버 실행 시

**포트 충돌:**
- 3000 포트가 사용 중이면 자동으로 다른 포트 사용
- 터미널에 표시된 포트 번호 확인

**API 연결 오류:**
- Backend 서버가 실행 중인지 확인
- http://localhost:8000 접속 가능한지 확인

---

## 🛑 서버 중지

**Backend 서버 중지:**
- 터미널 1에서 `Ctrl + C` 누르기

**Frontend 서버 중지:**
- 터미널 2에서 `Ctrl + C` 누르기

---

## 🐛 문제 해결

### Backend 서버가 시작되지 않을 때

```bash
# 의존성 재설치
pip install -r requirements.txt

# 포트 확인
netstat -ano | findstr :8000
```

### Frontend 서버가 시작되지 않을 때

```bash
# node_modules 삭제 후 재설치
cd frontend
rm -rf node_modules  # Windows: rmdir /s node_modules
npm install
npm run dev
```

### API 연결 오류

1. Backend 서버가 실행 중인지 확인
2. http://localhost:8000 접속 가능한지 확인
3. 브라우저 개발자 도구 (F12) → Network 탭에서 오류 확인

---

## 📝 접속 주소 요약

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API 문서 (Swagger)**: http://localhost:8000/docs
- **API 문서 (ReDoc)**: http://localhost:8000/redoc
- **헬스체크**: http://localhost:8000/health
- **메트릭**: http://localhost:8000/metrics

---

## 📝 다음 단계

서버가 정상적으로 실행되면:

1. **회원가입 및 로그인 테스트**
2. **대시보드에서 데이터 확인**
3. **센서 페이지에서 상태 확인**
4. **알림 페이지에서 알림 목록 확인**
5. **API 문서에서 엔드포인트 테스트**

---

**문제가 발생하면 터미널의 오류 메시지를 확인하세요!**

