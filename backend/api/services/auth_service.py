"""
인증 서비스 모듈

비밀번호 해싱, JWT 토큰 생성 및 검증을 제공합니다.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from .schemas.models.core.config import settings

logger = logging.getLogger(__name__)

# 비밀번호 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    평문 비밀번호와 해시된 비밀번호를 비교합니다.
    
    Args:
        plain_password: 평문 비밀번호
        hashed_password: 해시된 비밀번호
        
    Returns:
        비밀번호가 일치하면 True, 아니면 False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    비밀번호를 해시합니다.
    
    Args:
        password: 평문 비밀번호
        
    Returns:
        해시된 비밀번호
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT 액세스 토큰을 생성합니다.
    
    Args:
        data: 토큰에 포함할 데이터 (예: {"sub": "user@example.com"})
        expires_delta: 토큰 만료 시간 (기본값: 설정 파일의 값 사용)
        
    Returns:
        JWT 토큰 문자열
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    logger.debug(f"JWT 토큰 생성 완료. expires_at={expire}")
    return encoded_jwt


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

