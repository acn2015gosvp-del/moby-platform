# Backend MQTT AI 핸들러 구현 가이드

## 목표
Edge에서 오는 데이터를 수신하되, 데모를 위해 ID를 강제 지정하고 확률 기반으로 알림을 발송한다.

## 현재 구현 상태

✅ **이미 구현 완료됨**

현재 `backend/api/services/mqtt_ai_subscriber.py`에 모든 요구사항이 구현되어 있습니다.

---

## 구현 위치

**파일:** `backend/api/services/mqtt_ai_subscriber.py`
**함수:** `process_ai_alert_mqtt(topic: str, payload: bytes)`

**호출 위치:** `backend/api/services/mqtt_client.py`의 `_on_message` 메서드에서 호출됨

---

## 요구사항 대응 현황

### ✅ 1. 토픽 구독
- **요구사항:** `factory/inference/results/#`
- **구현:** `mqtt_client.py`에서 구독
  ```python
  client.subscribe("factory/inference/results/#", qos=1)
  ```

### ✅ 2. Device ID 하드코딩
- **요구사항:** `device_id = "Demo-Conveyor-01"`
- **구현:** `mqtt_ai_subscriber.py` Line 156
  ```python
  device_id = "Demo-Conveyor-01"
  ```

### ✅ 3. Deep Parsing
- **요구사항:** `context_payload.fields`에서 확률값 읽기
- **구현:** `parse_ai_result()` 함수에서 처리
  ```python
  fields = data.get("context_payload", {}).get("fields", {})
  s1_probs = {
      "정상": fields.get("mlp_s1_prob_normal", 0),
      "주의": fields.get("mlp_s1_prob_yellow", 0),
      "위험": fields.get("mlp_s1_prob_red", 0)
  }
  ```

### ✅ 4. Decision Logic (Argmax)
- **요구사항:** S1, S2 각각 가장 높은 확률 찾기
- **구현:** `parse_ai_result()` 함수
  ```python
  s1_status = max(s1_probs, key=s1_probs.get)  # argmax
  s2_status = max(s2_probs, key=s2_probs.get)  # argmax
  ```

### ✅ 5. Priority Check
- **요구사항:** `IS_CRITICAL_ACTIVE`가 True면 무시
- **구현:** `alert_state_manager.is_critical_active` 사용
  ```python
  state_manager = get_alert_state_manager()
  if state_manager.is_critical_active:
      return  # 알림 무시
  ```

### ✅ 6. WebSocket Broadcast
- **요구사항:** `type: "WARNING"` 메시지 전송
- **구현:** `websocket_notifier.send_alert()` 사용
  ```python
  websocket_payload = {
      "type": "WARNING",
      "message": f"⚠️ [AI 예지] {msg_content} 감지",
      "sensor": "AI-Model",
      "color": "orange"
  }
  await notifier.send_alert(websocket_payload)
  ```

---

## 코드 구조

### 현재 아키텍처

```
MQTT 메시지 수신
    ↓
mqtt_client.py (_on_message)
    ↓
mqtt_ai_subscriber.py (process_ai_alert_mqtt)
    ↓
parse_ai_result() - 확률 분석
    ↓
alert_state_manager - 우선순위 체크
    ↓
websocket_notifier - WebSocket 전송
    ↓
프론트엔드 (실시간 알림 표시)
```

### 핵심 함수

#### 1. `parse_ai_result(data: dict) -> Tuple[str, str]`
- 확률값 분석 및 상태 판정
- 반환: `(level, message)`

#### 2. `process_ai_alert_mqtt(topic: str, payload: bytes)`
- MQTT 메시지 처리 메인 함수
- 토픽 필터링, 우선순위 체크, WebSocket 전송

---

## 프롬프트 요구사항 vs 실제 구현

| 요구사항 | 프롬프트 | 실제 구현 | 상태 |
|---------|---------|----------|------|
| 토픽 구독 | `factory/inference/results/#` | ✅ 동일 | 완료 |
| Device ID | `"Demo-Conveyor-01"` | ✅ 동일 | 완료 |
| 확률 파싱 | `context_payload.fields` | ✅ 동일 | 완료 |
| Argmax 로직 | S1/S2 최고 확률 | ✅ 동일 | 완료 |
| 우선순위 체크 | `IS_CRITICAL_ACTIVE` | ✅ `is_critical_active` | 완료 |
| WebSocket | `type: "WARNING"` | ✅ 동일 | 완료 |

