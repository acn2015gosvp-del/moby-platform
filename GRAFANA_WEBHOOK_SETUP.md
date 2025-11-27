# Grafana Webhook 설정 가이드

## 📋 Grafana 관리자(Stark)에게 전달할 정보

### Webhook URL
백엔드 서버를 시작하면 콘솔에 다음 형식으로 출력됩니다:
```
✅ Grafana Webhook URL:
   http://192.168.x.x:8000/api/webhook/grafana
```

이 URL을 복사하여 Grafana에 등록하세요.

### Webhook 설정
- **Method**: `POST`
- **Content-Type**: `application/json`
- **URL**: 백엔드 서버 시작 시 콘솔에 출력된 URL 사용

### 예상 Webhook 페이로드 형식
Grafana는 다음과 같은 형식으로 알림을 전송합니다:
```json
{
  "alerts": [
    {
      "state": "alerting",
      "status": "firing",
      "labels": {
        "device_id": "motor_01",
        "alertname": "Temperature Threshold"
      },
      "annotations": {
        "summary": "온도 임계치 초과",
        "description": "온도가 80도를 초과했습니다."
      }
    }
  ]
}
```

## 🔧 프론트엔드 WebSocket 주소 설정

### 자동 감지 (기본값)
프론트엔드가 백엔드와 같은 서버에서 실행되는 경우, `window.location.hostname`을 자동으로 사용합니다.

### 수동 설정 방법

#### 방법 1: 환경 변수 사용 (권장)
프로젝트 루트에 `.env` 파일 생성:
```env
VITE_WS_BASE_URL=ws://192.168.x.x:8000/ws
VITE_API_BASE_URL=http://192.168.x.x:8000
```

#### 방법 2: 코드에서 직접 수정
`frontend/src/utils/constants.ts` 파일에서 `BACKEND_HOST` 상수 수정:
```typescript
const BACKEND_HOST = '192.168.x.x'  // 여기에 IP 주소 입력
```

## 🚀 서버 시작 및 확인

### 백엔드 서버 시작
```bash
# Windows PowerShell
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 또는 스크립트 사용
.\scripts\start_backend.ps1
```

**⚠️ 중요**: `--host 0.0.0.0` 옵션을 반드시 포함해야 외부에서 접속할 수 있습니다!

서버 시작 시 콘솔에 Grafana Webhook URL이 출력됩니다:
```
======================================================================
✅ Grafana Webhook URL:
   http://192.168.x.x:8000/api/webhook/grafana
======================================================================
```

### 프론트엔드 서버 시작
```bash
cd frontend
npm run dev
```

## ✅ 구현 완료 사항

### Backend (FastAPI)
- ✅ CORS 설정: `allow_origins=["*"]` (Grafana 서버 포함)
- ✅ IP 주소 자동 감지 및 Webhook URL 출력
- ✅ `POST /api/webhook/grafana` 엔드포인트
- ✅ `WS /ws` 엔드포인트
- ✅ MQTT 구독: `moby/ai/alert` 토픽
- ✅ 우선순위 로직: `IS_CRITICAL` 전역 변수 관리

### Frontend (React)
- ✅ WebSocket 연결: `window.location.hostname` 자동 감지
- ✅ react-toastify 통합
- ✅ Toast 알림: type에 따라 색상 및 유지 시간 자동 설정
  - `CRITICAL`: 빨간색, 10초
  - `WARNING`: 주황색, 8초
  - `RESOLVED`: 초록색, 5초

## 📝 참고사항

1. **Grafana Webhook URL**: 백엔드 서버 시작 시 콘솔에 출력된 URL을 복사하여 Grafana에 등록하세요.
2. **WebSocket 주소**: 프론트엔드와 백엔드가 다른 서버에서 실행되는 경우, 환경 변수 또는 코드에서 IP 주소를 수정하세요.
3. **네트워크 설정**: Grafana 서버가 백엔드 서버에 접근할 수 있도록 방화벽 설정을 확인하세요.

## 🔥 방화벽 설정 (Windows)

### 8000번 포트 열기
Windows 방화벽에서 8000번 포트를 열어야 외부에서 접속할 수 있습니다:

```powershell
# 관리자 권한으로 PowerShell 실행 후:
netsh advfirewall firewall add rule name="FastAPI Port 8000" dir=in action=allow protocol=TCP localport=8000
```

### 방화벽 규칙 확인
```powershell
netsh advfirewall firewall show rule name="FastAPI Port 8000"
```

### 서버 시작 시 주의사항
- ✅ **반드시 `--host 0.0.0.0` 옵션 사용**: 이 옵션이 없으면 localhost에서만 접속 가능
- ✅ **방화벽에서 8000번 포트 허용**: 외부 접속을 위해 필수

