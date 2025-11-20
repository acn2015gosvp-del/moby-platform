# 역할(Role) 기반 API 분석 문서

## 1. 로그인 후 Role 저장 위치

### 1.1 localStorage
- **키**: `user`
- **형식**: JSON 문자열
- **구조**:
```typescript
{
  id: number,
  email: string,
  username: string,
  is_active: boolean,
  role: string,  // "admin", "user", "viewer"
  created_at: string
}
```
- **저장 위치**: `frontend/src/services/auth/authService.ts`
  - `saveUser(user: User)` 함수로 저장
  - `getStoredUser()` 함수로 조회

### 1.2 React Context (AuthContext)
- **위치**: `frontend/src/context/AuthContext.tsx`
- **상태**: `user: User | null`
- **접근 방법**: `useAuth()` 훅 사용
```typescript
const { user } = useAuth()
// user.role로 접근 가능
```

### 1.3 sessionStorage
- **사용 안 함**: 현재 코드에서 sessionStorage는 사용하지 않음

### 1.4 Recoil/Zustand Store
- **사용 안 함**: 현재 코드에서 Recoil이나 Zustand 같은 상태 관리 라이브러리는 사용하지 않음
- **대신**: React Context API (`AuthContext`) 사용

---

## 2. 관리자 로그인 시 호출되는 API

### 2.1 보고서 생성 API
- **URL**: `/api/reports/generate` (프론트엔드) → `/reports/generate` (백엔드)
- **메서드**: `POST`
- **권한 체크**: 
  - `require_permissions(Permission.ALERT_READ, Permission.SENSOR_READ)`
  - 관리자는 모든 권한을 가지고 있으므로 접근 가능
- **위치**: `backend/api/routes_reports.py:73`

### 2.2 센서 API
- **센서 데이터 수신**: `/api/sensors/data` (프론트엔드) → `/sensors/data` (백엔드)
  - **메서드**: `POST`
  - **권한 체크**: 없음 (공개 엔드포인트)
  - **위치**: `backend/api/routes_sensors.py:119`

- **센서 상태 조회**: `/api/sensors/status` (프론트엔드) → `/sensors/status` (백엔드)
  - **메서드**: `GET`
  - **권한 체크**: 없음 (공개 엔드포인트)
  - **위치**: `backend/api/routes_sensors.py:192`

### 2.3 관리자 전용 API
- **현재 구현 상태**: 별도의 `/admin/*` 엔드포인트는 구현되어 있지 않음
- **권한 체크 방식**: 각 엔드포인트에서 `require_permissions()` 또는 `require_role()` 사용

---

## 3. 일반 사용자 로그인 시 호출되는 API

### 3.1 보고서 생성 API
- **URL**: `/api/reports/generate` (관리자와 동일)
- **메서드**: `POST`
- **권한 체크**: 
  - `require_permissions(Permission.ALERT_READ, Permission.SENSOR_READ)`
  - 일반 사용자(`Role.USER`)도 `ALERT_READ`, `SENSOR_READ` 권한을 가지고 있으므로 접근 가능

### 3.2 센서 API
- **센서 데이터 수신**: `/api/sensors/data` (관리자와 동일)
- **센서 상태 조회**: `/api/sensors/status` (관리자와 동일)
- **권한 체크**: 없음 (공개 엔드포인트)

---

## 4. 차이점 분석

### 4.1 URL 차이
- **차이 없음**: 관리자와 일반 사용자가 동일한 URL을 사용
- **예시**:
  - 보고서 생성: 모두 `/api/reports/generate` 사용
  - 센서 조회: 모두 `/api/sensors/status` 사용

### 4.2 Body 파라미터 차이
- **차이 없음**: 요청 body는 역할과 무관하게 동일

**보고서 생성 요청 예시**:
```json
{
  "period_start": "2025-01-01 00:00:00",
  "period_end": "2025-01-07 23:59:59",
  "equipment": "설비명",
  "sensor_ids": ["sensor_001"],
  "include_mlp_anomalies": true,
  "include_if_anomalies": true
}
```

