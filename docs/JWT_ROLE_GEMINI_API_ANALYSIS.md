# JWT Role 및 Gemini API 분석 문서

## 1. /login 엔드포인트 - JWT Payload에 Role 포함 여부

### 현재 상태: ❌ Role 미포함

**위치**: `backend/api/routes_auth.py:204`

```python
# JWT 토큰 생성
access_token = create_access_token(data={"sub": user.email})
```

**현재 JWT Payload 구조**:
```json
{
  "sub": "user@example.com",  // 이메일만 포함
  "exp": 1234567890           // 만료 시간
}
```

**문제점**:
- Role 정보가 JWT 토큰에 포함되지 않음
- 토큰 디코딩만으로는 사용자 역할을 알 수 없음
- 매번 데이터베이스에서 사용자 정보를 조회해야 함

**권장 수정 사항**:
```python
# 수정 전
access_token = create_access_token(data={"sub": user.email})

# 수정 후
access_token = create_access_token(data={
    "sub": user.email,
    "role": user.role  # Role 추가
})
```

**응답 형식**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  },
  "message": "로그인에 성공했습니다."
}
```

**참고**: 현재는 `role`을 응답에 포함하지 않음. `/me` 엔드포인트를 통해 조회해야 함.

---

## 2. /me 엔드포인트 - Role 반환 여부

### 현재 상태: ✅ Role 반환함

**위치**: `backend/api/routes_auth.py:232-277`

**엔드포인트**: `GET /auth/me`

**응답 형식**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "is_active": true,
    "role": "admin",  // ✅ Role 포함
    "created_at": "2025-01-01T00:00:00"
  },
  "message": "사용자 정보 조회 성공"
}
```

**코드**:
```python
@router.get("/me")
async def get_current_user_endpoint(
    current_user: User = Depends(get_current_user)
) -> SuccessResponse[UserResponse]:
    return SuccessResponse(
        success=True,
        data=UserResponse(
            id=current_user.id,
            email=current_user.email,
            username=current_user.username,
            is_active=current_user.is_active,
            role=current_user.role,  # ✅ Role 반환
            created_at=current_user.created_at
        ),
        message="사용자 정보 조회 성공"
    )
```

**프론트엔드 사용**:
- `frontend/src/services/auth/authService.ts:40-44`
- 로그인 후 `/auth/me` 호출하여 사용자 정보(role 포함) 조회
- `localStorage`에 저장: `localStorage.setItem('user', JSON.stringify(user))`

---

## 3. 관리자 전용 라우트 확인

### 현재 상태: ❌ 별도 Admin 라우트 없음

**확인 결과**:
- `backend/api/core/permissions.py`에 예시 코드만 있음 (실제 구현 없음)
- 별도의 `/admin/*` 라우터는 구현되어 있지 않음
- 모든 엔드포인트는 권한 체크(`require_permissions()`)로 보호됨

**예시 코드 (실제 구현 없음)**:
```python
# backend/api/core/permissions.py:88 (예시 주석)
@router.get("/admin/users")
async def get_users(
    current_user: User = Depends(require_permissions(Permission.USER_READ))
):
    ...
```

**현재 권한 체크 방식**:
- 각 엔드포인트에서 `require_permissions()` 또는 `require_role()` 사용
- 예: `/reports/generate`는 `Permission.ALERT_READ`, `Permission.SENSOR_READ` 필요

**권한별 접근 가능한 엔드포인트**:

| 엔드포인트 | ADMIN | USER | VIEWER |
|-----------|-------|------|--------|
| `/reports/generate` | ✅ | ✅ | ❌ |
| `/sensors/data` | ✅ | ✅ | ❌ |
| `/sensors/status` | ✅ | ✅ | ✅ |
| `/alerts/*` | ✅ | ✅ (읽기/쓰기) | ✅ (읽기만) |

---

## 4. 보고서 생성 관련 엔드포인트

### 현재 상태: 단일 엔드포인트만 존재

**엔드포인트**: `POST /reports/generate`

**위치**: `backend/api/routes_reports.py:43-207`

**URL 차이**:
- ❌ `/api/reports/generate` (일반 유저용) - **없음**
- ❌ `/api/admin/reports/generate` (관리자용) - **없음**
- ✅ `/reports/generate` (모든 인증된 사용자용) - **단일 엔드포인트**

**권한 체크**:
```python
@router.post("/generate")
async def generate_report(
    request: ReportRequest,
    current_user = Depends(get_current_user),
    _permissions = Depends(require_permissions(
        Permission.ALERT_READ, 
        Permission.SENSOR_READ
    )),
    db: Session = Depends(get_db)
):
    # ...
```

