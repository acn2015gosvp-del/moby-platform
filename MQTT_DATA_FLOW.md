# MQTT 데이터 처리 플로우

## 전체 흐름도

```
MQTT 메시지 수신
    ↓
_on_message() 콜백 (mqtt_client.py)
    ↓
토픽 분기
    ├─ sensors/+/data → 센서 데이터 처리
    └─ factory/inference/results/# → 추론 결과 처리
```

---

## 1. 센서 데이터 처리 (`sensors/+/data`)

### 플로우:
```
MQTT 메시지 수신
    ↓
_process_sensor_data() 호출
    ↓
데이터 파싱 (device_id, timestamp, temperature, humidity, vibration, sound)
    ↓
InfluxDB에 저장
    ├─ Measurement: sensor_data
    ├─ Fields: temperature, humidity, vibration, sound
    └─ Tags: device_id, sensor_type
    ↓
✅ 완료 (로깅만)
```

### 특징:
- **InfluxDB에만 저장** (알림 생성 없음)
- **실시간 시계열 데이터**로 저장
- Grafana에서 시각화 가능

---

## 2. 추론 결과 처리 (`factory/inference/results/#`)

### 플로우:
```
MQTT 메시지 수신
    ↓
process_ai_alert_mqtt() 호출
    ↓
1. JSON 파싱
    ↓
2. parse_ai_result() - AI 결과 분석
    ├─ MLP Classifier: 확률값 분석 → WARNING/NORMAL
    └─ Isolation Forest: 점수 분석 → NOTICE/NORMAL
    ↓
3. 정상 상태 체크
    ├─ NORMAL → 종료 (저장 안 함)
    └─ WARNING/NOTICE → 계속 진행
    ↓
4. 우선순위 체크 (IS_CRITICAL_ACTIVE)
    ├─ True → AI 알림 무시 (종료)
    └─ False → 계속 진행
    ↓
5. 백그라운드 스레드에서 처리 시작
    ↓
6. save_and_send() 함수 실행
    ├─ AlertPayloadModel 생성
    ├─ 데이터베이스 저장 (save_alert)
    ├─ InfluxDB 저장 (inference_results)
    ├─ WebSocket 전송 (실시간 알림)
    └─ 이메일 전송 (WARNING만)
    ↓
✅ 완료
```

### 저장 위치:

#### 1. **데이터베이스 (PostgreSQL)**
- **테이블**: `alerts`
- **목적**: 알림 이력 관리, 조회 API 제공
- **데이터**: AlertPayloadModel 구조

#### 2. **InfluxDB Cloud**
- **Measurement**: `inference_results`
- **Fields**: 
  - `level` (warning, notice)
  - `model_name`
  - `sensor_type`
  - `context_payload.fields`의 모든 확률값/점수
- **Tags**:
  - `device_id`
  - `model_name`
  - `sensor_type`
  - `level`
  - `source` (edge-ai-mqtt)
- **목적**: 시계열 데이터 저장, Grafana 시각화

#### 3. **WebSocket**
- **목적**: 프론트엔드 실시간 알림
- **형식**: JSON payload
- **수신자**: 연결된 모든 클라이언트

#### 4. **이메일** (선택적)
- **조건**: WARNING 레벨만 전송
- **NOTICE 레벨은 이메일 전송 안 함**

---

## 주요 파일 위치

### 1. MQTT 메시지 수신
- **파일**: `backend/api/services/mqtt_client.py`
- **함수**: `_on_message()`, `_process_sensor_data()`

### 2. 추론 결과 처리
- **파일**: `backend/api/services/mqtt_ai_subscriber.py`
- **함수**: `process_ai_alert_mqtt()`, `parse_ai_result()`

### 3. InfluxDB 저장
- **파일**: `backend/api/services/influx_client.py`
- **함수**: `influx_manager.write_point()`

### 4. 데이터베이스 저장
- **파일**: `backend/api/services/alert_storage.py`
- **함수**: `save_alert()`

### 5. WebSocket 전송
- **파일**: `backend/api/services/websocket_notifier.py`
- **함수**: `send_alert()`

---

## 데이터 구조 예시

### 센서 데이터 (MQTT)
```json
{
  "device_id": "sensor_001",
  "timestamp": "2025-01-27T10:00:00Z",
  "temperature": 25.5,
  "humidity": 60.0,
  "vibration": 0.3,
  "sound": 45.2
}
```

### 추론 결과 (MQTT)
```json
{
  "sensor_type": "accel_gyro",
  "model_name": "mlp_classifier",
  "context_payload": {
    "fields": {
      "mlp_s1_prob_normal": 0.05,
      "mlp_s1_prob_yellow": 0.10,
      "mlp_s1_prob_red": 0.85,
      "mlp_s2_prob_normal": 0.98,
      "mlp_s2_prob_yellow": 0.02,
      "mlp_s2_prob_red": 0.00
    }
  }
}
```

---

## 주의사항

1. **Telegraf 사용 안 함**: MQTT 메시지를 Python 코드에서 직접 처리
2. **비동기 처리**: 추론 결과는 백그라운드 스레드에서 처리 (UI 블로킹 방지)
3. **우선순위 로직**: CRITICAL 알림이 활성화되어 있으면 AI 알림 무시
4. **정상 상태 필터링**: NORMAL 레벨은 저장하지 않음 (InfluxDB, DB 모두)




