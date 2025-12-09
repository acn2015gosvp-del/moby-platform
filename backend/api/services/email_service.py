"""
알림 이메일 발송 서비스

CRITICAL, ERROR, WARNING 알림 발생 시 즉시 이메일 발송
"""

import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
from dataclasses import dataclass

from backend.api.services.schemas.models.core.logger import get_logger
from backend.api.services.schemas.models.core.config import settings

logger = get_logger(__name__)


@dataclass
class Alert:
    """알림 데이터 클래스"""
    alert_type: str  # CRITICAL, ERROR, WARNING
    message: str
    source: str  # 센서 ID
    timestamp: datetime
    severity: int  # 1(낮음) ~ 5(높음)


class AlertThrottler:
    """알림 폭주 방지 - 5분 이내 동일 소스 반복 제한"""

    def __init__(self, throttle_window: int = 300):  # 5분 = 300초
        self.throttle_window = throttle_window
        # 소스별 마지막 발송 시각 및 누적 알림 저장
        self.last_sent: Dict[str, datetime] = {}
        self.pending_alerts: Dict[str, List[Alert]] = defaultdict(list)

    def should_send(self, alert: Alert) -> tuple[bool, Optional[List[Alert]]]:
        """
        알림을 발송해야 하는지 확인

        Returns:
            (발송 여부, 함께 보낼 누적 알림 리스트)
        """
        now = datetime.now()
        source = alert.source

        # 첫 번째 알림이거나 Throttle 윈도우를 벗어난 경우
        if source not in self.last_sent:
            self.last_sent[source] = now
            logger.info(f"[Throttle] {source}: 첫 번째 알림 - 즉시 발송")
            return True, [alert]

        time_diff = (now - self.last_sent[source]).total_seconds()

        # 5분이 지났으면 누적된 알림과 함께 발송
        if time_diff >= self.throttle_window:
            self.last_sent[source] = now
            accumulated = self.pending_alerts[source] + [alert]
            self.pending_alerts[source] = []
            logger.info(f"[Throttle] {source}: Throttle 윈도우 경과 ({time_diff:.1f}초) - 누적 알림 {len(accumulated)}건 발송")
            return True, accumulated

        # 5분 이내면 누적만 하고 발송 안함
        self.pending_alerts[source].append(alert)
        logger.info(f"[Throttle] {source}: 알림 누적 중 ({len(self.pending_alerts[source])}개, 마지막 발송 후 {time_diff:.1f}초 경과)")
        return False, None

    def cleanup_old_entries(self):
        """오래된 항목 정리 (메모리 관리)"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.throttle_window * 2)

        # 오래된 항목 삭제
        sources_to_remove = [
            source for source, last_time in self.last_sent.items()
            if last_time < cutoff
        ]

        for source in sources_to_remove:
            del self.last_sent[source]
            if source in self.pending_alerts:
                del self.pending_alerts[source]


class AlertEmailService:
    """알림 이메일 발송 서비스"""

    # 이상 이벤트로 분류할 알림 타입
    ABNORMAL_TYPES = {'CRITICAL', 'ERROR', 'WARNING'}

    # 타입별 이모지 매핑
    TYPE_EMOJI = {
        'CRITICAL': '🚨',
        'ERROR': '❌',
        'WARNING': '⚠️'
    }

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        to_emails: List[str],
        max_retries: int = 3,
        throttle_window: int = 300
    ):
        """
        Args:
            smtp_host: SMTP 서버 주소 (예: smtp.gmail.com)
            smtp_port: SMTP 포트 (예: 587)
            smtp_user: SMTP 인증 사용자명
            smtp_password: SMTP 인증 비밀번호
            from_email: 발신자 이메일
            to_emails: 수신자 이메일 리스트 (운영팀 그룹)
            max_retries: 최대 재시도 횟수
            throttle_window: Throttle 윈도우 (초)
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.to_emails = to_emails
        self.max_retries = max_retries

        self.throttler = AlertThrottler(throttle_window)

        logger.info(f"AlertEmailService 초기화: {smtp_host}:{smtp_port}")
        logger.info(f"수신자: {', '.join(to_emails)}")

    def is_abnormal_event(self, alert: Alert) -> bool:
        """이상 이벤트 여부 확인"""
        return alert.alert_type in self.ABNORMAL_TYPES

    def compose_email_body(self, alerts: List[Alert]) -> str:
        """
        이메일 본문 구성

        단일 알림 또는 누적된 알림들을 포함하는 본문 생성
        """
        if len(alerts) == 1:
            # 단일 알림
            alert = alerts[0]
            emoji = self.TYPE_EMOJI.get(alert.alert_type, '📢')
            timestamp_str = alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')

            body = f"""
{emoji} 긴급 알림 발생
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 발생 시각: {timestamp_str}
🏷️  타입: {alert.alert_type}
📍 소스: {alert.source}
💬 메시지: {alert.message}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
즉시 조치가 필요할 수 있습니다.
시스템 대시보드를 확인해주세요.

※ 본 메일은 자동 발송되었습니다.
            """

        else:
            # 누적된 알림들
            first_alert = alerts[0]
            emoji = self.TYPE_EMOJI.get(first_alert.alert_type, '📢')
            source = first_alert.source

            body = f"""
{emoji} 긴급 알림 다건 발생 (5분 이내 {len(alerts)}건)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 소스: {source}
🔢 알림 건수: {len(alerts)}건
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

            for i, alert in enumerate(alerts, 1):
                timestamp_str = alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                body += f"""
