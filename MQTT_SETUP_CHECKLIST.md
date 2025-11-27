# MQTT 실시간 수신 설정 체크리스트

## ✅ 필수 설정 확인

### 1. Mosquitto 브로커 실행 확인

**Windows 서비스로 실행 중인 경우:**
```powershell
# 서비스 상태 확인
Get-Service mosquitto

# 서비스가 실행 중이 아니면 시작
Start-Service mosquitto

# 또는 재시작
Restart-Service mosquitto
```

**수동으로 실행 중인 경우:**
```powershell
# Mosquitto 프로세스 확인
Get-Process mosquitto -ErrorAction SilentlyContinue

# 실행 중이 아니면 시작
cd "C:\Program Files\mosquitto"
.\mosquitto.exe -c mosquitto.conf
```

**포트 1883 리스닝 확인:**
```powershell
netstat -an | findstr 1883
# LISTENING 상태여야 함
```

### 2. Mosquitto 설정 파일 확인

**파일 위치:** `C:\Program Files\mosquitto\mosquitto.conf`

**필수 설정:**
```
listener 1883
allow_anonymous true
```

**설정 확인:**
```powershell
Get-Content "C:\Program Files\mosquitto\mosquitto.conf" | Select-String -Pattern "listener|allow_anonymous"
```

### 3. 백엔드 MQTT 설정 확인

**`.env` 파일 또는 환경 변수:**
```
MQTT_HOST=localhost
MQTT_PORT=1883
```

**설정 확인:**
```powershell
# .env 파일 확인
Get-Content backend\.env | Select-String -Pattern "MQTT"
```

**기본값:**
- `MQTT_HOST`: `localhost` (자동으로 `127.0.0.1`로 변환)
- `MQTT_PORT`: `1883`

### 4. 백엔드 서버 실행 확인

**서버 실행:**
```powershell
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**서버 로그에서 MQTT 연결 확인:**
```
✅ MQTT connected successfully. Host: 127.0.0.1:1883
✅ Subscribed to sensor data topics: sensors/+/data
✅ Subscribed to Edge AI alert topic: factory/inference/results/#
```

### 5. 구독 중인 토픽 확인

현재 구독 중인 토픽:
- `sensors/+/data` - 센서 데이터 (QoS 1)
- `factory/inference/results/#` - Edge AI 알림 (QoS 1)

## 🔍 연결 상태 확인 방법

### 1. 백엔드 Health Check API

```powershell
# Health Check 엔드포인트 호출
curl http://localhost:8000/api/health

# 또는 브라우저에서
http://localhost:8000/api/health
```

**응답 예시:**
```json
{
  "status": "healthy",
  "mqtt": {
    "connected": true,
    "host": "127.0.0.1",
    "port": 1883
  }
}
```

### 2. 백엔드 로그 확인

**로그 파일 위치:**
- 개발 환경: `backend/logs/moby-debug.log`
- 프로덕션 환경: `backend/logs/moby.log`

**실시간 로그 확인:**
```powershell
# PowerShell에서 실시간 로그 확인
Get-Content backend\logs\moby-debug.log -Wait -Tail 50
```

**MQTT 관련 로그 키워드:**
- `✅ MQTT connected` - 연결 성공
- `❌ MQTT connection failed` - 연결 실패
- `📨 Edge AI 알림 수신` - AI 알림 수신
- `📥 MQTT message received` - 메시지 수신

### 3. MQTT 클라이언트로 테스트

**Mosquitto 클라이언트 설치 확인:**
```powershell
# Mosquitto 클라이언트가 설치되어 있는지 확인
mosquitto_pub --help
mosquitto_sub --help
```

**테스트 메시지 발행:**
```powershell
# AI 알림 테스트 메시지 발행
mosquitto_pub -h localhost -p 1883 -t "factory/inference/results/test-device" -m '{"model_name":"mlp_classifier","sensor_type":"accel_gyro","context_payload":{"fields":{"mlp_s1_prob_normal":0.05,"mlp_s1_prob_yellow":0.10,"mlp_s1_prob_red":0.85,"mlp_s2_prob_normal":0.98,"mlp_s2_prob_yellow":0.02,"mlp_s2_prob_red":0.00}}}'
```

