# API 문서

**작성일**: 2025-11-17  
**버전**: 1.0.0  
**기준 URL**: `http://localhost:8000` (개발 환경)

---

## 📋 목차

1. [개요](#개요)
2. [인증](#인증)
3. [엔드포인트](#엔드포인트)
4. [응답 형식](#응답-형식)
5. [에러 처리](#에러-처리)
6. [예제](#예제)

---

## 개요

MOBY Platform API는 RESTful API를 제공하며, 모든 응답은 JSON 형식입니다.

### Base URL

```
Development: http://localhost:8000
Production: https://api.moby-platform.com
```

### API 버전

현재 버전: `v1` (버전 정보는 URL에 포함되지 않음)

---

## 인증

현재는 인증이 구현되지 않았습니다. 향후 JWT 토큰 기반 인증이 추가될 예정입니다.

---

## 엔드포인트

### 알림 (Alerts)

#### POST `/alerts/evaluate`

알림을 생성하고 평가합니다.

**요청 본문:**
```json
{
  "vector": [1.5, 2.3, 3.1],
  "threshold": 5.0,
  "sensor_id": "sensor_001",
  "enable_llm_summary": true
}
```

**요청 필드:**
- `vector` (필수): 이상 탐지에 사용할 벡터 데이터 (배열)
- `threshold` (선택): 단일 임계값
- `warning_threshold` (선택): 경고 임계값 (critical_threshold와 함께 사용)
- `critical_threshold` (선택): 심각 임계값 (warning_threshold와 함께 사용)
- `sensor_id` (선택): 센서 ID (기본값: "unknown_sensor")
- `enable_llm_summary` (선택): LLM 요약 생성 여부 (기본값: true)
- `message` (선택): 알림 메시지
- `meta` (선택): 추가 메타데이터

**응답:**

성공 (201 Created):
```json
{
  "success": true,
  "data": {
    "id": "alert_abc123",
    "level": "warning",
    "message": "Anomaly detected",
    "llm_summary": "센서 데이터에서 이상 징후가 감지되었습니다...",
    "sensor_id": "sensor_001",
    "source": "alert-engine",
    "ts": "2025-11-17T18:00:00Z",
    "details": {
      "vector": [1.5, 2.3, 3.1],
      "norm": 4.1,
      "threshold": 5.0,
      "severity": "warning"
    }
  },
  "message": "Alert alert_abc123 created and dispatched successfully"
}
```

이상 없음 (204 No Content):
- 응답 본문 없음

에러 (400 Bad Request):
```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "Invalid request data: ...",
    "field": "request"
  },
  "timestamp": "2025-11-17T18:00:00Z"
}
```

**예제:**
```bash
curl -X POST "http://localhost:8000/alerts/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [1.5, 2.3, 3.1],
    "threshold": 5.0,
    "sensor_id": "sensor_001"
  }'
```

---

#### POST `/alerts/evaluate-legacy` (Deprecated)

레거시 형식의 알림 응답을 반환하는 엔드포인트입니다.

**참고:** 이 엔드포인트는 하위 호환성을 위해 유지됩니다. 새로운 프로젝트는 `/evaluate` 엔드포인트를 사용하는 것을 권장합니다.

**응답:**
```json
{
  "success": true,
  "data": {
    "status": "warning",
    "message": "Anomaly detected",
    "llm_summary": "..."
  },
  "message": "Alert processed successfully"
}
```

---

### 센서 (Sensors)

#### POST `/sensors/data`

Edge 장치로부터 센서 데이터를 수신합니다.

**요청 본문:**
```json
{
  "device_id": "sensor_001",
  "temperature": 25.5,
  "humidity": 60.0,
  "vibration": 0.5,
  "sound": 45.2
}
```

**요청 필드:**
- `device_id` (필수): 센서 장치 ID
- `temperature` (선택): 온도 데이터
- `humidity` (선택): 습도 데이터
- `vibration` (선택): 진동 데이터
- `sound` (선택): 소리 데이터

**응답:**

성공 (202 Accepted):
```json
{
  "success": true,
  "data": {
    "status": "received",
    "sensor_id": "sensor_001",
    "timestamp": "2025-11-17T18:00:00Z"
  },
  "message": "Sensor data from sensor_001 received successfully"
}
```

**예제:**
```bash
curl -X POST "http://localhost:8000/sensors/data" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "sensor_001",
    "temperature": 25.5,
    "humidity": 60.0
  }'
```

---

#### GET `/sensors/status`

전체 센서의 연결 상태를 조회합니다.

**응답:**

성공 (200 OK):
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "count": 10,
    "active": 9,
    "inactive": 1
  },
  "message": "Sensor status retrieved successfully"
}
```

**예제:**
```bash
curl "http://localhost:8000/sensors/status"
```

---

## 응답 형식

### 성공 응답

모든 성공 응답은 다음 형식을 따릅니다:

```json
{
  "success": true,
  "data": <응답 데이터>,
  "message": "Optional success message"
}
```

### 페이지네이션 응답

리스트 응답의 경우 페이지네이션 정보가 포함됩니다:

```json
{
  "success": true,
  "data": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "has_next": true,
  "has_prev": false
}
```

---

## 에러 처리

### 에러 응답 형식

모든 에러 응답은 다음 형식을 따릅니다:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지",
    "field": "에러가 발생한 필드 (선택사항)"
  },
  "timestamp": "2025-11-17T18:00:00Z"
}
```

### HTTP 상태 코드

- `200 OK`: 요청 성공
- `201 Created`: 리소스 생성 성공
- `202 Accepted`: 요청 수락 (비동기 처리)
- `204 No Content`: 요청 성공 (응답 본문 없음)
- `400 Bad Request`: 잘못된 요청
- `404 Not Found`: 리소스를 찾을 수 없음
- `422 Unprocessable Entity`: 입력 데이터 검증 실패
- `500 Internal Server Error`: 서버 내부 오류

### 에러 코드

- `BAD_REQUEST`: 잘못된 요청
- `VALIDATION_ERROR`: 입력 데이터 검증 실패
- `NOT_FOUND`: 리소스를 찾을 수 없음
- `INTERNAL_ERROR`: 서버 내부 오류

---

## 예제

### Python 예제

```python
import requests

# 알림 생성
response = requests.post(
    "http://localhost:8000/alerts/evaluate",
    json={
        "vector": [1.5, 2.3, 3.1],
        "threshold": 5.0,
        "sensor_id": "sensor_001"
    }
)
print(response.json())

# 센서 데이터 전송
response = requests.post(
    "http://localhost:8000/sensors/data",
    json={
        "device_id": "sensor_001",
        "temperature": 25.5,
        "humidity": 60.0
    }
)
print(response.json())

# 센서 상태 조회
response = requests.get("http://localhost:8000/sensors/status")
print(response.json())
```

### JavaScript 예제

```javascript
// 알림 생성
const response = await fetch('http://localhost:8000/alerts/evaluate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    vector: [1.5, 2.3, 3.1],
    threshold: 5.0,
    sensor_id: 'sensor_001'
  })
});

const data = await response.json();
console.log(data);
```

---

## Swagger UI

API 문서는 Swagger UI를 통해 확인할 수 있습니다:

- **개발 서버 실행 후**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Swagger UI에서는 모든 엔드포인트를 테스트할 수 있습니다.

---

## 변경 이력

### v1.0.0 (2025-11-17)
- 초기 API 문서 작성
- 알림 평가 엔드포인트 문서화
- 센서 데이터 수신 엔드포인트 문서화
- 표준화된 응답 형식 정의

---

**참고**: 이 문서는 개발자 B가 작성 및 유지보수합니다.

