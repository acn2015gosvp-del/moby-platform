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
    
    Args:
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 로그 파일 경로 (None이면 파일 로깅 안 함)
        log_format: 로그 포맷 문자열
    """
    # 로그 레벨 결정
    level = log_level or settings.LOG_LEVEL or "INFO"
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
    
    # 서드파티 라이브러리 로그 레벨 조정
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("paho").setLevel(logging.WARNING)
    logging.getLogger("influxdb_client").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    
    logging.info(
        f"✅ Logging configured. Level: {level}, "
        f"Environment: {settings.ENVIRONMENT}, "
        f"Debug: {settings.DEBUG}"
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
