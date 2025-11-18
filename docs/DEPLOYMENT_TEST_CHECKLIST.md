# 배포 테스트 체크리스트

MOBY Platform 배포 전 필수 테스트 항목입니다.

## 📋 사전 준비

### 환경 변수 확인
- [ ] `.env` 파일 생성 및 필수 변수 설정
- [ ] `SECRET_KEY` 변경 (프로덕션 환경)
- [ ] `GEMINI_API_KEY` 설정 (보고서 생성 기능 사용 시)
- [ ] `OPENAI_API_KEY` 설정 (LLM 요약 기능 사용 시)
- [ ] InfluxDB 연결 정보 확인
- [ ] MQTT Broker 연결 정보 확인

### 의존성 설치
- [ ] Backend 의존성 설치: `pip install -r requirements.txt`
- [ ] Frontend 의존성 설치: `cd frontend && npm install`
- [ ] `google-generativeai` 패키지 설치 확인

---

## 🧪 기능 테스트

### 1. Backend 서버 시작
```bash
# 프로젝트 루트에서 실행
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
```

**확인 사항**:
- [ ] 서버가 정상적으로 시작됨
- [ ] 환경 변수 검증 통과 (프로덕션 환경)
- [ ] 데이터베이스 테이블 자동 생성
- [ ] MQTT 클라이언트 연결 시도
- [ ] 로그에 오류 없음

**확인 URL**:
- [ ] http://localhost:8001/ → `{"status":"ok","message":"MOBY backend running"}`
- [ ] http://localhost:8001/docs → Swagger UI 표시
- [ ] http://localhost:8001/health → 헬스체크 응답 확인

### 2. Frontend 서버 시작
```bash
cd frontend
npm run dev
```

**확인 사항**:
- [ ] 서버가 정상적으로 시작됨 (포트 3000)
- [ ] 브라우저 콘솔에 오류 없음
- [ ] 페이지 로딩 정상

**확인 URL**:
- [ ] http://localhost:3000/ → 로그인 페이지 표시

### 3. 인증 기능
- [ ] 회원가입 성공
- [ ] 로그인 성공
- [ ] JWT 토큰 발급 확인
- [ ] 로그아웃 기능

### 4. 센서 데이터
- [ ] 센서 상태 조회 (`GET /sensors/status`)
- [ ] 센서 데이터 수신 (`POST /sensors/data`)
- [ ] MQTT 메시지 구독 확인

### 5. 알림 기능
- [ ] 알림 생성 (`POST /alerts/evaluate`)
- [ ] 알림 목록 조회 (`GET /alerts/latest`)
- [ ] WebSocket을 통한 실시간 알림 수신

### 6. 보고서 생성
- [ ] 보고서 생성 API 호출 (`POST /reports/generate`)
- [ ] 보고서 내용 확인
- [ ] 웹 UI에서 보고서 생성 및 다운로드

### 7. Grafana 연동 (선택사항)
- [ ] 데이터 소스 생성 (`POST /grafana/datasource`)
- [ ] 대시보드 생성 (`POST /grafana/dashboard`)

---

## 🔍 헬스체크 테스트

### 전체 헬스체크
```bash
curl http://localhost:8001/health
```

**확인 사항**:
- [ ] 응답 상태 코드: 200
- [ ] 모든 서비스 상태 확인
  - [ ] MQTT: `healthy` 또는 `degraded`
  - [ ] InfluxDB: `healthy` 또는 `unhealthy`
  - [ ] Database: `healthy`
  - [ ] Grafana: `healthy` 또는 `degraded` (선택사항)

### Liveness 프로브
```bash
curl http://localhost:8001/health/liveness
```

**확인 사항**:
- [ ] 응답 상태 코드: 200
- [ ] `{"status":"alive"}` 응답

### Readiness 프로브
```bash
curl http://localhost:8001/health/readiness
```

**확인 사항**:
- [ ] 응답 상태 코드: 200
- [ ] `{"status":"ready"}` 응답

---

## 📊 모니터링 테스트

### Prometheus 메트릭
```bash
curl http://localhost:8001/metrics
```

**확인 사항**:
- [ ] Prometheus 형식의 메트릭 출력
- [ ] `http_requests_total` 메트릭 존재
- [ ] `http_request_duration_seconds` 메트릭 존재

---

## 🐛 오류 처리 테스트

### 잘못된 요청
- [ ] 잘못된 인증 토큰 → 401 Unauthorized
- [ ] 권한 없는 요청 → 403 Forbidden
- [ ] 잘못된 데이터 형식 → 422 Unprocessable Entity
- [ ] 존재하지 않는 리소스 → 404 Not Found

### Rate Limiting
- [ ] 1분에 100회 이상 요청 → 429 Too Many Requests
- [ ] Rate Limit 헤더 확인 (`X-RateLimit-*`)

---

## 🔒 보안 테스트

### CSRF 보호 (프로덕션 환경)
- [ ] CSRF 토큰 없이 POST 요청 → 403 Forbidden
- [ ] 유효한 CSRF 토큰으로 요청 → 성공

### 인증/인가
- [ ] 관리자 권한 필요 엔드포인트 접근 테스트
- [ ] 사용자 권한 필요 엔드포인트 접근 테스트
- [ ] 뷰어 권한으로 쓰기 작업 시도 → 403 Forbidden

---

## 📝 로깅 확인

### 로그 파일 확인
```bash
# 프로덕션
cat logs/moby.log

# 개발/디버그
cat logs/moby-debug.log
```

**확인 사항**:
- [ ] 로그 파일 생성됨
- [ ] 로그 레벨 적절히 설정됨
- [ ] 오류 로그 없음
- [ ] 환경별 로그 레벨 차이 확인

---

## 🚀 Docker 배포 테스트 (선택사항)

### Docker Compose 실행
```bash
docker-compose up -d
```

**확인 사항**:
- [ ] 모든 컨테이너 정상 실행
- [ ] Backend 서비스 접근 가능
- [ ] Frontend 서비스 접근 가능
- [ ] 데이터베이스 연결 확인

### 로그 확인
```bash
docker-compose logs -f
```

---

## ✅ 최종 확인

- [ ] 모든 기능 테스트 통과
- [ ] 오류 없음
- [ ] 성능 기준 충족
- [ ] 보안 검증 완료
- [ ] 문서 최신화 확인

---

**테스트 완료일**: _______________
**테스트 담당자**: _______________

