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
# WAL 모드 활성화로 성능 향상
DATABASE_URL = "sqlite:///./moby.db?mode=rwc"

# SQLite는 단일 스레드에서만 작동하므로 StaticPool 사용
# 성능 최적화를 위한 설정 추가
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 1.0,  # 연결 타임아웃 (1초로 단축 - 빠른 시작)
    },
    poolclass=StaticPool,
    pool_pre_ping=False,  # SQLite는 빠르므로 pre_ping 불필요 (오히려 느려질 수 있음)
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

