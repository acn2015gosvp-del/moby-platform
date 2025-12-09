"""
Pytest 설정 및 공통 Fixture

테스트에 필요한 공통 설정과 fixture를 제공합니다.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.api.services.database import Base, get_db

# 테스트용 SQLite 데이터베이스 (메모리)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# 테스트용 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    테스트용 데이터베이스 세션 fixture
    
    각 테스트마다 새로운 세션을 생성하고, 테스트 후 롤백합니다.
    """
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    # 세션 생성
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        # 테이블 삭제
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    FastAPI 테스트 클라이언트 fixture
    
    데이터베이스 의존성을 테스트용 세션으로 오버라이드합니다.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """테스트용 사용자 데이터"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "Test1234"
    }


@pytest.fixture
def sample_sensor_data():
    """테스트용 센서 데이터"""
    return {
        "device_id": "sensor_001",
        "temperature": 25.5,
        "humidity": 60.0,
        "vibration": 0.5,
        "sound": 45.2
    }


@pytest.fixture
def sample_alert_data():
    """테스트용 알림 데이터"""
    return {
        "vector": [1.5, 2.3, 3.1],
        "threshold": 5.0,
        "sensor_id": "sensor_001",
        "enable_llm_summary": False
    }

