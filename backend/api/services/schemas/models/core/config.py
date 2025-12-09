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


def _normalize_env_file_encoding_once(env_file_path: Path) -> bool:
    """
    .env 파일을 UTF-8 (BOM 없음)로 정규화합니다 (한 번만 실행).
    정규화 플래그 파일을 확인하여 이미 정규화된 경우 건너뜁니다.
    최적화: 빠른 플래그 체크로 불필요한 작업 방지.
    
    Args:
        env_file_path: .env 파일 경로
        
    Returns:
        정규화가 필요한 경우 True, 이미 UTF-8인 경우 False
    """
    # 파일이 없으면 즉시 반환
    if not env_file_path.exists():
        return False
    
    # 정규화 플래그 파일 경로
    flag_file = env_file_path.with_suffix('.env.normalized')
    
    # 이미 정규화된 경우 건너뛰기 (빠른 체크)
    try:
        if flag_file.exists():
            # 플래그 파일이 있고, .env 파일이 최신이면 정규화 건너뛰기
            flag_mtime = flag_file.stat().st_mtime
            env_mtime = env_file_path.stat().st_mtime
            if flag_mtime >= env_mtime:
                # 이미 정규화됨 - 로그 출력 제거 (빠른 시작)
                return False
    except (OSError, IOError):
        # 파일 시스템 오류 시 정규화 시도 (안전)
        pass
    
    # 정규화 실행 (필요한 경우에만)
    result = _normalize_env_file_encoding(env_file_path)
    
    # 정규화 성공 시 플래그 파일 생성
    if result:
        try:
            flag_file.touch()
            logger.debug(f"정규화 플래그 파일 생성: {flag_file.name}")
        except Exception as e:
            logger.warning(f"정규화 플래그 파일 생성 실패: {e}")
    
    return result


