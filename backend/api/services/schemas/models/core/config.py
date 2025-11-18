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
    
    # 프로젝트 루트 찾기
    # config.py 위치: backend/api/services/schemas/models/core/config.py
    # 프로젝트 루트까지: core -> models -> schemas -> services -> api -> backend -> project_root (6단계)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent.parent.parent
    
    # 프로젝트 루트 확인 (backend 폴더가 있는지 확인)
    if not (project_root / "backend").exists():
        # 한 단계 더 올라가기
        project_root = project_root.parent
    
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
    
    # Grafana 설정 (선택사항)
    GRAFANA_URL: str = ""
    GRAFANA_API_KEY: str = ""
    
    # OpenAI API 설정
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # Gemini API 설정 (보고서 생성용)
    GEMINI_API_KEY: str = ""
    
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
    
    def validate_settings(self) -> tuple[list[str], list[str]]:
        """
        설정값을 검증하고 문제가 있는 필드를 반환합니다.
        
        Returns:
            (critical_issues, warning_issues): (치명적 문제 리스트, 경고 문제 리스트)
        """
        critical_issues = []
        warning_issues = []
        
        # 프로덕션 환경 필수 설정 검증
        if self.is_production():
            # SECRET_KEY 검증 (프로덕션에서 기본값 사용 시 치명적)
            if not self.SECRET_KEY or self.SECRET_KEY in (
                "your-secret-key-change-in-production",
                "your-secret-key-here-change-this-in-production",
                "change-this-in-production"
            ):
                critical_issues.append("SECRET_KEY (프로덕션 환경에서 기본값 사용 금지)")
            
            # InfluxDB 필수 설정
            if not self.INFLUX_TOKEN or self.INFLUX_TOKEN in ("your-token", "your-influxdb-token-here"):
                critical_issues.append("INFLUX_TOKEN")
            
            if not self.INFLUX_ORG or self.INFLUX_ORG in ("your-org", "your-influxdb-org-here"):
                critical_issues.append("INFLUX_ORG")
            
            # URL 형식 검증
            if not self.INFLUX_URL.startswith(("http://", "https://")):
                critical_issues.append("INFLUX_URL (올바른 URL 형식이 아님)")
            
            # 포트 범위 검증
            if not (1 <= self.MQTT_PORT <= 65535):
                critical_issues.append("MQTT_PORT (유효하지 않은 포트 번호)")
        
        # 개발 환경 경고 검증
        else:
            if not self.INFLUX_TOKEN or self.INFLUX_TOKEN in ("your-token", "your-influxdb-token-here"):
                warning_issues.append("INFLUX_TOKEN (일부 기능이 제한될 수 있음)")
            
            if not self.INFLUX_ORG or self.INFLUX_ORG in ("your-org", "your-influxdb-org-here"):
                warning_issues.append("INFLUX_ORG (일부 기능이 제한될 수 있음)")
            
            if not self.INFLUX_URL.startswith(("http://", "https://")):
                warning_issues.append("INFLUX_URL (올바른 URL 형식이 아님)")
            
            if not (1 <= self.MQTT_PORT <= 65535):
                warning_issues.append("MQTT_PORT (유효하지 않은 포트 번호)")
        
        # 공통 검증 (모든 환경)
        if not self.OPENAI_API_KEY or self.OPENAI_API_KEY in ("your-api-key", "your-openai-api-key-here"):
            warning_issues.append("OPENAI_API_KEY (LLM 기능 사용 불가)")
        
        # SECRET_KEY 기본값 경고 (개발 환경)
        if not self.is_production() and self.SECRET_KEY in (
            "your-secret-key-change-in-production",
            "your-secret-key-here-change-this-in-production",
            "change-this-in-production"
        ):
            warning_issues.append("SECRET_KEY (기본값 사용 중 - 프로덕션 배포 전 변경 필요)")
        
        return critical_issues, warning_issues
    
    def validate_and_raise(self) -> None:
        """
        설정을 검증하고 프로덕션 환경에서 치명적 문제가 있으면 예외를 발생시킵니다.
        
        Raises:
            ValueError: 프로덕션 환경에서 필수 설정이 누락된 경우
        """
        critical_issues, warning_issues = self.validate_settings()
        
        if critical_issues:
            error_msg = (
                f"❌ 프로덕션 환경에서 필수 설정이 누락되었습니다:\n"
                f"   {', '.join(critical_issues)}\n\n"
                f"   .env 파일을 확인하고 필수 환경 변수를 설정하세요.\n"
                f"   참고: env.example 파일을 참고하세요."
            )
            raise ValueError(error_msg)
        
        if warning_issues:
            logger.warning(
                f"⚠️ 설정 경고: {', '.join(warning_issues)}. "
                f"일부 기능이 제한될 수 있습니다."
            )
    
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

# 설정 검증 및 경고 (애플리케이션 시작 시 자동 검증)
# 프로덕션 환경에서는 validate_and_raise()를 main.py에서 호출하여
# 치명적 문제 시 애플리케이션 시작을 중단합니다.
critical_issues, warning_issues = settings.validate_settings()
if critical_issues:
    if settings.is_production():
        # 프로덕션 환경에서는 main.py에서 validate_and_raise()를 호출하여
        # 예외를 발생시킵니다. 여기서는 로깅만 합니다.
        logger.error(
            f"❌ 프로덕션 환경에서 필수 설정 누락: {', '.join(critical_issues)}"
        )
    else:
        logger.warning(
            f"⚠️ 설정 문제 감지: {', '.join(critical_issues)}. "
            f"프로덕션 배포 전 수정이 필요합니다."
        )

if warning_issues:
    logger.warning(
        f"⚠️ 설정 경고: {', '.join(warning_issues)}. "
        f"일부 기능이 제한될 수 있습니다."
    )

if not critical_issues and not warning_issues:
    logger.info(
        f"✅ 설정 검증 완료. "
        f"Environment: {settings.ENVIRONMENT}, "
        f"Debug: {settings.DEBUG}"
    )