### 4.3 Authorization 헤더 차이
- **형식**: 동일 (`Bearer {token}`)
- **차이점**: 
  - 토큰에 포함된 사용자 정보(이메일)로 역할을 식별
  - 백엔드에서 토큰을 디코딩하여 사용자 조회 후 `user.role` 확인
  - 권한 체크는 백엔드에서 수행

**Authorization 헤더 예시**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 4.4 백엔드 권한 체크 방식

#### 역할별 권한 매핑 (`backend/api/models/role.py`)
```python
ROLE_PERMISSIONS = {
    Role.ADMIN: {
        Permission.ALERT_READ,
        Permission.ALERT_WRITE,
        Permission.ALERT_DELETE,
        Permission.SENSOR_READ,
        Permission.SENSOR_WRITE,
        Permission.GRAFANA_READ,
        Permission.GRAFANA_WRITE,
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.USER_DELETE,
        Permission.SYSTEM_ADMIN,
    },
    Role.USER: {
        Permission.ALERT_READ,
        Permission.ALERT_WRITE,
        Permission.SENSOR_READ,
        Permission.SENSOR_WRITE,
        Permission.GRAFANA_READ,
    },
    Role.VIEWER: {
        Permission.ALERT_READ,
        Permission.SENSOR_READ,
        Permission.GRAFANA_READ,
    },
}
```

#### 권한 체크 예시 (`backend/api/routes_reports.py`)
```python
@router.post("/generate")
async def generate_report(
    request: ReportRequest,
    current_user = Depends(get_current_user),  # 토큰에서 사용자 추출
    _permissions = Depends(require_permissions(
        Permission.ALERT_READ, 
        Permission.SENSOR_READ
    )),  # 권한 체크
    db: Session = Depends(get_db)
):
    # ...
```

---

## 5. 프론트엔드에서 Role 사용 현황

### 5.1 현재 상태
- **Role 기반 UI 분기**: 현재 프론트엔드 코드에서 `user.role`을 사용한 UI 분기는 없음
- **모든 사용자 동일 API 호출**: 관리자와 일반 사용자가 동일한 API를 호출
- **권한 체크**: 백엔드에서만 수행

### 5.2 Role 접근 방법
```typescript
// AuthContext 사용
const { user } = useAuth()
if (user?.role === 'admin') {
  // 관리자 전용 UI 표시
}

// localStorage 직접 접근
const storedUser = JSON.parse(localStorage.getItem('user') || '{}')
const role = storedUser.role
```

---

## 6. 요약

| 항목 | 관리자 | 일반 사용자 | 차이점 |
|------|--------|-------------|--------|
| **API URL** | `/api/reports/generate` | `/api/reports/generate` | 동일 |
| **Authorization 헤더** | `Bearer {token}` | `Bearer {token}` | 동일 형식, 다른 토큰 |
| **Body 파라미터** | 동일 | 동일 | 차이 없음 |
| **권한 체크** | 백엔드에서 `require_permissions()` | 백엔드에서 `require_permissions()` | 백엔드에서 역할별 권한 확인 |
| **Role 저장 위치** | `localStorage.user.role` + `AuthContext.user.role` | 동일 | 동일 |

### 핵심 포인트
1. **URL은 동일**: 관리자와 일반 사용자가 같은 엔드포인트 사용
2. **권한은 백엔드에서 체크**: 프론트엔드가 아닌 백엔드에서 역할별 권한 확인
3. **Role은 localStorage와 Context에 저장**: `localStorage.user` (JSON)와 `AuthContext.user`에 저장
4. **별도 Admin API 없음**: `/admin/*` 엔드포인트는 구현되어 있지 않음

---

## 7. 참고 파일

- `frontend/src/types/auth.ts` - User 타입 정의
- `frontend/src/context/AuthContext.tsx` - 인증 컨텍스트
- `frontend/src/services/auth/authService.ts` - 인증 서비스
- `frontend/src/services/reports/reportService.ts` - 보고서 API 호출
- `frontend/src/services/sensors/sensorService.ts` - 센서 API 호출
- `backend/api/routes_reports.py` - 보고서 생성 엔드포인트
- `backend/api/routes_sensors.py` - 센서 엔드포인트
- `backend/api/core/permissions.py` - 권한 체크 유틸리티
- `backend/api/models/role.py` - 역할 및 권한 정의