**접근 가능한 역할**:
- ✅ `ADMIN`: 모든 권한 보유 → 접근 가능
- ✅ `USER`: `ALERT_READ`, `SENSOR_READ` 권한 보유 → 접근 가능
- ❌ `VIEWER`: `ALERT_READ`만 보유, `SENSOR_READ` 없음 → 접근 불가

**요청 Body** (역할과 무관하게 동일):
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

---

## 5. Gemini 호출 로직 위치

### 현재 상태: ✅ 단일 엔드포인트에 Gemini 호출 포함

**Gemini 호출 위치**:
1. **엔드포인트**: `POST /reports/generate`
2. **서비스 클래스**: `backend/api/services/report_generator.py`
3. **호출 메서드**: `MOBYReportGenerator.generate_report()`

**호출 흐름**:
```
POST /reports/generate
  ↓
routes_reports.py:generate_report()
  ↓
_collect_report_data()  # 데이터 수집
  ↓
get_report_generator()  # MOBYReportGenerator 인스턴스 가져오기
  ↓
generator.generate_report(report_data)  # Gemini API 호출
  ↓
report_generator.py:MOBYReportGenerator.generate_report()
  ↓
self.model.generate_content(prompt)  # 실제 Gemini API 호출
```

**Gemini 호출 코드** (`backend/api/services/report_generator.py:300-350`):
```python
def generate_report(self, data: Dict[str, Any]) -> str:
    """
    보고서를 생성합니다.
    
    Args:
        data: 보고서 생성에 필요한 데이터
        
    Returns:
        생성된 보고서 내용 (마크다운 형식)
    """
    # 프롬프트 생성
    prompt = self._build_prompt(data)
    
    # Gemini API 호출
    import time
    start_time = time.time()
    logger.info(f"Gemini API 호출 중... (모델: {self.model_name})")
    
    response = self.model.generate_content(prompt)
    
    elapsed_time = time.time() - start_time
    
    if not response.text:
        raise ValueError("Gemini API가 빈 응답을 반환했습니다.")
    
    logger.info(f"✅ 보고서 생성 완료 (소요 시간: {elapsed_time:.2f}초)")
    return response.text
```

**중요 사항**:
- ✅ **단일 엔드포인트**: `/reports/generate` 하나만 존재
- ✅ **Gemini 호출 포함**: 모든 보고서 생성 요청에서 Gemini API 호출
- ❌ **Gemini 미호출 엔드포인트 없음**: 별도의 Gemini 미호출 엔드포인트는 없음

**에러 원인 가능성**:
1. **권한 부족**: `VIEWER` 역할은 `SENSOR_READ` 권한이 없어 접근 불가
2. **Gemini API 키 문제**: `GEMINI_API_KEY`가 설정되지 않았거나 유효하지 않음
3. **모델 선택 실패**: 사용 가능한 Gemini 모델을 찾지 못함
4. **API 할당량 초과**: Gemini API 할당량이 초과됨

---

## 6. 요약 및 권장 사항

### 현재 구현 상태

| 항목 | 상태 | 설명 |
|------|------|------|
| JWT에 Role 포함 | ❌ | 이메일만 포함, Role 미포함 |
| /me에서 Role 반환 | ✅ | Role 정상 반환 |
| 관리자 전용 라우트 | ❌ | 별도 `/admin/*` 라우트 없음 |
| 보고서 엔드포인트 | 단일 | `/reports/generate` 하나만 존재 |
| Gemini 호출 | ✅ | 모든 보고서 생성에서 호출 |

### 권장 수정 사항

#### 1. JWT Payload에 Role 추가
```python
# backend/api/routes_auth.py:204
access_token = create_access_token(data={
    "sub": user.email,
    "role": user.role  # 추가
})
```

#### 2. 로그인 응답에 Role 포함 (선택사항)
```python
# backend/api/routes_auth.py:217
return SuccessResponse(
    success=True,
    data=Token(
        access_token=access_token,
        role=user.role  # 추가 (Token 모델 수정 필요)
    ),
    message="로그인에 성공했습니다."
)
```

#### 3. 관리자 전용 엔드포인트 추가 (필요시)
```python
# backend/api/routes_admin.py (새 파일)
router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/reports/generate")
async def admin_generate_report(
    request: ReportRequest,
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db)
):
    # 관리자 전용 로직
    ...
```

---

## 7. 참고 파일

- `backend/api/routes_auth.py` - 로그인, /me 엔드포인트
- `backend/api/services/auth_service.py` - JWT 토큰 생성/검증
- `backend/api/routes_reports.py` - 보고서 생성 엔드포인트
- `backend/api/services/report_generator.py` - Gemini 호출 로직
- `backend/api/core/permissions.py` - 권한 체크 유틸리티
- `backend/api/models/role.py` - 역할 및 권한 정의

