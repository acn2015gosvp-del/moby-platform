# Edge Inference Worker 업데이트 가이드

## 목표
`inference_worker.py`를 수정하여 Grafana 대시보드에 필요한 파생 데이터(health, slope 등)를 생성해 MQTT로 함께 전송한다.

## 사용법
`moby-edge` 프로젝트에서 `src/inference_worker.py`를 열고 아래 코드를 적용하세요.

---

## 수정 위치
**Target Method:** `_on_message` 내부, `client.publish` 호출 직전

## 추가할 로직

`results` 리스트를 순회하며 `context_payload["fields"]`에 다음 데이터를 계산하여 추가:

### 1. health (String)
- `mlp_s1_prob_red > 0.5` OR `mlp_s2_prob_red > 0.5` → `"CRITICAL"`
- `mlp_s1_prob_yellow > 0.5` OR `mlp_s2_prob_yellow > 0.5` → `"WARNING"`
- Else → `"NORMAL"`

### 2. rul_hours (Float)
- CRITICAL → `10.0`
- WARNING → `50.0`
- NORMAL → `100.0` (데모용 가상 로직)

### 3. fail_time (String)
- 현재 시간 + `rul_hours` 포맷: `%Y-%m-%d %H:%M`

### 4. slope (Float)
- CRITICAL → `0.1`
- else → `0.01`

---

## 구현 코드

```python
# Inside _on_message loop, before client.publish:

from datetime import datetime, timedelta

# results 리스트를 순회
for result in results:
    fields = result.context_payload.get("fields", {})
    
    # Health Check
    s1_red = fields.get("mlp_s1_prob_red", 0)
    s2_red = fields.get("mlp_s2_prob_red", 0)
    s1_yel = fields.get("mlp_s1_prob_yellow", 0)
    s2_yel = fields.get("mlp_s2_prob_yellow", 0)
    
    if s1_red > 0.5 or s2_red > 0.5:
        fields["health"] = "CRITICAL"
    elif s1_yel > 0.5 or s2_yel > 0.5:
        fields["health"] = "WARNING"
    else:
        fields["health"] = "NORMAL"
    
    # RUL & Slope (Simulation)
    if fields["health"] == "CRITICAL":
        fields["rul_hours"] = 10.0
        fields["slope"] = 0.1
    elif fields["health"] == "WARNING":
        fields["rul_hours"] = 50.0
        fields["slope"] = 0.01
    else:  # NORMAL
        fields["rul_hours"] = 100.0
        fields["slope"] = 0.01
    
    # Fail Time
    fail_datetime = datetime.now() + timedelta(hours=fields["rul_hours"])
    fields["fail_time"] = fail_datetime.strftime("%Y-%m-%d %H:%M")
    
    # context_payload 업데이트
    result.context_payload["fields"] = fields

# 이후 client.publish 호출
```

---

## 전체 예시 코드 구조

```python
def _on_message(self, client, userdata, msg):
    """
    MQTT 메시지 수신 시 추론을 수행하고 결과를 발행합니다.
    """
    try:
        # 메시지 파싱
        data = json.loads(msg.payload.decode())
        
        # 추론 수행
        results = self.inference_engine.process(data)
        
        # 파생 필드 추가 (여기에 위 코드 삽입)
        from datetime import datetime, timedelta
        
        for result in results:
            fields = result.context_payload.get("fields", {})
            
            # Health Check
            s1_red = fields.get("mlp_s1_prob_red", 0)
            s2_red = fields.get("mlp_s2_prob_red", 0)
            s1_yel = fields.get("mlp_s1_prob_yellow", 0)
            s2_yel = fields.get("mlp_s2_prob_yellow", 0)
            
            if s1_red > 0.5 or s2_red > 0.5:
                fields["health"] = "CRITICAL"
            elif s1_yel > 0.5 or s2_yel > 0.5:
                fields["health"] = "WARNING"
            else:
                fields["health"] = "NORMAL"
            
            # RUL & Slope
            if fields["health"] == "CRITICAL":
                fields["rul_hours"] = 10.0
                fields["slope"] = 0.1
            elif fields["health"] == "WARNING":
                fields["rul_hours"] = 50.0
                fields["slope"] = 0.01
            else:
                fields["rul_hours"] = 100.0
                fields["slope"] = 0.01
            
            # Fail Time
            fail_datetime = datetime.now() + timedelta(hours=fields["rul_hours"])
            fields["fail_time"] = fail_datetime.strftime("%Y-%m-%d %H:%M")
            
            # context_payload 업데이트
            result.context_payload["fields"] = fields
        
        # MQTT 발행
        for result in results:
            topic = f"factory/inference/results/{result.device_id}"
            payload = json.dumps({
                "model_name": result.model_name,
                "sensor_type": result.sensor_type,
                "context_payload": result.context_payload
            })
            client.publish(topic, payload, qos=1)
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")
```

---

## 추가된 필드 설명

### health
- **타입:** String
- **값:** `"CRITICAL"`, `"WARNING"`, `"NORMAL"`
- **용도:** Grafana 대시보드에서 상태 표시

### rul_hours
- **타입:** Float
- **값:** 
  - CRITICAL: `10.0` 시간
  - WARNING: `50.0` 시간
  - NORMAL: `100.0` 시간
- **용도:** Remaining Useful Life (잔여 수명) 시각화

### fail_time
- **타입:** String
- **형식:** `"%Y-%m-%d %H:%M"` (예: `"2025-11-27 15:30"`)
- **용도:** 예상 고장 시간 표시

### slope
- **타입:** Float
- **값:**
  - CRITICAL: `0.1` (급격한 성능 저하)
  - WARNING/NORMAL: `0.01` (완만한 성능 저하)
- **용도:** 성능 저하 추세 시각화

---

## 테스트 방법

1. Edge 디바이스에서 추론 실행
2. MQTT 메시지 확인:
   ```bash
   mosquitto_sub -h localhost -p 1883 -t "factory/inference/results/#" -v
   ```
3. 발행된 메시지에 다음 필드가 포함되어 있는지 확인:
   - `health`
   - `rul_hours`
   - `fail_time`
   - `slope`

---

## 주의사항

- `datetime.now()`는 Edge 디바이스의 로컬 시간을 사용합니다
- 시간대 설정이 올바른지 확인하세요
- `rul_hours`는 데모용 가상 로직이므로, 실제 RUL 계산 로직으로 교체해야 합니다

