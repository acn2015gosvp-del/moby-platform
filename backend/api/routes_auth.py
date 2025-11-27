"""
인증 관련 API 엔드포인트

회원가입, 로그인, 토큰 갱신 등의 인증 관련 API를 제공합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional, List

from backend.api.services.database import get_db
from backend.api.services.auth_service import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)
from backend.api.services.schemas.user_schema import (
    UserCreate,
    UserResponse,
    Token,
    UserLogin
)
from backend.api.models.user import User
from backend.api.core.responses import SuccessResponse, ErrorResponse
from backend.api.core.api_exceptions import BadRequestError, UnauthorizedError
from backend.api.core.permissions import require_permissions, require_role, get_user_permissions, get_current_user, oauth2_scheme
from backend.api.models.role import Role, Permission
from backend.api.services.schemas.models.core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/register",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="회원가입",
    description="""
    새로운 사용자를 등록합니다.
    
    **요구사항:**
    - 이메일: 유효한 이메일 형식, 중복 불가
    - 사용자명: 3-50자, 중복 불가
    - 비밀번호: 최소 8자, 영문자와 숫자 포함
    
    **응답:**
    - `201 Created`: 회원가입 성공
    - `400 Bad Request`: 잘못된 요청 데이터 또는 중복된 이메일/사용자명
    """,
)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> SuccessResponse[UserResponse]:
    """
    회원가입 엔드포인트
    
    Args:
        user_data: 회원가입 요청 데이터
        db: 데이터베이스 세션
        
    Returns:
        SuccessResponse[UserResponse]: 생성된 사용자 정보
        
    Raises:
        BadRequestError: 이메일 또는 사용자명이 이미 존재하는 경우
    """
    try:
        # 이메일 중복 확인
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            logger.warning(f"회원가입 실패: 이메일 중복 - {user_data.email}")
            raise BadRequestError(
                message="이미 등록된 이메일입니다.",
                field="email"
            )
        
        # 사용자명 중복 확인
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            logger.warning(f"회원가입 실패: 사용자명 중복 - {user_data.username}")
            raise BadRequestError(
                message="이미 사용 중인 사용자명입니다.",
                field="username"
            )
        
        # 비밀번호 해싱
        hashed_password = get_password_hash(user_data.password)
        
        # 사용자 생성 (기본 역할: USER)
        from backend.api.models.role import Role
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            is_active=True,
            role=Role.USER.value  # 기본 역할 설정
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"회원가입 성공: {user_data.email} (ID: {db_user.id})")
        
        return SuccessResponse(
            success=True,
            data=UserResponse(
                id=db_user.id,
                email=db_user.email,
                username=db_user.username,
                is_active=db_user.is_active,
                role=db_user.role,
                created_at=db_user.created_at
            ),
            message="회원가입이 완료되었습니다."
        )
        
    except BadRequestError:
        raise
    except Exception as e:
        logger.exception(f"회원가입 중 예상치 못한 오류: {e}")
        db.rollback()
        raise BadRequestError(
            message="회원가입 중 오류가 발생했습니다."
        )


@router.post(
    "/login",
    response_model=SuccessResponse[Token],
    summary="로그인",
    description="""
    사용자 로그인 및 JWT 토큰 발급
    
    **입력:**
    - 이메일: 등록된 이메일 주소
    - 비밀번호: 사용자 비밀번호
    
    **응답:**
    - `200 OK`: 로그인 성공, JWT 토큰 반환
    - `401 Unauthorized`: 이메일 또는 비밀번호가 잘못됨
    """,
)
async def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
) -> SuccessResponse[Token]:
    """
    로그인 엔드포인트
    
    Args:
        user_data: 로그인 요청 데이터
        db: 데이터베이스 세션
        
    Returns:
        SuccessResponse[Token]: JWT 토큰
        
    Raises:
        UnauthorizedError: 이메일 또는 비밀번호가 잘못된 경우
    """
    try:
        import time
        total_start = time.time()
        
        # 사용자 조회 (인덱스 사용)
        logger.debug(f"로그인 시도: {user_data.email}")
        query_start = time.time()
        user = db.query(User).filter(User.email == user_data.email).first()
        query_time = time.time() - query_start
        
        if query_time > 0.5:
            logger.warning(f"⚠️ 사용자 조회가 느립니다: {query_time:.3f}초")
        
        if not user:
            logger.warning(f"로그인 실패: 존재하지 않는 이메일 - {user_data.email}")
            raise UnauthorizedError(
                message="이메일 또는 비밀번호가 잘못되었습니다."
            )
        
        # 비밀번호 확인
        pwd_start = time.time()
        if not verify_password(user_data.password, user.hashed_password):
            pwd_time = time.time() - pwd_start
            logger.warning(f"로그인 실패: 비밀번호 불일치 - {user_data.email} (검증 시간: {pwd_time:.3f}초)")
            raise UnauthorizedError(
                message="이메일 또는 비밀번호가 잘못되었습니다."
            )
        pwd_time = time.time() - pwd_start
        if pwd_time > 0.3:
            logger.warning(f"⚠️ 비밀번호 검증이 느립니다: {pwd_time:.3f}초")
        
        # 계정 활성화 확인
        if not user.is_active:
            logger.warning(f"로그인 실패: 비활성화된 계정 - {user_data.email}")
            raise UnauthorizedError(
                message="비활성화된 계정입니다."
            )
        
        # JWT 토큰 생성 (에러 처리 강화)
        token_start = time.time()
        try:
            access_token = create_access_token(data={"sub": user.email})
        except ValueError as ve:
            # SECRET_KEY 또는 JWT 생성 관련 오류
            logger.error(f"JWT 토큰 생성 실패: {ve}", exc_info=True)
            raise UnauthorizedError(
                message="인증 토큰 생성 중 오류가 발생했습니다. 관리자에게 문의하세요."
            )
        except Exception as token_error:
            # 기타 JWT 생성 오류
            logger.error(f"JWT 토큰 생성 중 예상치 못한 오류: {token_error}", exc_info=True)
            raise UnauthorizedError(
                message="인증 토큰 생성 중 오류가 발생했습니다. 관리자에게 문의하세요."
            )
        token_time = time.time() - token_start
        
        total_time = time.time() - total_start
        logger.info(
            f"로그인 성공: {user.email} (ID: {user.id}) | "
            f"총 시간: {total_time:.3f}초 (쿼리: {query_time:.3f}초, 비밀번호: {pwd_time:.3f}초, 토큰: {token_time:.3f}초)"
        )
        
        # 성능 경고
        if total_time > 1.0:
            logger.warning(f"⚠️ 로그인 응답이 느립니다: {total_time:.3f}초")
        
        return SuccessResponse(
            success=True,
            data=Token(access_token=access_token),
            message="로그인에 성공했습니다."
        )
        
    except UnauthorizedError:
        # UnauthorizedError는 그대로 전달 (401 상태 코드)
        logger.debug(f"로그인 실패 (UnauthorizedError): {user_data.email}")
        raise
    except HTTPException:
        # HTTPException도 그대로 전달 (FastAPI가 처리)
        raise
    except Exception as e:
        # 상세한 에러 정보 로깅
        import traceback
        error_traceback = traceback.format_exc()
        logger.exception(f"❌ 로그인 처리 중 예상치 못한 오류 발생: {e}")
        logger.error(f"로그인 실패 상세 정보:\n{error_traceback}")
        
        # SECRET_KEY 관련 에러인지 확인
        if "SECRET_KEY" in str(e) or "secret" in str(e).lower():
            logger.error("SECRET_KEY가 설정되지 않았거나 잘못되었습니다.")
            raise UnauthorizedError(
                message="서버 설정 오류입니다. 관리자에게 문의하세요."
            )
        
        # JWT 토큰 생성 관련 에러인지 확인
        if "jwt" in str(e).lower() or "token" in str(e).lower():
            logger.error("JWT 토큰 생성 중 오류가 발생했습니다.")
            raise UnauthorizedError(
                message="인증 토큰 생성 중 오류가 발생했습니다. 관리자에게 문의하세요."
            )
        
        # 데이터베이스 관련 에러인지 확인
        if "database" in str(e).lower() or "db" in str(e).lower() or "sql" in str(e).lower():
            logger.error("데이터베이스 연결 오류가 발생했습니다.")
            raise UnauthorizedError(
                message="데이터베이스 연결 오류입니다. 관리자에게 문의하세요."
            )
        
        # 기타 예상치 못한 에러는 500 에러로 변환하지 않고 401로 반환
        # 이렇게 하면 프론트엔드에서 일관된 에러 처리가 가능함
        raise UnauthorizedError(
            message="로그인 중 오류가 발생했습니다. 관리자에게 문의하세요."
        )


@router.get(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="현재 사용자 정보 조회",
    description="""
    현재 로그인한 사용자의 정보를 조회합니다.
    
    **인증 필요**: JWT 토큰이 필요합니다.
    
    **응답:**
    - `200 OK`: 사용자 정보 반환
    - `401 Unauthorized`: 토큰이 유효하지 않음
    """,
)
async def get_current_user_endpoint(
    current_user: User = Depends(get_current_user)
) -> SuccessResponse[UserResponse]:
    """
    현재 로그인한 사용자 정보를 반환합니다.
    
    Args:
        current_user: 현재 로그인한 사용자 (의존성 주입)
        
    Returns:
        SuccessResponse[UserResponse]: 사용자 정보
        
    Raises:
        UnauthorizedError: 토큰이 유효하지 않거나 사용자를 찾을 수 없는 경우
    """
    try:
        return SuccessResponse(
            success=True,
            data=UserResponse(
                id=current_user.id,
                email=current_user.email,
                username=current_user.username,
                is_active=current_user.is_active,
                role=current_user.role,
                created_at=current_user.created_at
            ),
            message="사용자 정보 조회 성공"
        )
        
    except Exception as e:
        logger.exception(f"사용자 정보 조회 중 오류: {e}")
        raise UnauthorizedError(message="사용자 정보를 조회할 수 없습니다.")


@router.post(
    "/refresh",
    response_model=SuccessResponse[Token],
    summary="토큰 갱신",
    description="""
    JWT 토큰을 갱신합니다.
    
    **인증 필요**: 유효한 JWT 토큰이 필요합니다.
    
    **응답:**
    - `200 OK`: 새로운 토큰 반환
    - `401 Unauthorized`: 토큰이 유효하지 않음
    """,
)
async def refresh_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> SuccessResponse[Token]:
    """
    토큰 갱신 엔드포인트
    
    Args:
        token: 현재 JWT 토큰 (의존성 주입)
        db: 데이터베이스 세션
        
    Returns:
        SuccessResponse[Token]: 새로운 JWT 토큰
        
    Raises:
        UnauthorizedError: 토큰이 유효하지 않거나 사용자를 찾을 수 없는 경우
    """
    try:
        # 토큰 디코딩
        payload = decode_access_token(token)
        if payload is None:
            raise UnauthorizedError(message="유효하지 않은 토큰입니다.")
        
        email: str = payload.get("sub")
        if email is None:
            raise UnauthorizedError(message="토큰에 이메일 정보가 없습니다.")
        
        # 사용자 조회 및 활성화 확인
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise UnauthorizedError(message="사용자를 찾을 수 없습니다.")
        
        if not user.is_active:
            raise UnauthorizedError(message="비활성화된 계정입니다.")
        
        # 새로운 토큰 생성
        new_access_token = create_access_token(data={"sub": user.email})
        
        logger.info(f"토큰 갱신 성공: {user.email} (ID: {user.id})")
        
        return SuccessResponse(
            success=True,
            data=Token(access_token=new_access_token),
            message="토큰이 갱신되었습니다."
        )
        
    except UnauthorizedError:
        raise
    except Exception as e:
        logger.exception(f"토큰 갱신 중 오류: {e}")
        raise UnauthorizedError(message="토큰을 갱신할 수 없습니다.")


@router.get(
    "/permissions",
    response_model=SuccessResponse[dict],
    summary="현재 사용자 권한 조회",
    description="""
    현재 로그인한 사용자의 권한 목록을 조회합니다.
    
    **인증 필요**: JWT 토큰이 필요합니다.
    """,
)
async def get_my_permissions(
    current_user: User = Depends(get_current_user)
) -> SuccessResponse[dict]:
    """
    현재 사용자의 권한 목록을 반환합니다.
    
    Args:
        current_user: 현재 로그인한 사용자
        
    Returns:
        SuccessResponse[dict]: 권한 정보
    """
    permissions = get_user_permissions(current_user)
    return SuccessResponse(
        success=True,
        data={
            "role": current_user.role,
            "permissions": [p.value for p in permissions]
        },
        message="권한 정보 조회 성공"
    )


@router.get(
    "/users",
    response_model=SuccessResponse[List[UserResponse]],
    summary="사용자 목록 조회 (관리자 전용)",
    description="""
    모든 사용자 목록을 조회합니다. 관리자만 접근 가능합니다.
    
    **인증 필요**: JWT 토큰 및 관리자 권한 필요
    """,
)
async def get_users(
    current_user: User = Depends(require_permissions(Permission.USER_READ)),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> SuccessResponse[List[UserResponse]]:
    """
    사용자 목록을 반환합니다. (관리자 전용)
    
    Args:
        current_user: 현재 로그인한 사용자 (권한 체크됨)
        db: 데이터베이스 세션
        skip: 건너뛸 레코드 수
        limit: 반환할 최대 레코드 수
        
    Returns:
        SuccessResponse[List[UserResponse]]: 사용자 목록
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return SuccessResponse(
        success=True,
        data=[
            UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                is_active=user.is_active,
                role=user.role,
                created_at=user.created_at
            )
            for user in users
        ],
        message="사용자 목록 조회 성공"
    )


