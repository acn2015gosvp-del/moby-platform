"""
데이터베이스 설정 모듈

SQLAlchemy를 사용한 데이터베이스 연결 및 세션 관리를 제공합니다.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.services.schemas.models.core.config import settings
import os

# 환경 변수에서 DATABASE_URL을 가져오거나, 기본값으로 SQLite 사용
# CI/CD 환경에서는 PostgreSQL을 사용 (환경 변수로 설정)
# 로컬 개발 환경에서는 SQLite 사용 (기본값)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./moby.db?mode=rwc"  # 기본값: SQLite (개발용)
)

# 데이터베이스 타입에 따라 엔진 설정 다르게 적용
is_postgresql = DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")

if is_postgresql:
    # PostgreSQL 설정
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # 연결 상태 확인
        pool_size=5,
        max_overflow=10,
        echo=settings.DEBUG
    )
else:
    # SQLite 설정 (개발용)
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 1.0,  # 연결 타임아웃 (1초로 단축 - 빠른 시작)
        },
        poolclass=StaticPool,
        pool_pre_ping=False,  # SQLite는 빠르므로 pre_ping 불필요
        echo=settings.DEBUG  # 디버그 모드에서 SQL 쿼리 로그 출력
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    데이터베이스 세션 의존성
    
    Yields:
        Session: SQLAlchemy 세션
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    데이터베이스 테이블을 생성합니다.
    """
    Base.metadata.create_all(bind=engine)

