"""
센서 타입별 Severity 라우팅 서비스

Grafana Webhook에서 받은 알림을 센서 타입에 따라 자동으로 severity를 설정합니다.

라우팅 규칙:
- Critical (즉시 중단): 온도, 진동 → severity=critical
- Warning (점검 요망): 소음, 습도 → severity=warning
"""

import logging
from typing import Dict, Any, Optional
from backend.api.services.schemas.models.core.logger import get_logger
from backend.api.services.constants import AlertLevel

logger = get_logger(__name__)


# 센서 타입 매핑 (한글/영어 모두 지원)
SENSOR_TYPE_MAPPING = {
    # Critical 센서 (즉시 중단)
    "critical": {
        "온도": "temperature",
        "temperature": "temperature",
        "temp": "temperature",
        "진동": "vibration",
        "vibration": "vibration",
        "vib": "vibration",
    },
    # Warning 센서 (점검 요망)
    "warning": {
        "소음": "sound",
        "sound": "sound",
        "음압": "sound",
        "습도": "humidity",
        "humidity": "humidity",
        "humid": "humidity",
    }
}


def detect_sensor_type(labels: Dict[str, Any], message: str = "") -> Optional[str]:
    """
    Grafana 알림에서 센서 타입을 감지합니다.
    
    Args:
        labels: Grafana 알림의 labels 딕셔너리
        message: 알림 메시지 (선택)
        
    Returns:
        감지된 센서 타입 (temperature, vibration, sound, humidity) 또는 None
    """
    # labels에서 센서 타입 추출 시도
    sensor_type = (
        labels.get("sensor_type") or
        labels.get("sensor") or
        labels.get("type") or
        labels.get("metric") or
        None
    )
    
    if sensor_type:
        sensor_type_lower = str(sensor_type).lower()
        # 매핑에서 찾기
        for severity, sensors in SENSOR_TYPE_MAPPING.items():
            for key, value in sensors.items():
                if key.lower() in sensor_type_lower:
                    logger.debug(f"센서 타입 감지 (labels): {value} (from: {sensor_type})")
                    return value
    
    # 메시지에서 센서 타입 추출 시도
    if message:
        message_lower = message.lower()
        for severity, sensors in SENSOR_TYPE_MAPPING.items():
            for key, value in sensors.items():
                if key.lower() in message_lower:
                    logger.debug(f"센서 타입 감지 (message): {value} (from: {key})")
                    return value
    
    # alertname에서 추출 시도
    alertname = labels.get("alertname", "").lower()
    if alertname:
        for severity, sensors in SENSOR_TYPE_MAPPING.items():
            for key, value in sensors.items():
                if key.lower() in alertname:
                    logger.debug(f"센서 타입 감지 (alertname): {value} (from: {alertname})")
                    return value
    
    logger.debug("센서 타입을 감지할 수 없습니다.")
    return None


def route_severity_by_sensor_type(
    labels: Dict[str, Any],
    message: str = "",
    default_severity: str = "critical"
) -> str:
    """
    센서 타입에 따라 severity를 라우팅합니다.
    
    라우팅 규칙:
    - Critical (즉시 중단): 온도, 진동 → severity=critical
    - Warning (점검 요망): 소음, 습도 → severity=warning
    
    Args:
        labels: Grafana 알림의 labels 딕셔너리
        message: 알림 메시지 (선택)
        default_severity: 센서 타입을 감지하지 못한 경우 기본 severity
        
    Returns:
        라우팅된 severity (critical 또는 warning)
    """
    sensor_type = detect_sensor_type(labels, message)
    
    if not sensor_type:
        logger.debug(f"센서 타입 감지 실패, 기본 severity 사용: {default_severity}")
        return default_severity
    
    # Critical 센서 확인
    if sensor_type in SENSOR_TYPE_MAPPING["critical"].values():
        logger.info(f"✅ 센서 타입 라우팅: {sensor_type} → severity=critical")
        return "critical"
    
    # Warning 센서 확인
    if sensor_type in SENSOR_TYPE_MAPPING["warning"].values():
        logger.info(f"✅ 센서 타입 라우팅: {sensor_type} → severity=warning")
        return "warning"
    
    # 매핑에 없는 경우 기본값 사용
    logger.warning(
        f"⚠️ 알려지지 않은 센서 타입: {sensor_type}, 기본 severity 사용: {default_severity}"
    )
    return default_severity

