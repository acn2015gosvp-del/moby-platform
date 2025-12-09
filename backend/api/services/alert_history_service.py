"""
알림 이력 서비스 모듈

알림 이력을 데이터베이스에 저장하고 조회하는 기능을 제공합니다.
이상징후 모니터링 및 자동 보고서 시스템용 서비스입니다.
"""

import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import desc, func as sql_func

from backend.api.models.alert_history import AlertHistory, CheckStatus
from backend.api.services.schemas.models.core.logger import get_logger

logger = get_logger(__name__)


def save_alert_history(
    db: Session,
    device_id: str,
    message: str,
    error_code: Optional[str] = None,
    raw_value: Optional[Dict[str, Any]] = None,
    occurred_at: Optional[datetime] = None
) -> AlertHistory:
    """
    알림 이력을 데이터베이스에 저장합니다.
    
    Args:
        db: 데이터베이스 세션
        device_id: 디바이스/센서 ID
        message: 알림 메시지
        error_code: 에러 코드 (선택)
        raw_value: 원시 데이터 값 (dict, JSON 문자열로 변환됨)
        occurred_at: 발생 시각 (없으면 현재 시각)
        
    Returns:
        저장된 AlertHistory 모델 인스턴스
    """
    try:
        # raw_value를 JSON 문자열로 변환
        raw_value_str = None
        if raw_value:
            try:
                raw_value_str = json.dumps(raw_value, ensure_ascii=False, default=str)
            except Exception as e:
                logger.warning(f"raw_value JSON 변환 실패: {e}")
                raw_value_str = str(raw_value)
        
        # AlertHistory 모델 생성
        alert_history = AlertHistory(
            device_id=device_id,
            message=message,
            error_code=error_code,
            raw_value=raw_value_str,
            occurred_at=occurred_at or datetime.now(),
            check_status=CheckStatus.UNCHECKED
        )
        
        db.add(alert_history)
        db.commit()
        db.refresh(alert_history)
        
        logger.info(
            f"✅ Alert history saved to database. "
            f"ID: {alert_history.id}, Device: {device_id}, Message: {message[:50]}..."
        )
        
        return alert_history
        
    except Exception as e:
        logger.error(
            f"❌ Failed to save alert history to database. "
            f"Device: {device_id}, Error: {e}",
            exc_info=True
        )
        db.rollback()
        raise


def get_unchecked_alerts(
    db: Session,
    limit: Optional[int] = None
) -> List[AlertHistory]:
    """
    미확인 알림 목록을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        limit: 조회할 최대 개수 (없으면 전체)
        
    Returns:
        AlertHistory 모델 인스턴스 리스트
    """
    try:
        query = db.query(AlertHistory).filter(
            AlertHistory.check_status == CheckStatus.UNCHECKED
        ).order_by(desc(AlertHistory.occurred_at))
        
        if limit:
            query = query.limit(limit)
        
        alerts = query.all()
        
        logger.debug(f"Retrieved {len(alerts)} unchecked alerts (limit={limit})")
        
        return alerts
        
    except Exception as e:
        logger.error(
            f"❌ Failed to retrieve unchecked alerts. Error: {e}",
            exc_info=True
        )
        raise


def check_alert(
    db: Session,
    alert_id: int,
    checked_by: str
) -> Optional[AlertHistory]:
    """
    알림을 확인 처리합니다.
    
    Args:
        db: 데이터베이스 세션
        alert_id: 알림 ID
        checked_by: 확인한 사용자 ID 또는 이메일
        
    Returns:
        업데이트된 AlertHistory 모델 인스턴스 또는 None
    """
    try:
        alert = db.query(AlertHistory).filter(AlertHistory.id == alert_id).first()
        
        if not alert:
            logger.warning(f"Alert history not found: ID={alert_id}")
            return None
        
        alert.check_status = CheckStatus.CHECKED
        alert.checked_by = checked_by
        
        db.commit()
        db.refresh(alert)
        
        logger.info(
            f"✅ Alert checked. ID: {alert_id}, Checked by: {checked_by}"
        )
        
        return alert
        
    except Exception as e:
        logger.error(
            f"❌ Failed to check alert. ID: {alert_id}, Error: {e}",
            exc_info=True
        )
        db.rollback()
        raise


def get_today_alerts(db: Session, target_date: Optional[date] = None) -> List[AlertHistory]:
    """
    금일 발생한 알림 목록을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        target_date: 조회할 날짜 (없으면 오늘)
        
    Returns:
        AlertHistory 모델 인스턴스 리스트
    """
    try:
        if target_date is None:
            target_date = date.today()
        
        # 날짜 범위 설정 (해당 날짜의 00:00:00 ~ 23:59:59)
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        alerts = db.query(AlertHistory).filter(
            AlertHistory.occurred_at >= start_datetime,
            AlertHistory.occurred_at <= end_datetime
        ).order_by(desc(AlertHistory.occurred_at)).all()
        
        logger.info(
            f"Retrieved {len(alerts)} alerts for date: {target_date}"
        )
        
        return alerts
        
    except Exception as e:
        logger.error(
            f"❌ Failed to retrieve today alerts. Date: {target_date}, Error: {e}",
            exc_info=True
        )
        raise