**메시지 구독 테스트:**
```powershell
# 모든 메시지 구독
mosquitto_sub -h localhost -p 1883 -t "#" -v
```

## 🚨 문제 해결

### 문제 1: MQTT 연결 실패

**증상:**
```
❌ MQTT connection failed. Result code: 3 (server unavailable)
```

**해결 방법:**
1. Mosquitto 브로커가 실행 중인지 확인
2. 포트 1883이 열려있는지 확인
3. 방화벽 설정 확인

### 문제 2: 메시지 수신 안 됨

**확인 사항:**
1. 토픽 이름이 정확한지 확인 (`factory/inference/results/#`)
2. 메시지 형식이 올바른지 확인 (JSON 형식)
3. 백엔드 로그에서 에러 메시지 확인

### 문제 3: 구독 실패

**증상:**
```
❌ Failed to subscribe to Edge AI alert topic
```

**해결 방법:**
1. Mosquitto 설정에서 `allow_anonymous true` 확인
2. 백엔드 서버 재시작
3. MQTT 클라이언트 재연결

## 📝 빠른 확인 스크립트

**PowerShell 스크립트로 한 번에 확인:**
```powershell
Write-Host "=== MQTT 설정 확인 ===" -ForegroundColor Cyan

# 1. Mosquitto 서비스 확인
Write-Host "`n1. Mosquitto 서비스 상태:" -ForegroundColor Yellow
$service = Get-Service mosquitto -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "   상태: $($service.Status)" -ForegroundColor $(if ($service.Status -eq 'Running') { 'Green' } else { 'Red' })
} else {
    Write-Host "   Mosquitto 서비스를 찾을 수 없습니다." -ForegroundColor Red
}

# 2. 포트 1883 확인
Write-Host "`n2. 포트 1883 리스닝 상태:" -ForegroundColor Yellow
$port = netstat -an | findstr "1883.*LISTENING"
if ($port) {
    Write-Host "   ✅ 포트 1883이 리스닝 중입니다." -ForegroundColor Green
} else {
    Write-Host "   ❌ 포트 1883이 리스닝 중이 아닙니다." -ForegroundColor Red
}

# 3. Mosquitto 설정 확인
Write-Host "`n3. Mosquitto 설정:" -ForegroundColor Yellow
$configPath = "C:\Program Files\mosquitto\mosquitto.conf"
if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw
    if ($config -match "listener 1883") {
        Write-Host "   ✅ listener 1883 설정됨" -ForegroundColor Green
    } else {
        Write-Host "   ❌ listener 1883 설정 안 됨" -ForegroundColor Red
    }
    if ($config -match "allow_anonymous true") {
        Write-Host "   ✅ allow_anonymous true 설정됨" -ForegroundColor Green
    } else {
        Write-Host "   ❌ allow_anonymous true 설정 안 됨" -ForegroundColor Red
    }
} else {
    Write-Host "   설정 파일을 찾을 수 없습니다: $configPath" -ForegroundColor Red
}

# 4. 백엔드 설정 확인
Write-Host "`n4. 백엔드 MQTT 설정:" -ForegroundColor Yellow
if (Test-Path "backend\.env") {
    $envContent = Get-Content "backend\.env" | Select-String -Pattern "MQTT"
    if ($envContent) {
        Write-Host "   $envContent" -ForegroundColor Green
    } else {
        Write-Host "   기본값 사용 (localhost:1883)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   .env 파일 없음 - 기본값 사용" -ForegroundColor Yellow
}

Write-Host "`n=== 확인 완료 ===" -ForegroundColor Cyan
```

## ✅ 체크리스트

- [ ] Mosquitto 브로커 실행 중
- [ ] 포트 1883 리스닝 중
- [ ] `listener 1883` 설정됨
- [ ] `allow_anonymous true` 설정됨
- [ ] 백엔드 서버 실행 중
- [ ] MQTT 연결 성공 로그 확인
- [ ] 토픽 구독 성공 로그 확인
- [ ] 테스트 메시지 발행/수신 확인

