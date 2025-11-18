# 🔧 문제 해결 가이드

MOBY Platform 실행 중 발생할 수 있는 문제와 해결 방법을 안내합니다.

---

## 📋 목차

1. [인코딩 오류 (UnicodeDecodeError)](#인코딩-오류-unicodedecodeerror)
2. [포트 충돌](#포트-충돌)
3. [환경 변수 오류](#환경-변수-오류)
4. [MQTT 연결 실패](#mqtt-연결-실패)
5. [InfluxDB 연결 실패](#influxdb-연결-실패)
6. [데이터베이스 오류](#데이터베이스-오류)
7. [의존성 설치 오류](#의존성-설치-오류)

---

## 인코딩 오류 (UnicodeDecodeError)

### 증상

```
UnicodeDecodeError: 'cp949' codec can't decode byte 0x8f in position 12: illegal multibyte sequence
decoding with 'cp949' codec failed
```

### 원인

Windows에서 UTF-8로 인코딩된 파일을 읽을 때 기본 인코딩(cp949)으로 읽으려고 해서 발생합니다.

### 해결 방법

#### 방법 1: 환경 변수 설정 (권장)

**PowerShell에서:**
```powershell
$env:PYTHONIOENCODING="utf-8"
```

**영구적으로 설정하려면:**
```powershell
[System.Environment]::SetEnvironmentVariable("PYTHONIOENCODING", "utf-8", "User")
```

**CMD에서:**
```cmd
set PYTHONIOENCODING=utf-8
```

#### 방법 2: Python 스크립트 실행 시 인코딩 지정

```bash
python -X utf8 your_script.py
```

#### 방법 3: 파일 읽기 시 명시적 인코딩 지정

Python 코드에서 파일을 읽을 때:
```python
# ❌ 잘못된 방법
with open("file.txt") as f:
    content = f.read()

# ✅ 올바른 방법
with open("file.txt", encoding="utf-8") as f:
    content = f.read()
```

#### 방법 4: requirements.txt 파일 인코딩 확인

파일이 UTF-8로 저장되어 있는지 확인:
```powershell
# 파일 인코딩 확인 (PowerShell)
Get-Content requirements.txt -Encoding UTF8 | Out-File -Encoding UTF8 requirements_utf8.txt
```

---

## 포트 충돌

### 증상

```
ERROR:    [Errno 48] Address already in use
또는
포트 8000이 이미 사용 중입니다
```

### 해결 방법

#### 1. 사용 중인 포트 확인

**Windows:**
```powershell
netstat -ano | findstr ":8000"
```

**Linux/Mac:**
```bash
lsof -i :8000
```

#### 2. 프로세스 종료

**Windows:**
```powershell
# PID 확인 후
taskkill /PID <PID번호> /F
```

**Linux/Mac:**
```bash
kill -9 <PID번호>
```

#### 3. 다른 포트 사용

```bash
# 백엔드
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload

# 프론트엔드 (vite.config.ts 수정)
# server: { port: 5174 }
```

---

## 환경 변수 오류

### 증상

```
ValueError: Invalid configuration
또는
환경 변수가 설정되지 않았습니다
```

### 해결 방법

#### 1. .env 파일 확인

```bash
# .env 파일이 프로젝트 루트에 있는지 확인
ls .env  # Linux/Mac
dir .env  # Windows
```

#### 2. 필수 환경 변수 확인

```python
# Python에서 확인
python -c "from backend.api.services.schemas.models.core.config import settings; print(settings.validate_settings())"
```

#### 3. .env 파일 재생성

```bash
# env.example 복사
copy env.example .env  # Windows
cp env.example .env    # Linux/Mac

# .env 파일 편집하여 실제 값 입력
```

---

## MQTT 연결 실패

### 증상

```
❌ MQTT connection failed
⚠️ MQTT disconnected unexpectedly
```

### 해결 방법

**중요**: MQTT 연결 실패는 **정상**입니다! MQTT Broker가 없어도 웹 서버는 정상 실행됩니다.

#### MQTT Broker 실행 (선택사항)

**Mosquitto 설치 및 실행:**

```bash
# Windows (Chocolatey)
choco install mosquitto

# Linux
sudo apt-get install mosquitto mosquitto-clients

# 실행
mosquitto -c mosquitto.conf
```

**테스트:**
```bash
# 발행
mosquitto_pub -h localhost -t test/topic -m "Hello"

# 구독
mosquitto_sub -h localhost -t test/topic
```

---

## InfluxDB 연결 실패

### 증상

```
Failed to connect to InfluxDB
InfluxDB connection error
```

### 해결 방법

**중요**: InfluxDB 연결 실패도 **정상**입니다! InfluxDB가 없어도 웹 서버는 정상 실행됩니다.

#### InfluxDB 설치 및 실행 (선택사항)

**Docker로 실행:**
```bash
docker run -d -p 8086:8086 \
  -e INFLUXDB_DB=moby-data \
  -e INFLUXDB_ADMIN_USER=admin \
  -e INFLUXDB_ADMIN_PASSWORD=admin123 \
  influxdb:2.7
```

**토큰 생성:**
1. http://localhost:8086 접속
2. 초기 설정 완료
3. API Token 생성
4. `.env` 파일에 토큰 추가

---

## 데이터베이스 오류

### 증상

```
sqlalchemy.exc.OperationalError
Table does not exist
```

### 해결 방법

#### 1. 데이터베이스 초기화

```bash
python scripts/migrate_db.py
```

#### 2. 데이터베이스 파일 확인

```bash
# SQLite 파일 위치 확인
ls moby.db  # Linux/Mac
dir moby.db  # Windows
```

#### 3. 데이터베이스 재생성

```bash
# 백업 후 재생성
python scripts/migrate_db.py --backup
rm moby.db  # Linux/Mac
del moby.db  # Windows
python scripts/migrate_db.py
```

---

## 의존성 설치 오류

### 증상

```
ERROR: Could not find a version that satisfies the requirement
또는
pip install 실패
```

### 해결 방법

#### 1. Python 버전 확인

```bash
python --version  # Python 3.9 이상 필요
```

#### 2. pip 업그레이드

```bash
python -m pip install --upgrade pip
```

#### 3. 가상 환경 재생성

```bash
# 기존 가상 환경 삭제
rm -rf venv  # Linux/Mac
rmdir /s venv  # Windows

# 새로 생성
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 의존성 재설치
pip install -r requirements.txt
```

#### 4. 개별 패키지 설치

```bash
# 문제가 있는 패키지만 개별 설치
pip install fastapi uvicorn
pip install pydantic pydantic-settings
# ...
```

---

## 추가 도움말

### 로그 확인

**백엔드 로그:**
```bash
# 로그 파일 위치
logs/moby.log          # 프로덕션
logs/moby-debug.log    # 디버그 모드
```

**프론트엔드 로그:**
- 브라우저 개발자 도구 콘솔 확인
- 터미널 출력 확인

### 디버그 모드 활성화

**.env 파일에 추가:**
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### 헬스 체크

```bash
# 백엔드 상태 확인
curl http://localhost:8000/health

# 프론트엔드 확인
curl http://localhost:5173
```

---

## 문제가 해결되지 않을 때

1. **로그 확인**: 상세한 오류 메시지 확인
2. **문서 확인**: [README.md](../README.md), [EXECUTION_ORDER.md](EXECUTION_ORDER.md) 참고
3. **환경 확인**: Python 버전, Node.js 버전 확인
4. **의존성 확인**: 모든 패키지가 최신 버전인지 확인

---

## 빠른 체크리스트

문제 발생 시 다음을 확인하세요:

- [ ] Python 버전이 3.9 이상인가?
- [ ] Node.js 버전이 18 이상인가?
- [ ] `.env` 파일이 프로젝트 루트에 있는가?
- [ ] 필수 환경 변수가 설정되어 있는가?
- [ ] 가상 환경이 활성화되어 있는가?
- [ ] 모든 의존성이 설치되어 있는가?
- [ ] 포트가 사용 중이 아닌가?
- [ ] 프로젝트 루트에서 명령어를 실행하고 있는가?

