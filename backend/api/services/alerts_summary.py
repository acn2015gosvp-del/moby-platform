"""
알림 요약 서비스 모듈

alert_engine.py에서 LLM 요약 로직을 분리하여 제공하는 서비스입니다.
알림 데이터를 받아 LLM을 통해 요약을 생성하는 기능을 제공합니다.
"""
import logging
import asyncio
from typing import Dict, Optional

from backend.api.core.exceptions import LLMSummaryError
from .llm_client import summarize_alert
from .cache import get_cache, cache_key

logger = logging.getLogger(__name__)


def generate_alert_summary(alert_data: Dict) -> Optional[str]:
    """
    알림 데이터를 받아 LLM 요약을 생성합니다. (동기 버전)
    캐싱을 통해 동일한 알림에 대한 중복 요약 생성을 방지합니다.
    
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
            logger.warning("generate_alert_summary: alert_data가 비어있습니다.")
            return None
        
        alert_id = alert_data.get("id", "unknown")
        sensor_id = alert_data.get("sensor_id", "unknown")
        
        # 캐시 키 생성 (alert_id 기반)
        cache = get_cache()
        cache_key_str = cache_key("llm_summary", alert_id=alert_id)
        
        # 캐시에서 조회
        cached_summary = cache.get(cache_key_str)
        if cached_summary is not None:
            logger.debug(
                f"generate_alert_summary: 캐시에서 조회. "
                f"alert_id={alert_id}"
            )
            return cached_summary
        
        logger.debug(
            f"generate_alert_summary: LLM 요약 생성 시작. "
            f"alert_id={alert_id}, sensor_id={sensor_id}"
        )
        
        summary = summarize_alert(alert_data)
        
        if summary:
            # 캐시에 저장 (TTL: 1시간)
            cache.set(cache_key_str, summary, ttl=3600.0)
            logger.info(
                f"generate_alert_summary: LLM 요약 생성 성공. "
                f"alert_id={alert_id}, summary_length={len(summary)}"
            )
        else:
            logger.warning(
                f"generate_alert_summary: LLM 요약이 None을 반환했습니다. "
                f"alert_id={alert_id}"
            )
        
        return summary
        
    except Exception as e:
        alert_id = alert_data.get("id", "unknown") if alert_data else "unknown"
        # Gemini API 키가 없거나 오류가 발생한 경우 None을 반환 (선택사항 기능)
        error_msg = str(e)
        if "GEMINI_API_KEY" in error_msg or "API 키" in error_msg or "Gemini" in error_msg:
            logger.debug(
                f"generate_alert_summary: Gemini API 키가 없거나 모델을 사용할 수 없습니다. "
                f"LLM 요약을 건너뜁니다. (alert_id={alert_id})"
            )
            return None
        logger.warning(
            f"generate_alert_summary: LLM 요약 생성 중 오류 발생: {e}. "
            f"LLM 요약을 건너뜁니다. (alert_id={alert_id})"
        )
        # 예외를 다시 발생시키지 않고 None을 반환 (선택사항 기능)
        return None


async def generate_alert_summary_async(alert_data: Dict) -> Optional[str]:
    """
    알림 데이터를 받아 LLM 요약을 비동기로 생성합니다.
    
    Args:
        alert_data: 요약할 알림 데이터 (dict)
        
    Returns:
        생성된 요약 문자열, 실패 시 None
    """
    try:
        if not alert_data:
            logger.warning("generate_alert_summary_async: alert_data가 비어있습니다.")
            return None
        
        alert_id = alert_data.get("id", "unknown")
        sensor_id = alert_data.get("sensor_id", "unknown")
        
        logger.debug(
            f"generate_alert_summary_async: LLM 요약 생성 시작 (비동기). "
            f"alert_id={alert_id}, sensor_id={sensor_id}"
        )
        
        # I/O 작업을 별도 스레드에서 실행하여 블로킹 방지
        loop = asyncio.get_event_loop()
        summary = await loop.run_in_executor(None, summarize_alert, alert_data)
        
        if summary:
            logger.info(
                f"generate_alert_summary_async: LLM 요약 생성 성공. "
                f"alert_id={alert_id}, summary_length={len(summary)}"
            )
        else:
            logger.warning(
                f"generate_alert_summary_async: LLM 요약이 None을 반환했습니다. "
                f"alert_id={alert_id}"
            )
        
        return summary
        
    except Exception as e:
        alert_id = alert_data.get("id", "unknown") if alert_data else "unknown"
        # Gemini API 키가 없거나 오류가 발생한 경우 None을 반환 (선택사항 기능)
        error_msg = str(e)
        if "GEMINI_API_KEY" in error_msg or "API 키" in error_msg or "Gemini" in error_msg:
            logger.debug(
                f"generate_alert_summary_async: Gemini API 키가 없거나 모델을 사용할 수 없습니다. "
                f"LLM 요약을 건너뜁니다. (alert_id={alert_id})"
            )
            return None
        logger.warning(
            f"generate_alert_summary_async: LLM 요약 생성 중 오류 발생: {e}. "
            f"LLM 요약을 건너뜁니다. (alert_id={alert_id})"
        )
        # 예외를 다시 발생시키지 않고 None을 반환 (선택사항 기능)
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

