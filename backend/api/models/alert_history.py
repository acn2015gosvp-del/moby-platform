"""
알림 이력 모델

SQLAlchemy를 사용한 알림 이력 데이터베이스 모델을 정의합니다.
이상징후 모니터링 및 자동 보고서 시스템용 테이블입니다.
"""

import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, Index
from sqlalchemy.sql import func
from backend.api.services.database import Base


class CheckStatus(enum.Enum):
    """알림 확인 상태 열거형"""
    UNCHECKED = "UNCHECKED"
    CHECKED = "CHECKED"


class AlertHistory(Base):
    """알림 이력 테이블 모델 (tb_alert_history)"""
    __tablename__ = "tb_alert_history"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String, nullable=False, index=True, comment="디바이스/센서 ID")
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True, server_default=func.now(), comment="알림 발생 시각")
    error_code = Column(String, nullable=True, index=True, comment="에러 코드")
    raw_value = Column(Text, nullable=True, comment="원시 데이터 값 (JSON 문자열)")
    message = Column(Text, nullable=False, comment="알림 메시지")
    check_status = Column(SQLEnum(CheckStatus), nullable=False, default=CheckStatus.UNCHECKED, index=True, comment="확인 상태")
    checked_by = Column(String, nullable=True, comment="확인한 사용자 ID 또는 이메일")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True, comment="레코드 생성 시각")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="레코드 수정 시각")
    
    # 복합 인덱스 추가 (쿼리 성능 최적화)
    __table_args__ = (
        Index('idx_alert_history_device_status', 'device_id', 'check_status'),  # 디바이스별 미확인 알림 조회 최적화
        Index('idx_alert_history_occurred_status', 'occurred_at', 'check_status'),  # 날짜별 미확인 알림 조회 최적화
    )

