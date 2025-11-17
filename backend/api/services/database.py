"""
데이터베이스 설정 모듈

SQLAlchemy를 사용한 데이터베이스 연결 및 세션 관리를 제공합니다.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.services.schemas.models.core.config import settings

# SQLite 데이터베이스 URL (개발용)
# 프로덕션에서는 PostgreSQL 등을 사용하는 것을 권장합니다.
DATABASE_URL = "sqlite:///./moby.db"

# SQLite는 단일 스레드에서만 작동하므로 StaticPool 사용
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
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

