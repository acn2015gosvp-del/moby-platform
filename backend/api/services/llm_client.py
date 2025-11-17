"""
LLM 클라이언트 서비스 모듈

OpenAI API를 사용하여 알림 요약을 생성하는 서비스입니다.
싱글톤 패턴을 사용하여 클라이언트를 재사용하고, 에러 처리 및 타임아웃을 제공합니다.
"""

import logging
from typing import Optional
from openai import OpenAI, OpenAIError
from openai.types.chat import ChatCompletion

from .schemas.models.core.config import settings

logger = logging.getLogger(__name__)

# 싱글톤 클라이언트 인스턴스
_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    """
    OpenAI 클라이언트를 싱글톤 패턴으로 반환합니다.
    
    Returns:
        OpenAI: OpenAI 클라이언트 인스턴스
    """
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-api-key":
            raise ValueError(
                "OPENAI_API_KEY가 설정되지 않았습니다. "
                ".env 파일에 OPENAI_API_KEY를 설정해주세요."
            )
        _client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=30.0,  # 30초 타임아웃
            max_retries=2  # 최대 2회 재시도
        )
        logger.debug("OpenAI 클라이언트가 초기화되었습니다.")
    return _client


def summarize_alert(data: dict, timeout: float = 30.0) -> Optional[str]:
    """
    알림 데이터를 받아 LLM 요약을 생성합니다.
    
    Args:
        data: 요약할 알림 데이터 (dict)
        timeout: API 호출 타임아웃 (초, 기본값: 30.0)
        
    Returns:
        생성된 요약 문자열, 실패 시 None
        
    Raises:
        ValueError: API 키가 설정되지 않은 경우
        OpenAIError: OpenAI API 호출 실패 시
        
    Example:
        >>> alert_data = {
        ...     "id": "alert_001",
        ...     "sensor_id": "sensor_001",
        ...     "level": "warning",
        ...     "message": "Anomaly detected"
        ... }
        >>> summary = summarize_alert(alert_data)
        >>> print(summary)
    """
    try:
        if not data:
            logger.warning("summarize_alert: data가 비어있습니다.")
            return None
        
        client = _get_client()
        
        # 프롬프트 생성
        prompt = _create_summary_prompt(data)
        
        logger.debug(
            f"LLM 요약 생성 시작. alert_id={data.get('id', 'unknown')}, "
            f"model={settings.OPENAI_MODEL}"
        )
        
        # API 호출
        response: ChatCompletion = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes industrial IoT alerts in Korean."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=200,
            timeout=timeout
        )
        
        summary = response.choices[0].message.content
        
        if summary:
            logger.info(
                f"LLM 요약 생성 성공. alert_id={data.get('id', 'unknown')}, "
                f"summary_length={len(summary)}"
            )
        else:
            logger.warning(
                f"LLM 요약이 None을 반환했습니다. alert_id={data.get('id', 'unknown')}"
            )
        
        return summary
        
    except ValueError as e:
        logger.error(f"summarize_alert: 설정 오류 - {e}")
        raise
    except OpenAIError as e:
        logger.error(
            f"summarize_alert: OpenAI API 오류 - {e}. "
            f"alert_id={data.get('id', 'unknown') if data else 'unknown'}"
        )
        raise
    except Exception as e:
        logger.exception(
            f"summarize_alert: 예상치 못한 오류 - {e}. "
            f"alert_id={data.get('id', 'unknown') if data else 'unknown'}"
        )
        raise


def _create_summary_prompt(data: dict) -> str:
    """
    알림 데이터로부터 요약 프롬프트를 생성합니다.
    
    Args:
        data: 알림 데이터 (dict)
        
    Returns:
        생성된 프롬프트 문자열
    """
    alert_id = data.get("id", "unknown")
    sensor_id = data.get("sensor_id", "unknown")
    level = data.get("level", "unknown")
    message = data.get("message", "No message")
    norm = data.get("details", {}).get("norm", "N/A")
    severity = data.get("details", {}).get("severity", "N/A")
    
    prompt = f"""다음 산업용 IoT 알림을 한국어로 간결하게 요약해주세요:

알림 ID: {alert_id}
센서 ID: {sensor_id}
레벨: {level}
메시지: {message}
Norm 값: {norm}
심각도: {severity}

요약은 2-3 문장으로 작성하고, 주요 이상 징후와 권장 조치를 포함해주세요."""
    
    return prompt


def reset_client():
    """
    클라이언트 인스턴스를 리셋합니다. (테스트용)
    """
    global _client
    _client = None
    logger.debug("OpenAI 클라이언트가 리셋되었습니다.")
