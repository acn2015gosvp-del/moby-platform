# Grafana 대시보드 임베딩 설정 가이드

Grafana 서버가 변경되었을 때 iframe 임베딩을 새로 설정하는 방법입니다.

## 📋 필요한 설정 항목

### 1. Grafana 서버 설정 (필수)

#### 1.1 iframe 임베딩 허용

**설정 파일 방법:**
```ini
# grafana.ini 파일에 추가
[security]
allow_embedding = true
```

**환경 변수 방법 (Docker):**
```bash
GF_SECURITY_ALLOW_EMBEDDING=true
```

**Grafana UI 방법:**
1. Grafana에 로그인
2. Settings → Security → Allow embedding 체크
3. 저장 후 Grafana 재시작

#### 1.2 CORS 설정 (필요시)

```ini
[security]
allow_embedding = true
cors_allow_origin = *
```

또는 특정 도메인만 허용:
```ini
cors_allow_origin = http://localhost:5173,http://192.168.80.99:5173
```

### 2. Public Dashboard 설정 (권장)

Public Dashboard을 사용하면 인증 없이 임베딩할 수 있습니다.

#### 2.1 Public Dashboard 생성

1. Grafana에 로그인
2. 대시보드로 이동
3. 대시보드 설정 (⚙️) → **Sharing** → **Public Dashboard** 탭
4. **Generate public URL** 클릭
5. Public Dashboard URL 복사

**예시 URL 형식:**
```
http://192.168.80.99:3000/public-dashboards/1923537167584938bf0db89d9bca20bf
```

#### 2.2 Public Dashboard 설정 확인

- ✅ **Public Dashboard 활성화**: ON
- ✅ **Time range picker**: 필요시 활성화
- ✅ **Annotations**: 필요시 활성화

### 3. 프론트엔드 환경 변수 설정

`frontend/.env` 파일에 다음 변수를 설정합니다:

```env
# Grafana 서버 기본 URL
VITE_GRAFANA_URL=http://192.168.80.99:3001

# Grafana 대시보드 전체 URL (Public Dashboard URL 사용 권장)
VITE_GRAFANA_DASHBOARD_URL=http://192.168.80.99:3000/public-dashboards/1923537167584938bf0db89d9bca20bf

# Grafana API Key (선택사항, API 접근이 필요한 경우)
VITE_GRAFANA_API_KEY=your-api-key-here
```

**중요:** `VITE_GRAFANA_DASHBOARD_URL`이 설정되어 있으면 이 URL을 그대로 사용합니다. URL 생성 로직을 사용하지 않습니다.

### 4. 일반 대시보드 URL 형식 (Public Dashboard 미사용 시)

Public Dashboard을 사용하지 않는 경우, 다음 형식의 URL을 사용할 수 있습니다:

```
http://192.168.80.99:3001/d/{dashboard-uid}/view?orgId=1&refresh=30s&kiosk=tv
```

**필수 파라미터:**
- `orgId`: 조직 ID (기본값: 1)
- `refresh`: 자동 새로고침 간격 (예: 30s)
- `kiosk`: TV 모드 (tv, tv-side-menu 등)

**선택 파라미터:**
- `from`, `to`: 시간 범위
- `var-device_id`: 설비 ID 변수

## 🔧 설정 단계별 가이드

### Step 1: Grafana 서버 설정 확인

```bash
# Grafana 서버 접속 확인
curl http://192.168.80.99:3001/api/health

# 또는 브라우저에서 직접 접속
http://192.168.80.99:3001
```

### Step 2: iframe 임베딩 활성화

**방법 A: 설정 파일 수정**
```bash
# Grafana 설정 파일 위치 확인
# Linux: /etc/grafana/grafana.ini
# Docker: 볼륨 마운트된 설정 파일
# Windows: Grafana 설치 디렉토리/conf/grafana.ini

# [security] 섹션에 추가
[security]
allow_embedding = true
```

**방법 B: 환경 변수 (Docker)**
```bash
docker run -e GF_SECURITY_ALLOW_EMBEDDING=true grafana/grafana
```

