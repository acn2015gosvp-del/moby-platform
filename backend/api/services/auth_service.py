"""
인증 서비스 모듈

비밀번호 해싱, JWT 토큰 생성 및 검증을 제공합니다.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt

from .schemas.models.core.config import settings

logger = logging.getLogger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    평문 비밀번호와 해시된 비밀번호를 비교합니다.
    
    Args:
        plain_password: 평문 비밀번호
        hashed_password: 해시된 비밀번호
        
    Returns:
        비밀번호가 일치하면 True, 아니면 False
    """
    try:
        # bcrypt를 직접 사용하여 검증
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        logger.warning(f"비밀번호 검증 중 오류: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    비밀번호를 해시합니다.
    
    Args:
        password: 평문 비밀번호 (최대 72바이트)
        
    Returns:
        해시된 비밀번호
    """
    # bcrypt를 직접 사용하여 해싱
    password_bytes = password.encode('utf-8')
    # bcrypt는 최대 72바이트까지만 지원
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT 액세스 토큰을 생성합니다.
    
    Args:
        data: 토큰에 포함할 데이터 (예: {"sub": "user@example.com"})
        expires_delta: 토큰 만료 시간 (기본값: 설정 파일의 값 사용)
        
    Returns:
        JWT 토큰 문자열
        
    Raises:
        ValueError: SECRET_KEY가 설정되지 않았거나 유효하지 않은 경우
        Exception: JWT 토큰 생성 중 기타 오류 발생 시
    """
    # SECRET_KEY 검증
    if not settings.SECRET_KEY or not settings.SECRET_KEY.strip():
        error_msg = "SECRET_KEY가 설정되지 않았습니다. .env 파일에 SECRET_KEY를 설정하세요."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # SECRET_KEY 길이 검증 (최소 32자 권장)
    if len(settings.SECRET_KEY) < 16:
        logger.warning(f"SECRET_KEY가 너무 짧습니다 ({len(settings.SECRET_KEY)}자). 보안을 위해 최소 32자 이상을 권장합니다.")
    
    # ALGORITHM 검증
    if not settings.ALGORITHM or not settings.ALGORITHM.strip():
        error_msg = "ALGORITHM이 설정되지 않았습니다."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # ACCESS_TOKEN_EXPIRE_MINUTES 검증
    if not hasattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES') or settings.ACCESS_TOKEN_EXPIRE_MINUTES is None:
        expire_minutes = 30  # 기본값
        logger.warning(f"ACCESS_TOKEN_EXPIRE_MINUTES가 설정되지 않아 기본값 {expire_minutes}분을 사용합니다.")
    else:
        expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        if expire_minutes <= 0:
            logger.warning(f"ACCESS_TOKEN_EXPIRE_MINUTES가 유효하지 않습니다 ({expire_minutes}). 기본값 30분을 사용합니다.")
            expire_minutes = 30
    
    try:
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
        
        to_encode.update({"exp": expire})
        
        # JWT 토큰 생성
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        logger.debug(f"JWT 토큰 생성 완료. expires_at={expire}")
        return encoded_jwt
        
    except JWTError as e:
        error_msg = f"JWT 토큰 생성 실패: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg) from e
    except Exception as e:
        error_msg = f"JWT 토큰 생성 중 예상치 못한 오류: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg) from e


def decode_access_token(token: str) -> Optional[dict]:
    """
    JWT 토큰을 디코딩하고 검증합니다.
    
    Args:
        token: JWT 토큰 문자열
        
    Returns:
        디코딩된 토큰 데이터 (dict), 검증 실패 시 None
        
    Raises:
        JWTError: 토큰이 유효하지 않은 경우
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT 토큰 검증 실패: {e}")
        return None

