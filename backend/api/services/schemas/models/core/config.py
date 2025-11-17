"""
환경 설정 관리 모듈

.env 파일에서 환경 변수를 로드하고 검증합니다.
환경별 설정 분리를 지원합니다.
"""

import os
import logging
from pathlib import Path
from typing import Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    # Pydantic v1 호환성
    from pydantic import BaseSettings
    SettingsConfigDict = None

logger = logging.getLogger(__name__)


def _get_env_file() -> Optional[str]:
    """
    환경에 따라 .env 파일 경로를 결정합니다.
    
    우선순위:
    1. .env.{ENVIRONMENT} (예: .env.dev, .env.prod)
    2. .env
    3. None (환경 변수만 사용)
    """
    env = os.getenv("ENVIRONMENT", "dev").lower()
    project_root = Path(__file__).parent.parent.parent.parent.parent
    
    # .env.{environment} 파일 확인
    env_file = project_root / f".env.{env}"
    if env_file.exists():
        logger.info(f"Loading environment file: .env.{env}")
        return str(env_file)
    
    # .env 파일 확인
    env_file = project_root / ".env"
    if env_file.exists():
        logger.info("Loading environment file: .env")
        return str(env_file)
    
    logger.warning(
        "No .env file found. Using environment variables and defaults only."
    )
    return None


class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스
    
    환경 변수 또는 .env 파일에서 설정을 로드합니다.
    """
    
    # 환경 설정
    ENVIRONMENT: str = "dev"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # MQTT 설정
    MQTT_HOST: str = "localhost"
    MQTT_PORT: int = 1883
    
    # InfluxDB 설정
    INFLUX_URL: str = "http://localhost:8086"
    INFLUX_TOKEN: str = ""
    INFLUX_ORG: str = ""
    INFLUX_BUCKET: str = "moby-data"
    
    # OpenAI API 설정
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # 인증 설정
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Pydantic v2 설정
    if SettingsConfigDict:
        model_config = SettingsConfigDict(
            env_file=_get_env_file(),
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore",  # 추가 필드는 무시
        )
    else:
        # Pydantic v1 호환성
        class Config:
            env_file = _get_env_file()
            env_file_encoding = "utf-8"
            case_sensitive = False
            extra = "ignore"
    
    def validate_settings(self) -> list[str]:
        """
        설정값을 검증하고 문제가 있는 필드를 반환합니다.
        
        Returns:
            문제가 있는 필드 이름 리스트
        """
        issues = []
        
        # 필수 설정 검증
        if not self.INFLUX_TOKEN or self.INFLUX_TOKEN == "your-token":
            issues.append("INFLUX_TOKEN")
        
        if not self.INFLUX_ORG or self.INFLUX_ORG == "your-org":
            issues.append("INFLUX_ORG")
        
        if not self.OPENAI_API_KEY or self.OPENAI_API_KEY == "your-api-key":
            issues.append("OPENAI_API_KEY")
        
        # URL 형식 검증
        if not self.INFLUX_URL.startswith(("http://", "https://")):
            issues.append("INFLUX_URL")
        
        # 포트 범위 검증
        if not (1 <= self.MQTT_PORT <= 65535):
            issues.append("MQTT_PORT")
        
        return issues
    
    def is_production(self) -> bool:
        """프로덕션 환경인지 확인"""
        return self.ENVIRONMENT.lower() in ("prod", "production")
    
    def is_development(self) -> bool:
        """개발 환경인지 확인"""
        return self.ENVIRONMENT.lower() in ("dev", "development")
    
    def is_testing(self) -> bool:
        """테스트 환경인지 확인"""
        return self.ENVIRONMENT.lower() in ("test", "testing")


# 설정 인스턴스 생성
settings = Settings()

# 설정 검증 및 경고
validation_issues = settings.validate_settings()
if validation_issues:
    logger.warning(
        f"⚠️ Configuration issues detected: {', '.join(validation_issues)}. "
        f"Please check your .env file or environment variables."
    )
    
    if settings.is_production():
        logger.error(
            f"❌ Critical configuration issues in production environment: "
            f"{', '.join(validation_issues)}"
        )
else:
    logger.info(
        f"✅ Configuration loaded successfully. "
        f"Environment: {settings.ENVIRONMENT}, "
        f"Debug: {settings.DEBUG}"
    )