---

## 프롬프트 스타일 코드 (참고용)

프롬프트에서 요구한 스타일의 코드는 다음과 같습니다:

```python
# main.py에 직접 추가하는 스타일 (현재는 서비스 레이어로 분리됨)

@mqtt.on_message()
async def handle_inference_result(client, topic, payload, qos, properties):
    if not topic.startswith("factory/inference/results"):
        return
    
    try:
        data = json.loads(payload)
        
        if data.get("model_name") == "mlp_classifier":
            # 1. Demo ID Force
            device_id = "Demo-Conveyor-01"
            
            # 2. Parse Probs & Determine Level
            fields = data.get("context_payload", {}).get("fields", {})
            
            s1_probs = {
                "정상": fields.get("mlp_s1_prob_normal", 0),
                "주의": fields.get("mlp_s1_prob_yellow", 0),
                "위험": fields.get("mlp_s1_prob_red", 0)
            }
            s2_probs = {
                "정상": fields.get("mlp_s2_prob_normal", 0),
                "주의": fields.get("mlp_s2_prob_yellow", 0),
                "위험": fields.get("mlp_s2_prob_red", 0)
            }
            
            s1_status = max(s1_probs, key=s1_probs.get)
            s2_status = max(s2_probs, key=s2_probs.get)
            
            alerts = []
            level = "NORMAL"
            
            if s1_status == "위험":
                alerts.append(f"속도변동 위험({s1_probs['위험']:.2f})")
                level = "WARNING"
            elif s1_status == "주의":
                alerts.append("속도변동 주의")
                if level == "NORMAL":
                    level = "WARNING"
            
            if s2_status == "위험":
                alerts.append(f"불균형 위험({s2_probs['위험']:.2f})")
                level = "WARNING"
            elif s2_status == "주의":
                alerts.append("불균형 주의")
                if level == "NORMAL":
                    level = "WARNING"
            
            # 3. Priority Check & Broadcast
            from backend.api.services.alert_state_manager import get_alert_state_manager
            from backend.api.services.websocket_notifier import get_websocket_notifier
            
            state_manager = get_alert_state_manager()
            notifier = get_websocket_notifier()
            
            if level != "NORMAL" and not state_manager.is_critical_active:
                msg = ", ".join(alerts)
                await notifier.send_alert({
                    "type": "WARNING",
                    "message": f"⚠️ [AI 예지] {msg} 감지",
                    "sensor": device_id,
                    "color": "orange"
                })
                
    except Exception as e:
        logger.error(f"Error processing AI message: {e}")
```

---

## 현재 구현의 장점

1. **서비스 레이어 분리**: 비즈니스 로직이 명확하게 분리됨
2. **재사용성**: 다른 곳에서도 `process_ai_alert_mqtt` 함수 재사용 가능
3. **테스트 용이성**: 각 함수를 독립적으로 테스트 가능
4. **유지보수성**: 코드 구조가 명확하고 수정이 쉬움

---

## 테스트 방법

### 1. MQTT 테스트 메시지 발행

```bash
mosquitto_pub -h localhost -p 1883 -t "factory/inference/results/test" -m '{
  "model_name": "mlp_classifier",
  "sensor_type": "accel_gyro",
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
}'
```

### 2. 로그 확인

```bash
# 백엔드 로그에서 확인
Get-Content backend\logs\moby-debug.log -Wait -Tail 50
```

**예상 로그:**
```
📨 Edge AI 알림 수신 (MQTT): topic=factory/inference/results/test
✅ Edge AI Warning 알림 처리 및 전송 완료: device_id=Demo-Conveyor-01
🚀 [MQTT AI] WebSocket으로 알림 전송 시도
```

### 3. 프론트엔드 확인

- 브라우저에서 주황색 WARNING 알림이 표시되어야 함
- 5초 후 자동으로 사라짐

---

## 결론

✅ **모든 요구사항이 이미 구현되어 있습니다.**

현재 구현은 프롬프트의 요구사항을 모두 만족하며, 더 나은 아키텍처로 구성되어 있습니다.

추가 작업이 필요하지 않으며, 바로 사용 가능합니다.