def _normalize_env_file_encoding(env_file_path: Path) -> bool:
    """
    .env 파일을 UTF-8 (BOM 없음)로 정규화합니다.
    중요한 환경 변수(API 키 등)가 손상되지 않도록 검증합니다.
    최적화: UTF-8 먼저 확인하여 빠른 경로 제공.
    
    Args:
        env_file_path: .env 파일 경로
        
    Returns:
        정규화가 필요한 경우 True, 이미 UTF-8인 경우 False
    """
    if not env_file_path.exists():
        return False
    
    try:
        # UTF-8 먼저 확인 (가장 일반적인 경우, 빠른 경로)
        content = None
        used_encoding = None
        
        # 먼저 UTF-8로 빠르게 시도
        try:
            with open(env_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            used_encoding = 'utf-8'
            
            # BOM 확인 (UTF-8이지만 BOM이 있는 경우만 정규화)
            if content.startswith('\ufeff'):
                # BOM 제거만 필요
                pass
            else:
                # 이미 UTF-8이고 BOM도 없음 - 정규화 불필요
                return False
                
        except (UnicodeDecodeError, UnicodeError):
            # UTF-8이 아니면 다른 인코딩 시도
            for encoding in ['utf-8-sig', 'latin-1', 'cp949', 'euc-kr']:
                try:
                    with open(env_file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    used_encoding = encoding
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
        
        if content is None:
            logger.warning(f"Could not decode .env file with any encoding: {env_file_path}")
            return False
        
        # 중요한 환경 변수 추출 (검증용)
        # API 키와 토큰은 인코딩 변환 시 손상되면 안 되므로 사전에 추출
        sensitive_keys = ['GEMINI_API_KEY', 'INFLUX_TOKEN', 'GRAFANA_API_KEY', 'SECRET_KEY']
        original_values = {}
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                # 주석 제거 (값에 #이 있을 수 있으므로 주의)
                if ' #' in line:
                    line = line[:line.index(' #')]
                key = line.split('=', 1)[0].strip()
                if key in sensitive_keys:
                    value = line.split('=', 1)[1].strip().strip('"').strip("'")
                    original_values[key] = value
                    logger.debug(f"Extracted {key} for verification (length: {len(value)})")
        
        # UTF-8 (BOM 없음)로 다시 저장
        needs_conversion = used_encoding not in ['utf-8', 'utf-8-sig']
        has_bom = content.startswith('\ufeff')
        
        if needs_conversion or has_bom:
            # 변환 전 백업 생성 (중요 값 손상 방지)
            import shutil
            from datetime import datetime
            
            backup_path = env_file_path.with_suffix(f'.env.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            try:
                shutil.copy2(env_file_path, backup_path)
                logger.info(f"📦 백업 생성: {backup_path.name}")
            except Exception as e:
                logger.error(f"❌ 백업 생성 실패: {e}")
                return False  # 백업 실패 시 변환 중단
            
            # BOM 제거
            if has_bom:
                content = content[1:]
            
            # UTF-8로 저장
            try:
                with open(env_file_path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(content)
                logger.debug(f"임시로 UTF-8로 저장 완료")
            except Exception as e:
                logger.error(f"❌ 파일 저장 실패: {e}")
                # 저장 실패 시 백업에서 복원
                try:
                    shutil.copy2(backup_path, env_file_path)
                    logger.warning(f"백업에서 복원: {backup_path.name}")
                except Exception as restore_error:
                    logger.error(f"복원 실패: {restore_error}")
                return False
            
            # 변환 후 검증: 중요한 값이 손상되지 않았는지 확인
            verification_passed = True
            corrupted_keys = []
            
            # 변환된 파일 다시 읽기
            try:
                with open(env_file_path, 'r', encoding='utf-8') as f:
                    converted_content = f.read()
            except Exception as e:
                logger.error(f"변환된 파일 읽기 실패: {e}")
                verification_passed = False
                converted_content = content
            
            for key, original_value in original_values.items():
                # 변환 후 값 추출
                new_value = None
                for line in converted_content.split('\n'):
                    line_stripped = line.strip()
                    if line_stripped.startswith(f"{key}="):
                        # 주석 제거
                        if ' #' in line_stripped:
                            line_stripped = line_stripped[:line_stripped.index(' #')]
                        new_value = line_stripped.split('=', 1)[1].strip().strip('"').strip("'")
                        break
                
                if new_value is None:
                    logger.warning(f"⚠️ {key}를 변환된 파일에서 찾을 수 없습니다")
                    corrupted_keys.append(key)
                    verification_passed = False
                elif new_value != original_value:
                    logger.error(
                        f"❌ {key} 값이 변환 중 손상되었습니다!\n"
                        f"   원본 길이: {len(original_value)}자\n"
                        f"   변환 후 길이: {len(new_value)}자\n"
                        f"   원본 앞 10자: {original_value[:10]}...\n"
                        f"   변환 후 앞 10자: {new_value[:10]}..."
                    )
                    corrupted_keys.append(key)
                    verification_passed = False
                else:
                    logger.debug(f"✅ {key} 검증 통과 (길이: {len(original_value)}자)")
            
            if not verification_passed:
                # 손상된 키가 있으면 백업에서 복원
                logger.error(
                    f"❌ 인코딩 변환 중 중요 값이 손상되었습니다!\n"
                    f"   손상된 키: {', '.join(corrupted_keys)}\n"
                    f"   백업에서 자동 복원합니다..."
                )
                try:
                    shutil.copy2(backup_path, env_file_path)
                    logger.warning(f"✅ 백업에서 복원 완료: {backup_path.name}")
                    logger.warning(f"   원본 인코딩({used_encoding})을 유지합니다.")
                    # 백업 파일은 유지 (수동 확인용)
                    return False
                except Exception as e:
                    logger.error(f"❌ 백업 복원 실패: {e}")
                    logger.error(f"   수동으로 {backup_path.name}을 .env로 복사하세요!")
                    return False
            
            # 검증 통과 시
            if needs_conversion:
                logger.info(f"✅ .env 파일 인코딩 변환 완료: {used_encoding} → UTF-8")
            if has_bom:
                logger.info(f"✅ BOM 제거 완료")
            
            # 모든 중요 값 검증 통과
            logger.info(f"✅ 모든 중요 환경 변수 검증 통과 ({len(original_values)}개)")
            
            # 정규화 플래그 파일 생성 (성공 시)
            try:
                flag_file = env_file_path.with_suffix('.env.normalized')
                flag_file.touch()
                logger.debug(f"정규화 플래그 파일 생성: {flag_file.name}")
            except Exception as e:
                logger.warning(f"정규화 플래그 파일 생성 실패: {e}")
            
            # 백업 파일 정리 (성공 시, 최신 백업만 유지)
            try:
                # 같은 이름 패턴의 오래된 백업 파일 삭제
                backup_dir = backup_path.parent
                backup_pattern = env_file_path.stem + '.env.backup.*'
                import glob
                old_backups = sorted(glob.glob(str(backup_dir / backup_pattern)), reverse=True)
                # 최신 3개만 유지하고 나머지 삭제
                for old_backup in old_backups[3:]:
                    try:
                        Path(old_backup).unlink()
                        logger.debug(f"오래된 백업 삭제: {Path(old_backup).name}")
                    except Exception:
                        pass
            except Exception:
                pass  # 백업 정리 실패해도 계속 진행
            
            return True
        
        return False
        
    except Exception as e:
        logger.warning(f"Failed to normalize .env file encoding: {e}")
        return False


def _get_env_file() -> Optional[str]:
    """
    환경에 따라 .env 파일 경로를 결정하고 인코딩을 정규화합니다.
    
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
        _normalize_env_file_encoding_once(env_file)
        logger.info(f"Loading environment file: .env.{env}")
        return str(env_file)
    
    # .env 파일 확인
    env_file = project_root / ".env"
    if env_file.exists():
        _normalize_env_file_encoding_once(env_file)
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
    
    # OpenAI API 설정 (사용 안 함 - Gemini API로 대체됨)
    # 알람 및 보고서 생성은 모두 Gemini API를 사용합니다.
    # OPENAI_API_KEY: str = ""
    # OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # Gemini API 설정 (보고서 생성 및 알림 요약용)
    GEMINI_API_KEY: str = ""
    
    # 메신저 알림 설정 (선택사항)
    SLACK_WEBHOOK_URL: Optional[str] = None  # Slack Webhook URL
    TELEGRAM_BOT_TOKEN: Optional[str] = None  # Telegram Bot Token
    TELEGRAM_CHAT_ID: Optional[str] = None  # Telegram Chat ID
    
    # 이메일 알림 설정 (선택사항)
    SMTP_HOST: Optional[str] = None  # SMTP 서버 주소 (예: smtp.gmail.com)
    SMTP_PORT: int = 587  # SMTP 포트 (기본값: 587)
    SMTP_USER: Optional[str] = None  # SMTP 인증 사용자명
    SMTP_PASSWORD: Optional[str] = None  # SMTP 인증 비밀번호
    SMTP_FROM_EMAIL: Optional[str] = None  # 발신자 이메일
    SMTP_TO_EMAILS: Optional[str] = None  # 수신자 이메일 (쉼표로 구분, 예: "admin@example.com,ops@example.com")
    
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
        # OpenAI는 더 이상 사용하지 않음 (Gemini API로 완전 대체)
        # 알람 및 보고서 생성은 모두 Gemini API를 사용합니다.
        
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
