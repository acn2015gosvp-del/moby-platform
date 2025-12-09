"""
Pytest 설정 및 공통 Fixture

테스트에 필요한 공통 설정과 fixture를 제공합니다.
"""

import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.api.services.database import Base, get_db

# 환경 변수에서 DATABASE_URL을 가져오거나, 기본값으로 SQLite 사용
# CI 환경에서는 PostgreSQL을 사용 (환경 변수로 설정)
# 로컬 개발 환경에서는 SQLite 사용 (기본값)
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///:memory:"  # 기본값: SQLite 메모리 DB (테스트용)
)

# 데이터베이스 타입에 따라 엔진 설정 다르게 적용
is_postgresql = SQLALCHEMY_DATABASE_URL.startswith("postgresql://") or SQLALCHEMY_DATABASE_URL.startswith("postgres://")

if is_postgresql:
    # PostgreSQL 설정 (CI 환경)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,  # 연결 상태 확인
        pool_size=5,
        max_overflow=10,
    )
else:
    # SQLite 설정 (로컬 개발 환경)
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


@pytest.fixture
def authenticated_user(db_session):
    """인증된 테스트 사용자 생성"""
    from backend.api.models.user import User
    from backend.api.models.role import Role
    from backend.api.services.auth_service import get_password_hash
    
    # 테스트 사용자 생성
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("Test1234"),
        role=Role.ADMIN.value,  # 모든 권한을 가진 ADMIN 역할
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(authenticated_user):
    """인증 토큰 생성"""
    from backend.api.services.auth_service import create_access_token
    from datetime import timedelta
    
    token_data = {"sub": authenticated_user.email}
    token = create_access_token(data=token_data, expires_delta=timedelta(hours=1))
    return token


@pytest.fixture
def auth_headers(auth_token):
    """인증 헤더 반환"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def authenticated_client(client, auth_headers):
    """인증된 테스트 클라이언트"""
    # 클라이언트에 기본 헤더 설정
    original_request = client.request
    
    def authenticated_request(method, url, **kwargs):
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"].update(auth_headers)
        return original_request(method, url, **kwargs)
    
    client.request = authenticated_request
    return client


@pytest.fixture(scope="function", autouse=True)
def cleanup_influx_manager():
    """
    각 테스트 후 InfluxDB Manager를 정리하는 fixture.
    autouse=True로 설정하여 모든 테스트에서 자동으로 실행됩니다.
    """
    yield
    # 테스트 종료 후 InfluxDB Manager 정리
    try:
        from backend.api.services.influx_client import _get_influx_manager
        manager = _get_influx_manager()
        if manager is not None:
            manager.close()
    except Exception:
        # 정리 실패 시 무시 (이미 정리되었을 수 있음)
        pass