[{i}] {timestamp_str}
   타입: {alert.alert_type}
   메시지: {alert.message}

"""

            body += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
동일 소스에서 짧은 시간에 여러 알림이 발생했습니다.
시스템 점검이 필요할 수 있습니다.

※ 본 메일은 자동 발송되었습니다.
            """

        return body.strip()

    def compose_email_subject(self, alerts: List[Alert]) -> str:
        """이메일 제목 구성"""
        if len(alerts) == 1:
            alert = alerts[0]
            emoji = self.TYPE_EMOJI.get(alert.alert_type, '📢')
            timestamp_str = alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            return f"{emoji} [긴급 알림] [{timestamp_str}] {alert.source} - {alert.message[:30]}"
        else:
            first_alert = alerts[0]
            emoji = self.TYPE_EMOJI.get(first_alert.alert_type, '📢')
            return f"{emoji} [긴급 알림 x{len(alerts)}] {first_alert.source} - 다건 발생"

    async def send_email_with_retry(self, alert: Alert) -> bool:
        """
        이메일 발송 (재시도 로직 포함)

        Returns:
            발송 성공 여부
        """
        # Throttling 확인
        should_send, alerts_to_send = self.throttler.should_send(alert)

        if not should_send:
            # Throttle 상태: 알림이 누적되었지만 아직 발송하지 않음
            logger.debug(f"📧 [이메일] Throttle 상태: {alert.source} - 알림 누적 중, 발송 대기 중")
            return True  # Throttle 상태는 에러가 아님
        
        # alerts_to_send가 None이면 발송하지 않음
        if alerts_to_send is None or len(alerts_to_send) == 0:
            logger.warning(f"⚠️ [이메일] 발송할 알림이 없습니다: {alert.source}")
            return False

        # 재시도 로직
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"📧 [이메일] 발송 시도 {attempt}/{self.max_retries}: {alert.source}")
                success = await self._send_email(alerts_to_send)
                if success:
                    logger.info(f"✅ 이메일 발송 성공: {alert.source} ({len(alerts_to_send)}건)")
                    return True
                else:
                    logger.warning(f"⚠️ 이메일 발송 실패 (시도 {attempt}/{self.max_retries}): success=False")

            except smtplib.SMTPAuthenticationError as e:
                last_exception = e
                logger.error(
                    f"❌ 이메일 발송 실패 (인증 오류, 시도 {attempt}/{self.max_retries}): {e}\n"
                    f"   호스트: {self.smtp_host}:{self.smtp_port}\n"
                    f"   사용자: {self.smtp_user}\n"
                    f"   가능한 원인: 잘못된 사용자명 또는 비밀번호"
                )
                # 인증 오류는 재시도하지 않음
                break
            except smtplib.SMTPConnectError as e:
                last_exception = e
                logger.error(
                    f"❌ 이메일 발송 실패 (연결 오류, 시도 {attempt}/{self.max_retries}): {e}\n"
                    f"   호스트: {self.smtp_host}:{self.smtp_port}\n"
                    f"   가능한 원인: SMTP 서버가 실행되지 않았거나 네트워크 문제"
                )
            except Exception as e:
                last_exception = e
                logger.error(
                    f"❌ 이메일 발송 실패 (시도 {attempt}/{self.max_retries}): {e}",
                    exc_info=True
                )

            if attempt < self.max_retries:
                # 지수 백오프: 2초, 4초, 8초
                wait_time = 2 ** attempt
                logger.info(f"⏳ {wait_time}초 후 재시도...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    f"💥 최대 재시도 횟수 초과. 발송 실패: {alert.source}\n"
                    f"   마지막 오류: {last_exception}"
                )
                return False

        return False

    async def _send_email(self, alerts: List[Alert]) -> bool:
        """실제 이메일 발송 (동기 SMTP를 비동기 컨텍스트에서 실행)"""
        try:
            logger.info(f"📧 [이메일] 발송 준비: {len(alerts)}건 알림")
            
            # 이메일 메시지 구성
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = self.compose_email_subject(alerts)

            body = self.compose_email_body(alerts)
            # UTF-8 인코딩 명시 (한글 지원)
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            logger.debug(f"📧 [이메일] 메시지 구성 완료: From={self.from_email}, To={', '.join(self.to_emails)}")

            # SMTP 연결 및 발송 (blocking operation을 executor에서 실행)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._smtp_send, msg)

            return True

        except Exception as e:
            logger.error(f"이메일 발송 중 오류: {e}")
            raise

    def _smtp_send(self, msg: MIMEMultipart):
        """동기 SMTP 발송 (executor에서 실행됨)"""
        try:
            logger.info(f"📧 [SMTP] 연결 시도: {self.smtp_host}:{self.smtp_port}")
            
            # SMTP 연결 (타임아웃 설정)
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                logger.debug(f"📧 [SMTP] 연결 성공: {self.smtp_host}:{self.smtp_port}")
                
                # TLS 시작
                logger.debug(f"📧 [SMTP] STARTTLS 시작...")
                server.starttls()
                logger.debug(f"📧 [SMTP] STARTTLS 완료")
                
                # 로그인
                logger.debug(f"📧 [SMTP] 로그인 시도: {self.smtp_user}")
                server.login(self.smtp_user, self.smtp_password)
                logger.debug(f"📧 [SMTP] 로그인 성공")
                
                # 메시지 발송
                logger.debug(f"📧 [SMTP] 메시지 발송 시작...")
                server.send_message(msg)
                logger.info(f"✅ [SMTP] 메시지 발송 성공")
                
        except smtplib.SMTPAuthenticationError as e:
            logger.error(
                f"❌ [SMTP] 인증 실패: {e}\n"
                f"   호스트: {self.smtp_host}:{self.smtp_port}\n"
                f"   사용자: {self.smtp_user}\n"
                f"   가능한 원인: 잘못된 사용자명 또는 비밀번호"
            )
            raise
        except smtplib.SMTPConnectError as e:
            logger.error(
                f"❌ [SMTP] 연결 실패: {e}\n"
                f"   호스트: {self.smtp_host}:{self.smtp_port}\n"
                f"   가능한 원인: SMTP 서버가 실행되지 않았거나 네트워크 문제"
            )
            raise
        except smtplib.SMTPException as e:
            logger.error(
                f"❌ [SMTP] 오류 발생: {e}\n"
                f"   호스트: {self.smtp_host}:{self.smtp_port}\n"
                f"   사용자: {self.smtp_user}"
            )
            raise
        except Exception as e:
            logger.error(
                f"❌ [SMTP] 예상치 못한 오류: {e}\n"
                f"   호스트: {self.smtp_host}:{self.smtp_port}\n"
                f"   사용자: {self.smtp_user}",
                exc_info=True
            )
            raise

    async def process_alert(self, alert: Alert) -> bool:
        """
        알림 처리 메인 로직

        1. 알림 필터링
        2. 이메일 구성 및 발송
        3. 재시도 및 Throttling 처리

        Returns:
            처리 성공 여부
        """
        # 1. 이상 이벤트 필터링
        if not self.is_abnormal_event(alert):
            logger.debug(f"⚪ 정상 알림, 이메일 발송 안함: {alert.alert_type}")
            return True

        logger.info(f"🔴 이상 이벤트 감지: [{alert.alert_type}] {alert.source} - {alert.message}")

        # 2. 이메일 발송 (재시도 + Throttling)
        success = await self.send_email_with_retry(alert)

        # 3. 주기적으로 Throttler 정리
        self.throttler.cleanup_old_entries()

        return success


