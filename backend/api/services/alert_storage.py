"""
알림 저장소 서비스 모듈

알림을 데이터베이스에 저장하고 조회하는 기능을 제공합니다.
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.api.models.alert import Alert
from backend.api.services.alert_engine import AlertPayloadModel

logger = logging.getLogger(__name__)


def save_alert(db: Session, alert_payload: AlertPayloadModel) -> Alert:
    """
    알림을 데이터베이스에 저장합니다.
    
    Args:
        db: 데이터베이스 세션
        alert_payload: 저장할 알림 페이로드
        
    Returns:
        저장된 Alert 모델 인스턴스
    """
    try:
        # AlertPayloadModel을 dict로 변환
        alert_dict = alert_payload.model_dump()
        
        # details 처리: 이미 dict이거나 AlertDetailsModel 인스턴스일 수 있음
        details_value = alert_dict.get("details")
        if details_value:
            if hasattr(details_value, "model_dump"):
                # AlertDetailsModel 인스턴스인 경우
                details_dict = details_value.model_dump()
            elif isinstance(details_value, dict):
                # 이미 dict인 경우
                details_dict = details_value
            else:
                details_dict = None
        else:
            details_dict = None
        
        # Alert 모델 생성
        db_alert = Alert(
            alert_id=alert_dict["id"],
            level=alert_dict["level"],
            message=alert_dict["message"],
            llm_summary=alert_dict.get("llm_summary"),
            sensor_id=alert_dict["sensor_id"],
            source=alert_dict["source"],
            ts=alert_dict["ts"],
            details=details_dict
        )
        
        db.add(db_alert)
        db.commit()
        db.refresh(db_alert)
        
        logger.info(
            f"✅ Alert saved to database. "
            f"Alert ID: {alert_dict['id']}, Sensor: {alert_dict['sensor_id']}, Level: {alert_dict['level']}"
        )
        
        return db_alert
        
    except Exception as e:
        logger.error(
            f"❌ Failed to save alert to database. "
            f"Alert ID: {alert_dict.get('id', 'unknown')}, Error: {e}",
            exc_info=True
        )
        db.rollback()
        raise


def get_latest_alerts(
    db: Session,
    limit: int = 10,
    sensor_id: Optional[str] = None,
    level: Optional[str] = None
) -> List[Alert]:
    """
    최신 알림 목록을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        limit: 조회할 최대 개수
        sensor_id: 특정 센서 ID로 필터링 (선택)
        level: 특정 레벨로 필터링 (선택)
        
    Returns:
        Alert 모델 인스턴스 리스트
    """
    try:
        query = db.query(Alert)
        
        # 필터링
        if sensor_id:
            query = query.filter(Alert.sensor_id == sensor_id)
        if level:
            query = query.filter(Alert.level == level)
        
        # 최신순 정렬 및 제한
        # created_at이 None인 경우를 대비하여 id로도 정렬
        try:
            alerts = query.order_by(desc(Alert.created_at), desc(Alert.id)).limit(limit).all()
        except Exception as order_error:
            logger.warning(f"created_at 정렬 실패, id로만 정렬 시도: {order_error}")
            alerts = query.order_by(desc(Alert.id)).limit(limit).all()
        
        logger.debug(
            f"Retrieved {len(alerts)} latest alerts. "
            f"Filters: sensor_id={sensor_id}, level={level}, limit={limit}"
        )
        
        return alerts
        
    except Exception as e:
        logger.error(
            f"❌ Failed to retrieve latest alerts. Error: {e}",
            exc_info=True
        )
        raise


def get_alert_by_id(db: Session, alert_id: str) -> Optional[Alert]:
    """
    알림 ID로 알림을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        alert_id: 조회할 알림 ID
        
    Returns:
        Alert 모델 인스턴스 또는 None
    """
    try:
        alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
        return alert
    except Exception as e:
        logger.error(
            f"❌ Failed to retrieve alert by ID. Alert ID: {alert_id}, Error: {e}",
            exc_info=True
        )
        return None


def delete_all_alerts(db: Session) -> int:
    """
    모든 알림을 삭제합니다.
    
    Args:
        db: 데이터베이스 세션
        
    Returns:
        삭제된 알림 개수
    """
    try:
        # 모든 알림 조회
        alerts = db.query(Alert).all()
        count = len(alerts)
        
        # 모든 알림 삭제
        for alert in alerts:
            db.delete(alert)
        
        db.commit()
        
        logger.info(f"✅ Deleted {count} alerts from database")
        
        return count
        
    except Exception as e:
        logger.error(
            f"❌ Failed to delete all alerts. Error: {e}",
            exc_info=True
        )
        db.rollback()
        raise
