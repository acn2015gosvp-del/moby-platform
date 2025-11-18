"""
사용자 관련 스키마 모듈

회원가입, 로그인, 사용자 정보 응답을 위한 Pydantic 모델을 정의합니다.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """사용자 기본 정보"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)


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
    email: EmailStr
    password: str


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

