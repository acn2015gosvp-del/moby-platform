# 모니터링 가이드

MOBY Platform의 모니터링 및 메트릭 수집에 대한 가이드입니다.

## 📊 모니터링 개요

MOBY Platform은 다음 모니터링 기능을 제공합니다:

1. **Prometheus 메트릭**: HTTP 요청, 응답 시간, 에러율 등
2. **헬스체크 엔드포인트**: 시스템 및 서비스 상태 확인
3. **로깅**: 구조화된 로그 파일 및 콘솔 출력

---

## 🔍 Prometheus 메트릭

### 메트릭 엔드포인트

**URL**: `http://localhost:8001/metrics`

**설명**: Prometheus 형식의 메트릭을 제공합니다.

**예시 응답**:
```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",status="200",endpoint="/health"} 42.0

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/health",le="0.005"} 35.0
http_request_duration_seconds_bucket{method="GET",endpoint="/health",le="0.01"} 40.0
http_request_duration_seconds_bucket{method="GET",endpoint="/health",le="+Inf"} 42.0
```

### 수집되는 메트릭

#### 1. HTTP 요청 메트릭
- `http_requests_total`: 총 HTTP 요청 수 (method, status, endpoint별)
- `http_request_duration_seconds`: HTTP 요청 처리 시간 (히스토그램)
- `http_requests_inprogress`: 현재 처리 중인 요청 수

#### 2. 제외된 엔드포인트
다음 엔드포인트는 메트릭 수집에서 제외됩니다:
- `/metrics` (메트릭 엔드포인트 자체)
- `/health` (헬스체크)
- `/health/liveness` (Liveness 프로브)
- `/health/readiness` (Readiness 프로브)

### Prometheus 설정 예시

`prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'moby-platform'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8001']
        labels:
          environment: 'production'
          service: 'moby-backend'
```

---

## 🏥 헬스체크 엔드포인트

### 1. 전체 헬스체크

**URL**: `GET /health`

**설명**: 모든 서비스의 상태를 확인합니다.

**응답 예시**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2025-01-XXT10:00:00Z",
    "version": "1.0.0",
    "uptime_seconds": 3600.5,
    "services": {
      "mqtt": {
        "name": "mqtt",
        "status": "healthy",
        "message": "Connected",
        "details": {
          "host": "localhost",
          "port": 1883,
          "queue_size": 0
        }
      },
      "influxdb": {
        "name": "influxdb",
        "status": "healthy",
        "message": "Connected",
        "details": {
          "url": "http://localhost:8086",
          "org": "WISE",
          "bucket": "moby-data",
          "buffer_size": 0
        }
      },
      "database": {
        "name": "database",
        "status": "healthy",
        "message": "Connected"
      },
      "grafana": {
        "name": "grafana",
        "status": "degraded",
        "message": "Grafana client not configured"
      }
    }
  },
  "message": "Health check completed"
}
```

**상태 값**:
- `healthy`: 서비스가 정상 작동
- `degraded`: 일부 기능 제한되지만 핵심 기능은 작동
- `unhealthy`: 서비스가 비정상

### 2. Liveness 프로브

**URL**: `GET /health/liveness`

**설명**: Kubernetes Liveness 프로브용. 애플리케이션이 살아있는지만 확인합니다.

**응답**: 항상 200 OK

### 3. Readiness 프로브

**URL**: `GET /health/readiness`

**설명**: Kubernetes Readiness 프로브용. 애플리케이션이 요청을 처리할 준비가 되었는지 확인합니다.

**응답**:
- `200 OK`: 준비 완료
- `503 Service Unavailable`: 준비되지 않음

---

## 📝 로깅

### 로그 레벨

환경에 따라 자동으로 로그 레벨이 설정됩니다:

- **프로덕션**: `INFO` 이상 (기본값)
- **개발**: `INFO` (기본값)
- **디버그 모드**: `DEBUG` (모든 로그 출력)

### 로그 파일 위치

- **프로덕션**: `logs/moby.log`
- **개발/디버그**: `logs/moby-debug.log`

### 로그 포맷

```
2025-01-XX 10:00:00 | INFO     | backend.api.routes_health | routes_health.py:241 | Health check completed
```

포맷: `%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s`

### 서드파티 라이브러리 로그 레벨

다음 라이브러리의 로그 레벨이 자동으로 조정됩니다:

- **프로덕션**: `WARNING` 이상
- **개발**: `INFO` 이상
- **디버그 모드**: `DEBUG`

조정되는 라이브러리:
- `uvicorn`
- `uvicorn.access`
- `fastapi`
- `paho` (MQTT)
- `influxdb_client`
- `openai`
- `httpx`
- `httpcore`

---

## 📈 Grafana 대시보드 설정

### Prometheus 데이터 소스 추가

1. Grafana에 로그인
2. **Configuration** → **Data Sources** → **Add data source**
3. **Prometheus** 선택
4. **URL**: `http://localhost:9090` (Prometheus 서버 주소)
5. **Save & Test**

### 대시보드 예시

#### HTTP 요청 메트릭
```
# 총 요청 수
sum(rate(http_requests_total[5m])) by (method, status)

# 평균 응답 시간
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# 에러율
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
```

#### 현재 처리 중인 요청
```
http_requests_inprogress
```

---

## 🔧 모니터링 설정

### 환경 변수

`.env` 파일에서 다음 설정을 조정할 수 있습니다:

```env
# 로그 레벨 설정
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# 디버그 모드 (모든 로그 출력)
DEBUG=false

# 환경 설정
ENVIRONMENT=dev  # dev, prod, production
```

### 로그 파일 비활성화

로그 파일을 비활성화하려면 `main.py`의 `setup_logging()` 호출에서 `log_file=None`을 전달하세요.

---

## 🚨 알림 설정

### Prometheus Alertmanager

Prometheus Alertmanager를 사용하여 다음 조건에서 알림을 받을 수 있습니다:

1. **높은 에러율**: `rate(http_requests_total{status=~"5.."}[5m]) > 0.1`
2. **느린 응답 시간**: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1.0`
3. **서비스 다운**: `/health` 엔드포인트가 `unhealthy` 반환

### 예시 Alert 규칙

`alerts.yml`:
```yaml
groups:
  - name: moby_platform
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "높은 에러율 감지"
          description: "에러율이 10%를 초과했습니다."

      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "느린 응답 시간"
          description: "95 백분위 응답 시간이 1초를 초과했습니다."
```

---

## 📚 참고 자료

- [Prometheus 공식 문서](https://prometheus.io/docs/)
- [Grafana 대시보드 가이드](https://grafana.com/docs/grafana/latest/dashboards/)
- [FastAPI Instrumentator 문서](https://github.com/trallnag/prometheus-fastapi-instrumentator)

---

**최종 업데이트**: 2025-01-XX

