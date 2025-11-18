# 🚀 빠른 시작 가이드

MOBY Platform을 빠르게 실행하는 방법을 안내합니다.

---

## ⚡ 빠른 실행 (이미 설치된 경우)

### 1. 백엔드 서버 실행 (터미널 1)

```powershell
# 가상 환경 활성화 (필요한 경우)
venv\Scripts\activate

# 환경 변수 설정 (인코딩 오류 방지)
$env:PYTHONIOENCODING="utf-8"

# 프로젝트 루트에서 실행
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 프론트엔드 서버 실행 (터미널 2)

```powershell
cd frontend
npm run dev
```

---

## 📋 전체 실행 순서

### 사전 준비

1. **가상 환경 활성화**
   ```powershell
   venv\Scripts\activate
   ```

2. **환경 변수 설정** (인코딩 오류 방지)
   ```powershell
   $env:PYTHONIOENCODING="utf-8"
   ```

### 백엔드 서버 실행

**터미널 1에서:**

```powershell
# 프로젝트 루트 디렉토리에서
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**정상 실행 확인:**
- 브라우저에서 http://localhost:8000/docs 접속
- API 문서(Swagger UI)가 표시되면 성공

### 프론트엔드 서버 실행

**터미널 2에서:**

```powershell
cd frontend
npm run dev
```

**정상 실행 확인:**
- 브라우저에서 http://localhost:5173 접속
- 웹 페이지가 표시되면 성공

---

## 🔍 실행 확인

### 백엔드 확인

```powershell
# 헬스 체크
curl http://localhost:8000/health

# 또는 브라우저에서
# http://localhost:8000/health
# http://localhost:8000/docs
```

### 프론트엔드 확인

```powershell
# 브라우저에서
# http://localhost:5173
```

---

## 🛑 서버 종료

각 터미널에서 `Ctrl + C`를 눌러 서버를 종료합니다.

---

## ⚠️ 주의사항

1. **프로젝트 루트에서 실행**: 백엔드는 반드시 프로젝트 루트(`moby-platform/`)에서 실행해야 합니다.

2. **두 개의 터미널 필요**: 백엔드와 프론트엔드는 별도의 터미널에서 실행해야 합니다.

3. **가상 환경 활성화**: 백엔드 실행 전에 가상 환경을 활성화해야 합니다.

4. **인코딩 설정**: Windows에서 인코딩 오류가 발생하면 `$env:PYTHONIOENCODING="utf-8"` 설정을 추가하세요.

---

## 📚 추가 참고 자료

- [전체 실행 순서 가이드](EXECUTION_ORDER.md)
- [문제 해결 가이드](TROUBLESHOOTING.md)
- [API 문서](../README.md)
