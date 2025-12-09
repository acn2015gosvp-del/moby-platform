# 코드 안정성 및 개발 환경 가이드

## HMR (Hot Module Replacement) 문제 해결

### 문제 상황
- `routes_grafana.py` 외 다른 파일이 불필요하게 자주 변경되어 HMR이 불안정할 수 있음
- 자동 감지/재시작이 예상치 못한 동작을 유발할 수 있음

### 해결 방법

#### 1. 수동 재시작 (권장)

HMR 기능이 불안정할 경우, 자동 감지/재시작 대신 서버 프로세스를 수동으로 완전히 종료한 후 다시 실행하는 것이 더 안정적입니다.

**백엔드 서버 수동 재시작:**

```powershell
# 1. 현재 실행 중인 서버 종료
# 터미널에서 Ctrl+C를 눌러 서버 종료

# 2. 프로세스가 완전히 종료되었는지 확인
netstat -ano | findstr :8000

# 3. 여전히 실행 중인 프로세스가 있으면 강제 종료
# PID 확인 후
Stop-Process -Id <PID> -Force

# 4. 서버 재시작
cd backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**프론트엔드 개발 서버 수동 재시작:**

```powershell
# 1. 현재 실행 중인 서버 종료
# 터미널에서 Ctrl+C를 눌러 서버 종료

# 2. 프로세스가 완전히 종료되었는지 확인
netstat -ano | findstr :5173

# 3. 서버 재시작
cd frontend
npm run dev
```

#### 2. 자동 재시작 비활성화 (선택사항)

개발 중 자동 재시작이 불필요한 경우 `--reload` 옵션을 제거:

```powershell
# 백엔드 (--reload 제거)
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 프론트엔드는 Vite가 기본적으로 HMR을 사용하므로, 
# 필요시 vite.config.ts에서 설정 조정
```

## 코드 안정성 확인 체크리스트

### 1. 불필요한 파일 변경 확인

다음 파일들이 불필요하게 자주 변경되는지 확인:

- `backend/api/routes_grafana.py` - Grafana Webhook 핸들러 (정상적으로 변경됨)
- `backend/api/services/websocket_notifier.py` - WebSocket 전송 로직
- `backend/api/routes_websocket.py` - WebSocket 엔드포인트
- `frontend/src/hooks/useWebSocket.ts` - WebSocket 클라이언트 훅

**확인 방법:**

```powershell
# Git으로 최근 변경된 파일 확인
git status
git diff --name-only

# 특정 파일의 변경 이력 확인
git log --oneline --follow backend/api/routes_grafana.py
```

### 2. 파일 변경 빈도 모니터링

불필요하게 자주 변경되는 파일이 있는지 확인:

```powershell
# 최근 24시간 내 변경된 파일 확인
Get-ChildItem -Recurse -File | Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-24) } | Select-Object FullName, LastWriteTime | Sort-Object LastWriteTime -Descending
```

### 3. HMR 트리거 확인

프론트엔드 개발 서버 로그에서 불필요한 HMR 트리거 확인:

- 브라우저 콘솔에서 `[vite]` 로그 확인
- 예상치 못한 모듈 재로딩이 있는지 확인

## 안정적인 개발 워크플로우

### 권장 개발 순서

1. **코드 수정 전**
   - 현재 실행 중인 서버 상태 확인
   - 변경할 파일 목록 정리

2. **코드 수정**
   - 필요한 파일만 수정
   - 불필요한 포맷팅/정리 작업은 별도 커밋으로 분리

3. **수동 재시작 (필요 시)**
   - 코드 변경 후 서버를 수동으로 재시작
   - 변경 사항이 정상 반영되었는지 확인

4. **테스트**
   - 기능 테스트
   - 로그 확인
   - 에러 없이 정상 동작하는지 확인

### 자동 재시작 vs 수동 재시작

| 방식 | 장점 | 단점 | 권장 상황 |
|------|------|------|----------|
| 자동 재시작 (`--reload`) | 빠른 피드백, 편리함 | 불안정할 수 있음, 예상치 못한 재시작 | 작은 변경, 안정적인 환경 |
| 수동 재시작 | 안정적, 예측 가능 | 수동 작업 필요 | 큰 변경, 디버깅 중, 프로덕션 준비 |

## 문제 해결

### HMR이 계속 실패하는 경우

1. **캐시 정리**
   ```powershell
   # 프론트엔드 node_modules 및 캐시 정리
   cd frontend
   Remove-Item -Recurse -Force node_modules
   Remove-Item -Recurse -Force .vite
   npm install
   ```

2. **포트 충돌 확인**
   ```powershell
   # 8000 포트 사용 중인 프로세스 확인
   netstat -ano | findstr :8000
   
   # 5173 포트 사용 중인 프로세스 확인
   netstat -ano | findstr :5173
   ```

3. **완전 재시작**
   - 모든 서버 프로세스 종료
   - 터미널 재시작
   - 서버 순차적으로 재시작

## 참고

- FastAPI `--reload` 옵션은 파일 변경 감지 시 자동 재시작
- Vite HMR은 브라우저에서 모듈을 핫 리로드 (서버 재시작 없음)
- 두 방식 모두 불안정할 경우 수동 재시작이 더 안정적

