"""
알림 우선순위 처리 서비스

Track A (Grafana Webhook)와 Track B (AI Model)에서 받은 알림을
우선순위 로직(Critical > Warning > Info)에 따라 처리합니다.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, UTC, timezone

from backend.api.services.schemas.models.core.logger import get_logger
from backend.api.services.alert_engine import AlertPayloadModel, AlertDetailsModel, process_alert
from backend.api.services.constants import AlertLevel
from backend.api.services.sensor_routing import route_severity_by_sensor_type

logger = get_logger(__name__)


def _now_iso() -> str:
    """UTC 기준 ISO8601 타임스탬프 문자열을 반환합니다."""
    try:
        return datetime.now(UTC).isoformat()
    except TypeError:
        # Python 3.9, 3.10 호환성
        return datetime.now(timezone.utc).isoformat()


def determine_priority_level(level: str) -> int:
    """
    알림 레벨을 우선순위 숫자로 변환합니다.
    
    Args:
        level: 알림 레벨 (critical, warning, info)
        
    Returns:
        우선순위 숫자 (높을수록 우선순위가 높음)
    """
    priority_map = {
        AlertLevel.CRITICAL: 3,
        AlertLevel.WARNING: 2,
        AlertLevel.INFO: 1,
        "critical": 3,
        "warning": 2,
        "info": 1,
    }
    return priority_map.get(level, 0)


def process_grafana_alert(
    grafana_alert: Dict[str, Any],
    sensor_id: Optional[str] = None
) -> Optional[AlertPayloadModel]:
    """
    Grafana Webhook에서 받은 알림을 처리하여 표준 AlertPayloadModel로 변환합니다.
    (Track A)
    
    Args:
        grafana_alert: Grafana에서 전송한 웹훅 알림 데이터
        sensor_id: 센서 ID (없으면 Grafana 데이터에서 추출 시도)
        
    Returns:
        변환된 AlertPayloadModel 또는 None (처리 실패 시)
    """
    try:
        # Grafana 웹훅 형식 파싱
        # Grafana 웹훅은 여러 형식이 있을 수 있으므로 유연하게 처리
        alert_data = grafana_alert.get("alerts", [{}])[0] if "alerts" in grafana_alert else grafana_alert
        
        # 알림 레벨 결정
        state = alert_data.get("state", "").lower()
        labels = alert_data.get("labels", {})
        annotations = alert_data.get("annotations", {})
        
        # 메시지 구성 (센서 타입 감지에 사용)
        summary = annotations.get("summary", "")
        description = annotations.get("description", "")
        message = summary or description or alert_data.get("message", "")
        
        # 레벨 매핑
        if state in ["alerting", "firing"]:
            # 1순위: labels에서 명시적으로 지정된 severity 확인
            explicit_severity = labels.get("severity", "").lower()
            if explicit_severity in ["critical", "error", "fatal"]:
                severity = "critical"
                level = AlertLevel.CRITICAL
            elif explicit_severity in ["warning", "warn"]:
                severity = "warning"
                level = AlertLevel.WARNING
            else:
                # 2순위: 센서 타입에 따른 자동 라우팅
                severity = route_severity_by_sensor_type(
                    labels=labels,
                    message=message,
                    default_severity="critical"  # 알림 상태면 기본적으로 Critical
                )
                if severity == "critical":
                    level = AlertLevel.CRITICAL
                elif severity == "warning":
                    level = AlertLevel.WARNING
                else:
                    level = AlertLevel.CRITICAL
        elif state == "pending":
            severity = "warning"
            level = AlertLevel.WARNING
        else:
            severity = "info"
            level = AlertLevel.INFO
        
        # 메시지는 위에서 이미 구성됨
        
        # 센서 ID 추출
        device_id = sensor_id or labels.get("device_id") or labels.get("sensor_id") or labels.get("instance", "unknown_device")
        
        # AlertDetailsModel 생성
        details = AlertDetailsModel(
            vector=[],
            norm=0.0,
            threshold=None,
            warning_threshold=None,
            critical_threshold=None,
            severity=severity,
            meta={
                "grafana_alert": alert_data,
                "rule_name": labels.get("alertname", ""),
            }
        )
        
        # AlertPayloadModel 생성
        alert_payload = AlertPayloadModel(
            id=f"grafana-{alert_data.get('fingerprint', datetime.now().isoformat())}",
            level=level.value,
            message=message,
            llm_summary=None,  # Grafana 알림은 LLM 요약 없음
            sensor_id=device_id,
            source="grafana-webhook",
            ts=_now_iso(),
            details=details
        )
        
        logger.info(
            f"✅ Grafana 알림 처리 완료. "
            f"Device: {device_id}, Level: {level.value}, Message: {message[:50]}..."
        )
        
        return alert_payload
        
    except Exception as e:
        logger.error(
            f"❌ Grafana 알림 처리 실패: {e}",
            exc_info=True
        )
        return None


def process_ai_model_alert(
    ai_alert_data: Dict[str, Any]
) -> Optional[AlertPayloadModel]:
    """
    AI Model에서 받은 이상 탐지 결과를 처리하여 AlertPayloadModel로 변환합니다.
    (Track B)
    
    Args:
        ai_alert_data: AI 모델에서 생성한 이상 탐지 데이터
        
    Returns:
        변환된 AlertPayloadModel 또는 None (이상이 아닌 경우)
    """
    try:
        # AI 모델 알림은 기존 alert_engine.process_alert를 사용
        result = process_alert(ai_alert_data)
        
        if result:
            logger.info(
                f"✅ AI 모델 알림 처리 완료. "
                f"Sensor: {result.sensor_id}, Level: {result.level}"
            )
        
        return result
        
    except Exception as e:
        logger.error(
            f"❌ AI 모델 알림 처리 실패: {e}",
            exc_info=True
        )
        return None


def merge_and_prioritize_alerts(
    alert1: Optional[AlertPayloadModel],
    alert2: Optional[AlertPayloadModel]
) -> Optional[AlertPayloadModel]:
    """
    두 알림을 비교하여 우선순위가 높은 알림을 반환합니다.
    우선순위: Critical > Warning > Info
    
    Args:
        alert1: 첫 번째 알림
        alert2: 두 번째 알림
        
    Returns:
        우선순위가 높은 알림 (둘 다 없으면 None)
    """
    if alert1 is None:
        return alert2
    if alert2 is None:
        return alert1
    
    priority1 = determine_priority_level(alert1.level)
    priority2 = determine_priority_level(alert2.level)
    
    if priority1 >= priority2:
        logger.debug(f"알림 우선순위 결정: Alert1 선택 (Priority: {priority1} >= {priority2})")
        return alert1
    else:
        logger.debug(f"알림 우선순위 결정: Alert2 선택 (Priority: {priority2} > {priority1})")
        return alert2

