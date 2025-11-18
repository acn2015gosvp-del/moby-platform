"""
알림 모델

SQLAlchemy를 사용한 알림 데이터베이스 모델을 정의합니다.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Index
from sqlalchemy.sql import func
from backend.api.services.database import Base


class Alert(Base):
    """알림 테이블 모델"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String, unique=True, index=True, nullable=False)  # Alert Engine에서 생성한 ID
    level = Column(String, nullable=False, index=True)  # info, warning, critical
    message = Column(Text, nullable=False)
    llm_summary = Column(Text, nullable=True)
    sensor_id = Column(String, nullable=False, index=True)
    source = Column(String, nullable=False, default="alert-engine")
    ts = Column(String, nullable=False)  # ISO 8601 타임스탬프 문자열
    details = Column(JSON, nullable=True)  # AlertDetailsModel을 JSON으로 저장
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 복합 인덱스 추가 (쿼리 성능 최적화)
    __table_args__ = (
        Index('idx_alert_sensor_level', 'sensor_id', 'level'),  # sensor_id와 level 조합 쿼리 최적화
        Index('idx_alert_level_created', 'level', 'created_at'),  # level과 created_at 조합 쿼리 최적화
    )

