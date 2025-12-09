"""
LLM 클라이언트 서비스 모듈

Gemini API를 사용하여 알림 요약을 생성하는 서비스입니다.
싱글톤 패턴을 사용하여 클라이언트를 재사용하고, 에러 처리 및 타임아웃을 제공합니다.
"""

import logging
import os
from typing import Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from .schemas.models.core.config import settings

logger = logging.getLogger(__name__)

# 싱글톤 모델 인스턴스
_model: Optional[genai.GenerativeModel] = None
_model_name: Optional[str] = None


def _get_model() -> Optional[genai.GenerativeModel]:
    """
    Gemini 모델을 싱글톤 패턴으로 반환합니다.
    API 키가 없으면 None을 반환합니다 (선택사항 기능).
    
    Returns:
        GenerativeModel: Gemini 모델 인스턴스, API 키가 없으면 None
    """
    global _model, _model_name
    
    if _model is None:
        if not GEMINI_AVAILABLE:
            logger.debug("google-generativeai 패키지가 설치되지 않았습니다. LLM 요약 기능을 사용할 수 없습니다.")
            return None
        
        api_key = os.getenv('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key or api_key in ("your-api-key", "your-gemini-api-key-here", ""):
            logger.debug("GEMINI_API_KEY가 설정되지 않았습니다. LLM 요약 기능을 사용할 수 없습니다.")
            return None
        
        try:
            genai.configure(api_key=api_key)
            
            # 알림 요약에 적합한 빠른 모델 우선 사용
            model_candidates = [
                'gemini-2.5-flash',              # 가장 빠르고 효율적
                'models/gemini-2.5-flash',      # 긴 이름 버전
                'models/gemini-flash-latest',    # 최신 Flash 모델
                'gemini-flash-latest',           # 짧은 이름
                'models/gemini-1.5-flash',       # 안정적인 Flash 모델
                'gemini-1.5-flash',              # 짧은 이름
            ]
            
            for model_name in model_candidates:
                try:
                    test_model = genai.GenerativeModel(
                        model_name=model_name,
                        generation_config={
                            'temperature': 0.7,
                            'max_output_tokens': 200,  # 알림 요약은 짧게
                        }
                    )
                    
                    # 간단한 테스트 요청
                    test_response = test_model.generate_content("test")
                    
                    # 안전하게 테스트 응답 확인
                    test_text = None
                    try:
                        if hasattr(test_response, 'text') and test_response.text:
                            test_text = test_response.text
                        elif hasattr(test_response, 'candidates') and test_response.candidates:
                            candidate = test_response.candidates[0]
                            if hasattr(candidate, 'content') and candidate.content:
                                if hasattr(candidate.content, 'parts'):
                                    parts = candidate.content.parts
                                    if parts and hasattr(parts[0], 'text'):
                                        test_text = parts[0].text
                    
                    except AttributeError:
                        # response.text 접근 실패 시 candidates에서 추출 시도
                        if hasattr(test_response, 'candidates') and test_response.candidates:
                            candidate = test_response.candidates[0]
                            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                                parts = candidate.content.parts
                                if parts and hasattr(parts[0], 'text'):
                                    test_text = parts[0].text
                    
                    if test_text:
                        _model = test_model
                        _model_name = model_name
                        logger.debug(f"Gemini 모델 초기화 완료: {model_name}")
                        break
                except Exception as e:
                    error_msg = str(e)
                    logger.debug(f"모델 '{model_name}' 초기화 실패: {e}")
                    
                    # API 키 정지 상태 감지
                    if "CONSUMER_SUSPENDED" in error_msg or "has been suspended" in error_msg.lower():
                        logger.error(
                            f"Gemini API 키가 정지되었습니다. LLM 요약 기능을 사용할 수 없습니다. "
                            f"Google AI Studio (https://makersuite.google.com/app/apikey)에서 새 API 키를 생성하세요."
                        )
                        return None
                    continue
            
            if _model is None:
                logger.warning("사용 가능한 Gemini 모델을 찾을 수 없습니다. LLM 요약 기능을 사용할 수 없습니다.")
                return None
                
        except Exception as e:
            logger.warning(f"Gemini API 초기화 실패: {e}. LLM 요약 기능을 사용할 수 없습니다.")
            return None
    
    return _model


def summarize_alert(data: dict, timeout: float = 30.0) -> Optional[str]:
    """
    알림 데이터를 받아 LLM 요약을 생성합니다 (Gemini API 사용).
    
    Args:
        data: 요약할 알림 데이터 (dict)
        timeout: API 호출 타임아웃 (초, 기본값: 30.0) - Gemini는 내부적으로 처리
        
    Returns:
        생성된 요약 문자열, 실패 시 None
        
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
        
        model = _get_model()
        if model is None:
            logger.debug("Gemini 모델을 사용할 수 없습니다. LLM 요약을 건너뜁니다.")
            return None
        
        # 프롬프트 생성
        prompt = _create_summary_prompt(data)
        
        logger.debug(
            f"LLM 요약 생성 시작. alert_id={data.get('id', 'unknown')}, "
            f"model={_model_name}"
        )
        
        # Gemini API 호출
        response = model.generate_content(prompt)
        
        # 안전하게 응답 텍스트 추출
        summary = None
        try:
            if hasattr(response, 'text') and response.text:
                summary = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                # candidates에서 텍스트 추출
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts'):
                            parts_text = []
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    parts_text.append(part.text)
                            if parts_text:
                                summary = ''.join(parts_text)
                                break
        
        except AttributeError as ae:
            # response.text 접근 실패 시 candidates에서 추출 시도
            logger.warning(f"LLM 응답 처리 중 AttributeError: {ae}, candidates에서 추출 시도")
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    parts = candidate.content.parts
                    if parts and hasattr(parts[0], 'text'):
                        summary = parts[0].text
        
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
        
    except Exception as e:
        error_msg = str(e)
        alert_id = data.get('id', 'unknown') if data else 'unknown'
        
        # 429 할당량 초과 오류 처리
        if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
            logger.warning(
                f"summarize_alert: Gemini API 할당량 초과 - {e}. "
                f"alert_id={alert_id}. "
                f"LLM 요약을 건너뜁니다. 잠시 후 다시 시도하세요."
            )
            return None
        
        # 401/403 인증 오류 처리
        if "401" in error_msg or "403" in error_msg or "API_KEY_INVALID" in error_msg:
            logger.warning(
                f"summarize_alert: Gemini API 키 인증 오류 - {e}. "
                f"alert_id={alert_id}. "
                f"LLM 요약을 건너뜁니다. API 키를 확인하세요."
            )
            return None
        
        # 기타 오류
        logger.warning(
            f"summarize_alert: Gemini API 오류 - {e}. "
            f"alert_id={alert_id}. "
            f"LLM 요약을 건너뜁니다."
        )
        return None


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
    global _model, _model_name
    _model = None
    _model_name = None
    logger.debug("Gemini 모델이 리셋되었습니다.")