@router.patch(
    "/users/{user_id}/role",
    response_model=SuccessResponse[UserResponse],
    summary="사용자 역할 변경 (관리자 전용)",
    description="""
    사용자의 역할을 변경합니다. 관리자만 접근 가능합니다.
    
    **인증 필요**: JWT 토큰 및 관리자 권한 필요
    """,
)
async def update_user_role(
    user_id: int,
    new_role: str,
    current_user: User = Depends(require_permissions(Permission.USER_WRITE)),
    db: Session = Depends(get_db)
) -> SuccessResponse[UserResponse]:
    """
    사용자의 역할을 변경합니다. (관리자 전용)
    
    Args:
        user_id: 변경할 사용자 ID
        new_role: 새로운 역할 (admin, user, viewer)
        current_user: 현재 로그인한 사용자 (권한 체크됨)
        db: 데이터베이스 세션
        
    Returns:
        SuccessResponse[UserResponse]: 업데이트된 사용자 정보
        
    Raises:
        BadRequestError: 잘못된 역할 또는 사용자를 찾을 수 없는 경우
    """
    try:
        # 역할 유효성 검증
        try:
            role = Role(new_role)
        except ValueError:
            raise BadRequestError(
                message=f"Invalid role: {new_role}. Allowed values: {[r.value for r in Role]}",
                field="role"
            )
        
        # 사용자 조회
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise BadRequestError(
                message=f"User with ID {user_id} not found",
                field="user_id"
            )
        
        # 역할 변경
        user.role = role.value
        db.commit()
        db.refresh(user)
        
        logger.info(
            f"User role updated: {user.email} (ID: {user.id}) "
            f"by {current_user.email} (ID: {current_user.id}) "
            f"to {role.value}"
        )
        
        return SuccessResponse(
            success=True,
            data=UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                is_active=user.is_active,
                role=user.role,
                created_at=user.created_at
            ),
            message="사용자 역할이 변경되었습니다."
        )
        
    except BadRequestError:
        raise
    except Exception as e:
        logger.exception(f"사용자 역할 변경 중 오류: {e}")
        db.rollback()
        raise BadRequestError(message="사용자 역할 변경 중 오류가 발생했습니다.")

