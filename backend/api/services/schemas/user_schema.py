"""
사용자 관련 스키마 모듈

회원가입, 로그인, 사용자 정보 응답을 위한 Pydantic 모델을 정의합니다.
"""

import re
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from .models.core.config import settings


def validate_email(email: str) -> str:
    """
    이메일 주소를 검증합니다.
    개발 환경에서는 .local 도메인을 허용합니다.
    """
    # 기본 이메일 형식 검증 (프로덕션)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # 개발/테스트 환경에서는 .local 도메인도 허용
    if settings.is_development() or settings.is_testing():
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+(\.[a-zA-Z]{2,}|\.local)$'
    
    if not re.match(email_pattern, email):
        raise ValueError("유효하지 않은 이메일 주소 형식입니다.")
    
    return email


class UserBase(BaseModel):
    """사용자 기본 정보"""
    email: str = Field(..., description="이메일 주소")
    username: str = Field(..., min_length=3, max_length=50)
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """이메일 주소 검증"""
        return validate_email(v)


class UserCreate(UserBase):
    """회원가입 요청 스키마"""
    password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """비밀번호 유효성 검증"""
        if len(v) < 8:
            raise ValueError("비밀번호는 최소 8자 이상이어야 합니다.")
        if not any(c.isdigit() for c in v):
            raise ValueError("비밀번호는 최소 하나의 숫자를 포함해야 합니다.")
        if not any(c.isalpha() for c in v):
            raise ValueError("비밀번호는 최소 하나의 영문자를 포함해야 합니다.")
        return v


class UserLogin(BaseModel):
    """로그인 요청 스키마"""
    email: str = Field(..., description="이메일 주소")
    password: str
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """이메일 주소 검증"""
        return validate_email(v)


class UserResponse(UserBase):
    """사용자 정보 응답 스키마"""
    id: int
    is_active: bool
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT 토큰 응답 스키마"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """JWT 토큰 데이터"""
    email: Optional[str] = None

