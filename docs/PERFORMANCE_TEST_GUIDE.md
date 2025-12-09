# 성능 테스트 가이드

MOBY Platform의 성능 테스트 방법 및 기준입니다.

## 📋 개요

이 가이드는 MOBY Platform의 성능을 측정하고 최적화하는 방법을 제공합니다.

---

## 🎯 성능 목표

### 응답 시간
- **API 엔드포인트**: 평균 200ms 이하
- **보고서 생성**: 30초 이하
- **헬스체크**: 50ms 이하

### 처리량
- **동시 요청**: 최소 100 req/s
- **Rate Limiting**: 100 req/min (기본값)

### 리소스 사용량
- **메모리**: 평균 500MB 이하
- **CPU**: 평균 20% 이하 (유휴 상태)

---

## 🧪 테스트 도구

### 1. Apache Bench (ab)
```bash
# 설치 (Ubuntu/Debian)
sudo apt-get install apache2-utils

# 설치 (macOS)
brew install apache-bench
```

### 2. wrk
```bash
# 설치 (Ubuntu/Debian)
sudo apt-get install wrk

# 설치 (macOS)
brew install wrk
```

### 3. Python 스크립트 (기존 성능 테스트)
```bash
cd backend
python -m pytest tests/test_performance.py -v
```

---

## 📊 테스트 시나리오

### 1. 단일 요청 지연 시간 테스트

**목적**: 개별 API 엔드포인트의 응답 시간 측정

**방법**:
```bash
# 헬스체크
ab -n 100 -c 1 http://localhost:8001/health

# 센서 상태 조회
ab -n 100 -c 1 -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8001/sensors/status

# 알림 목록 조회
ab -n 100 -c 1 -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8001/alerts/latest
```

**기준**:
- 평균 응답 시간: 200ms 이하
- 95 백분위: 500ms 이하
- 99 백분위: 1000ms 이하

### 2. 동시 요청 처리 테스트

**목적**: 동시 다수 요청 처리 능력 측정

**방법**:
```bash
# 10개 동시 연결, 총 1000개 요청
ab -n 1000 -c 10 http://localhost:8001/health

# wrk 사용 (더 정확한 측정)
wrk -t4 -c100 -d30s http://localhost:8001/health
```

**기준**:
- 처리량: 최소 100 req/s
- 오류율: 0.1% 이하
- 응답 시간 증가: 동시 연결 수에 비례하여 선형 증가

### 3. 보고서 생성 성능 테스트

**목적**: LLM 기반 보고서 생성 시간 측정

**방법**:
```python
import time
import requests

start = time.time()
response = requests.post(
    'http://localhost:8001/reports/generate',
    headers={'Authorization': 'Bearer YOUR_TOKEN'},
    json={
        'period_start': '2025-11-07 09:00:00',
        'period_end': '2025-11-14 09:00:00',
        'equipment': 'Conveyor A-01'
    }
)
elapsed = time.time() - start
print(f"보고서 생성 시간: {elapsed:.2f}초")
```

**기준**:
- 평균 생성 시간: 30초 이하
- 최대 생성 시간: 60초 이하

### 4. 메모리 사용량 모니터링

**방법**:
```bash
# 프로세스 메모리 사용량 확인
ps aux | grep uvicorn

# 또는 htop 사용
htop
```

**기준**:
- 평균 메모리: 500MB 이하
- 최대 메모리: 1GB 이하

### 5. 데이터베이스 쿼리 성능

**방법**:
```python
import time
from backend.api.services.database import SessionLocal
from backend.api.services.alert_storage import get_latest_alerts

db = SessionLocal()
start = time.time()
alerts = get_latest_alerts(db, limit=1000)
elapsed = time.time() - start
print(f"알람 조회 시간: {elapsed:.2f}초")
```

**기준**:
- 1000개 알람 조회: 100ms 이하
- 인덱스 활용 확인

---

## 🔧 최적화 체크리스트

### 캐싱
- [ ] 센서 상태 조회 결과 캐싱 활성화
- [ ] LLM 요약 결과 캐싱 활성화
- [ ] 캐시 히트율 모니터링

### 데이터베이스
- [ ] 인덱스 추가 확인
- [ ] 쿼리 최적화 확인
- [ ] 연결 풀링 설정 확인

### API 최적화
- [ ] 불필요한 데이터 로딩 제거
- [ ] 페이지네이션 적용
- [ ] 응답 데이터 크기 최소화

### Frontend 최적화
- [ ] 코드 스플리팅 확인
- [ ] 번들 크기 확인
- [ ] 이미지 최적화 적용

---

## 📈 모니터링

### Prometheus 메트릭 확인
```bash
curl http://localhost:8001/metrics | grep http_request_duration
```

**주요 메트릭**:
- `http_request_duration_seconds`: 요청 처리 시간
- `http_requests_total`: 총 요청 수
- `http_requests_inprogress`: 현재 처리 중인 요청 수

### 로그 분석
```bash
# 느린 요청 확인
grep "slow" logs/moby.log

# 오류 확인
grep "ERROR" logs/moby.log
```

---

## 🐛 성능 문제 해결

### 느린 응답 시간
1. 데이터베이스 쿼리 최적화
2. 캐싱 활성화
3. 불필요한 데이터 로딩 제거
4. 인덱스 추가

### 높은 메모리 사용량
1. 메모리 누수 확인
2. 캐시 크기 조정
3. 불필요한 데이터 제거

### 높은 CPU 사용량
1. 비효율적인 알고리즘 확인
2. 동시 처리 수 제한
3. 백그라운드 작업 최적화

---

## 📚 참고 자료

- [FastAPI 성능 최적화](https://fastapi.tiangolo.com/advanced/performance/)
- [Python 프로파일링](https://docs.python.org/3/library/profile.html)
- [Prometheus 쿼리 가이드](https://prometheus.io/docs/prometheus/latest/querying/basics/)

---

**최종 업데이트**: 2025-01-XX

