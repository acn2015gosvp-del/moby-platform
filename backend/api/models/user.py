"""
사용자 모델

SQLAlchemy를 사용한 사용자 데이터베이스 모델을 정의합니다.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from backend.api.services.database import Base
from backend.api.models.role import Role


class User(Base):
    """사용자 테이블 모델"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default=Role.USER.value, nullable=False)  # 역할 필드 추가
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

