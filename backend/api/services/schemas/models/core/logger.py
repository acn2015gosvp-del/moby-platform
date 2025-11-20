"""
로깅 설정 모듈

중앙 집중식 로깅 설정을 제공합니다.
모든 모듈에서 일관된 로깅을 사용할 수 있도록 합니다.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from .config import settings


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> None:
    """
    애플리케이션 전체 로깅을 설정합니다.
    환경에 따라 자동으로 최적의 로깅 레벨을 설정합니다.
    
    Args:
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  None이면 환경에 따라 자동 결정
        log_file: 로그 파일 경로 (None이면 파일 로깅 안 함)
        log_format: 로그 포맷 문자열
    """
    # 로그 레벨 결정 (환경별 기본값)
    if log_level is None:
        if settings.is_production():
            # 프로덕션: INFO 이상만 로깅 (성능 최적화)
            level = settings.LOG_LEVEL or "INFO"
        elif settings.DEBUG:
            # 디버그 모드: 모든 로그 출력
            level = "DEBUG"
        else:
            # 개발 환경: INFO 기본
            level = settings.LOG_LEVEL or "INFO"
    else:
        level = log_level
    
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # 기본 로그 포맷
    if log_format is None:
        log_format = (
            "%(asctime)s | %(levelname)-8s | %(name)s | "
            "%(filename)s:%(lineno)d | %(message)s"
        )
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # 기존 핸들러 제거 (중복 방지)
    root_logger.handlers.clear()
    
    # 콘솔 핸들러 (항상 추가)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # 파일 핸들러 (선택사항)
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(numeric_level)
            file_formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
            
            logging.info(f"📝 File logging enabled: {log_file}")
        except Exception as e:
            logging.warning(f"⚠️ Failed to setup file logging: {e}")
    
    # 서드파티 라이브러리 로그 레벨 조정 (환경별)
    if settings.is_production():
        # 프로덕션: 서드파티 라이브러리는 WARNING 이상만
        third_party_level = logging.WARNING
    elif settings.DEBUG:
        # 디버그 모드: 모든 로그 출력
        third_party_level = logging.DEBUG
    else:
        # 개발 환경: INFO 이상
        third_party_level = logging.INFO
    
    logging.getLogger("uvicorn").setLevel(third_party_level)
    logging.getLogger("uvicorn.access").setLevel(
        logging.WARNING if settings.is_production() else logging.INFO
    )
    logging.getLogger("fastapi").setLevel(third_party_level)
    logging.getLogger("paho").setLevel(third_party_level)
    logging.getLogger("influxdb_client").setLevel(third_party_level)
    # OpenAI는 더 이상 사용하지 않음 (Gemini API로 완전 대체)
    # logging.getLogger("openai").setLevel(third_party_level)
    logging.getLogger("httpx").setLevel(third_party_level)
    logging.getLogger("httpcore").setLevel(third_party_level)
    
    # 로깅 설정 완료 메시지
    env_info = f"Environment: {settings.ENVIRONMENT}"
    if settings.is_production():
        env_info += " (PRODUCTION)"
    elif settings.DEBUG:
        env_info += " (DEBUG MODE)"
    
    logging.info(
        f"✅ Logging configured. Level: {level}, {env_info}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    모듈별 로거를 가져옵니다.
    
    Args:
        name: 로거 이름 (보통 __name__ 사용)
        
    Returns:
        설정된 로거 인스턴스
    """
    return logging.getLogger(name)


# 기본 로거 (하위 호환성)
# 주의: setup_logging()은 main.py에서 명시적으로 호출해야 합니다.
logger = get_logger("moby")