# ============================================
# FastAPI 통합 - 싱글톤 매니저
# ============================================

class AlertEmailManager:
    """FastAPI 앱에서 사용할 싱글톤 매니저"""

    _instance = None

    def __init__(self):
        self.service: Optional[AlertEmailService] = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AlertEmailManager()
        return cls._instance

    def initialize(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        to_emails: List[str],
        max_retries: int = 3,
        throttle_window: int = 300
    ):
        """서비스 초기화"""
        self.service = AlertEmailService(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            from_email=from_email,
            to_emails=to_emails,
            max_retries=max_retries,
            throttle_window=throttle_window
        )
        logger.info("AlertEmailManager 초기화 완료")

    async def handle_alert(
        self,
        alert_type: str,
        message: str,
        source: str,
        severity: int = 3
    ) -> bool:
        """
        알림 처리

        Args:
            alert_type: CRITICAL, ERROR, WARNING 등
            message: 알림 메시지
            source: 센서 ID 또는 소스
            severity: 심각도 (1-5)

        Returns:
            처리 성공 여부
        """
        if self.service is None:
            logger.error("AlertEmailService가 초기화되지 않았습니다!")
            return False

        alert = Alert(
            alert_type=alert_type,
            message=message,
            source=source,
            timestamp=datetime.now(),
            severity=severity
        )

        return await self.service.process_alert(alert)


# 전역 매니저 인스턴스
alert_email_manager = AlertEmailManager.get_instance()