**방법 C: Grafana UI**
1. Grafana 로그인
2. Settings → Security
3. "Allow embedding" 체크
4. 저장 후 재시작

### Step 3: Public Dashboard 생성 (권장)

1. Grafana에 로그인
2. 대시보드 선택
3. 대시보드 설정 (⚙️) → Sharing → Public Dashboard
4. "Generate public URL" 클릭
5. 생성된 URL 복사

### Step 4: 프론트엔드 환경 변수 설정

`frontend/.env` 파일 수정:
```env
VITE_GRAFANA_DASHBOARD_URL=http://192.168.80.99:3000/public-dashboards/1923537167584938bf0db89d9bca20bf
```

### Step 5: Vite 개발 서버 재시작

```bash
cd frontend
npm run dev
```

환경 변수 변경 후에는 반드시 서버를 재시작해야 합니다.

## ✅ 확인 방법

### 1. 브라우저에서 직접 URL 테스트

환경 변수에 설정한 URL을 브라우저 주소창에 직접 입력:
```
http://192.168.80.99:3000/public-dashboards/1923537167584938bf0db89d9bca20bf
```

대시보드가 정상적으로 표시되면 URL은 올바릅니다.

### 2. iframe 임베딩 테스트

다음 HTML을 파일로 저장하여 테스트:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Grafana Embed Test</title>
</head>
<body>
    <h1>Grafana Dashboard Embed Test</h1>
    <iframe 
        src="http://192.168.80.99:3000/public-dashboards/1923537167584938bf0db89d9bca20bf"
        width="100%" 
        height="800px"
        frameborder="0">
    </iframe>
</body>
</html>
```

브라우저에서 이 HTML 파일을 열어 대시보드가 표시되는지 확인합니다.

### 3. 모니터링 페이지에서 확인

1. 프론트엔드 애플리케이션 실행
2. 설비 모니터링 페이지 접속
3. 대시보드가 정상적으로 로드되는지 확인

## 🚨 문제 해결

### 문제 1: "X-Frame-Options" 에러

**증상:**
```
Refused to display 'http://...' in a frame because it set 'X-Frame-Options' to 'deny'.
```

**해결:**
- Grafana 설정에서 `allow_embedding = true` 확인
- Grafana 서버 재시작

### 문제 2: CORS 에러

**증상:**
```
Access to fetch at 'http://...' from origin 'http://localhost:5173' has been blocked by CORS policy
```

**해결:**
```ini
[security]
cors_allow_origin = http://localhost:5173,http://192.168.80.99:5173
```

### 문제 3: 인증 필요 에러

**증상:**
대시보드가 로그인 페이지로 리다이렉트됨

**해결:**
- Public Dashboard 사용 (권장)
- 또는 Grafana API Key를 사용한 인증 구현

### 문제 4: 대시보드가 표시되지 않음

**확인 사항:**
1. ✅ Grafana 서버가 실행 중인지 확인
2. ✅ URL이 올바른지 확인 (브라우저에서 직접 접속 테스트)
3. ✅ `allow_embedding = true` 설정 확인
4. ✅ Public Dashboard가 활성화되어 있는지 확인
5. ✅ 환경 변수가 올바르게 설정되었는지 확인
6. ✅ Vite 개발 서버 재시작

## 📝 체크리스트

새로운 Grafana 서버로 임베딩 설정 시:

- [ ] Grafana 서버 접속 확인
- [ ] `allow_embedding = true` 설정
- [ ] Grafana 서버 재시작
- [ ] Public Dashboard 생성 (또는 일반 대시보드 URL 확인)
- [ ] `frontend/.env`에 `VITE_GRAFANA_DASHBOARD_URL` 설정
- [ ] Vite 개발 서버 재시작
- [ ] 브라우저에서 직접 URL 테스트
- [ ] 모니터링 페이지에서 대시보드 로드 확인

## 🔗 참고 자료

- [Grafana 공식 문서 - Embedding](https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-authentication/allow-embedding/)
- [Grafana Public Dashboards](https://grafana.com/docs/grafana/latest/dashboards/dashboard-public/)
- [Grafana 설정 파일 참조](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/)

