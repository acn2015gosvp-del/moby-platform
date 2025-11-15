"""
알림 요약 서비스 모듈

alert_engine.py에서 LLM 요약 로직을 분리하여 제공하는 서비스입니다.
알림 데이터를 받아 LLM을 통해 요약을 생성하는 기능을 제공합니다.
"""
from typing import Dict, Optional
from services.llm_client import summarize_alert


def generate_alert_summary(alert_data: Dict) -> Optional[str]:
    """
    알림 데이터를 받아 LLM 요약을 생성합니다.
    
    Args:
        alert_data: 요약할 알림 데이터 (dict)
        
    Returns:
        생성된 요약 문자열, 실패 시 None
        
    Example:
        >>> alert_data = {"anomaly_score": 0.82, "sensor_id": "temp_01", "timestamp": "2025-01-01T10:00:00Z"}
        >>> summary = generate_alert_summary(alert_data)
        >>> print(summary)
    """
    try:
        if not alert_data:
            return None
            
        summary = summarize_alert(alert_data)
        return summary
    except Exception as e:
        # TODO: 로깅 추가 필요
        print(f"Error generating alert summary: {e}")
        return None


def generate_summary_batch(alert_list: list[Dict]) -> list[Optional[str]]:
    """
    여러 알림에 대한 요약을 배치로 생성합니다.
    
    Args:
        alert_list: 요약할 알림 데이터 리스트
        
    Returns:
        각 알림에 대한 요약 리스트 (실패 시 None 포함)
        
    Example:
        >>> alerts = [
        ...     {"anomaly_score": 0.82, "sensor_id": "temp_01"},
        ...     {"anomaly_score": 0.95, "sensor_id": "vib_02"}
        ... ]
        >>> summaries = generate_summary_batch(alerts)
    """
    summaries = []
    for alert_data in alert_list:
        summary = generate_alert_summary(alert_data)
        summaries.append(summary)
    return summaries

