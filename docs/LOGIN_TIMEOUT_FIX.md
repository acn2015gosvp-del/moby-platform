# 로그인 타임아웃 문제 해결

## 문제 상황
- 로그인이 너무 오래 걸리고 들어가지지 않음
- 브라우저 콘솔에 "Network Error: XMLHttpRequest" 오류 발생
- `client.ts:95`에서 네트워크 오류 발생

## 해결 방법

### 1. 프론트엔드 API 클라이언트 타임아웃 증가
- **파일**: `frontend/src/services/api/client.ts`
- **변경**: `timeout: 30000` → `timeout: 60000` (30초 → 60초)

### 2. 로그인 API 호출 타임아웃 증가
- **파일**: `frontend/src/services/auth/authService.ts`
- **변경**: 로그인 요청에 `timeout: 60000` 추가

### 3. 네트워크 오류 처리 개선
- **파일**: `frontend/src/services/api/client.ts`
- **변경**: 타임아웃 및 네트워크 오류에 대한 더 자세한 로그 추가

## 확인 사항

### 백엔드 서버 상태
```bash
# 포트 8000에서 실행 중인 프로세스 확인
netstat -ano | findstr :8000

# 백엔드 서버가 정상적으로 응답하는지 확인
curl http://localhost:8000/health
```

### 프록시 설정
- **파일**: `frontend/vite.config.ts`
- **설정**: `/api` → `http://localhost:8000` 프록시 확인

### Rate Limiting
- 로그인 엔드포인트(`/auth/login`)는 Rate Limiting에서 제외됨
- **파일**: `backend/api/middleware/rate_limit.py:156`

## 추가 권장 사항

1. **백엔드 서버 재시작**: 포트 충돌이 있는 경우
2. **프론트엔드 서버 재시작**: 프록시 설정 적용을 위해
3. **브라우저 캐시 클리어**: 오래된 설정이 남아있을 수 있음

## 참고
- 이전 타임아웃: 30초
- 현재 타임아웃: 60초
- 로그인은 일반적으로 1초 이내 완료되어야 함

