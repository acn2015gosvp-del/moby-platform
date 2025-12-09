"""
메신저 알림 서비스 (Slack, Telegram)

Grafana Webhook 알림을 Slack 또는 Telegram으로 전송합니다.
"""

import httpx
import json
from typing import Dict, Any, Optional
from backend.api.services.schemas.models.core.logger import get_logger
from backend.api.services.schemas.models.core.config import settings

logger = get_logger(__name__)


async def send_slack_notification(
    message: str,
    alert_type: str = "CRITICAL",
    device_id: Optional[str] = None,
    webhook_url: Optional[str] = None
) -> bool:
    """
    Slack Webhook을 통해 알림을 전송합니다.
    
    Args:
        message: 전송할 메시지
        alert_type: 알림 타입 (CRITICAL, WARNING, RESOLVED)
        device_id: 디바이스 ID
        webhook_url: Slack Webhook URL (없으면 환경변수에서 가져옴)
        
    Returns:
        전송 성공 여부
    """
    try:
        # Webhook URL 확인
        slack_webhook_url = webhook_url or getattr(settings, 'SLACK_WEBHOOK_URL', None)
        if not slack_webhook_url:
            logger.debug("Slack Webhook URL이 설정되지 않았습니다. 알림을 건너뜁니다.")
            return False
        
        # Slack 메시지 포맷 구성
        # 색상 설정 (타입에 따라)
        color_map = {
            "CRITICAL": "#dc2626",  # 빨간색
            "WARNING": "#f59e0b",   # 주황색
            "RESOLVED": "#10b981"   # 초록색
        }
        color = color_map.get(alert_type, "#6b7280")
        
        # 이모지 설정
        emoji_map = {
            "CRITICAL": "🚨",
            "WARNING": "⚠️",
            "RESOLVED": "✅"
        }
        emoji = emoji_map.get(alert_type, "ℹ️")
        
        # Slack 메시지 페이로드
        payload = {
            "text": f"{emoji} MOBY 알림",
            "attachments": [
                {
                    "color": color,
                    "title": f"{emoji} {alert_type}",
                    "text": message,
                    "fields": [
                        {
                            "title": "디바이스",
                            "value": device_id or "Unknown",
                            "short": True
                        },
                        {
                            "title": "타입",
                            "value": alert_type,
                            "short": True
                        }
                    ],
                    "footer": "MOBY Platform",
                    "ts": int(__import__('time').time())
                }
            ]
        }
        
        # HTTP 요청 전송
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                slack_webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
        logger.info(f"✅ Slack 알림 전송 성공: {alert_type} - {message[:50]}")
        return True
        
    except httpx.HTTPError as e:
        logger.error(f"❌ Slack 알림 전송 실패 (HTTP): {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Slack 알림 전송 실패: {e}", exc_info=True)
        return False


async def send_telegram_notification(
    message: str,
    alert_type: str = "CRITICAL",
    device_id: Optional[str] = None,
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None
) -> bool:
    """
    Telegram Bot API를 통해 알림을 전송합니다.
    
    Args:
        message: 전송할 메시지
        alert_type: 알림 타입 (CRITICAL, WARNING, RESOLVED)
        device_id: 디바이스 ID
        bot_token: Telegram Bot Token (없으면 환경변수에서 가져옴)
        chat_id: Telegram Chat ID (없으면 환경변수에서 가져옴)
        
    Returns:
        전송 성공 여부
    """
    try:
        # Bot Token과 Chat ID 확인
        telegram_bot_token = bot_token or getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        telegram_chat_id = chat_id or getattr(settings, 'TELEGRAM_CHAT_ID', None)
        
        if not telegram_bot_token or not telegram_chat_id:
            logger.debug("Telegram Bot Token 또는 Chat ID가 설정되지 않았습니다. 알림을 건너뜁니다.")
            return False
        
        # 이모지 설정
        emoji_map = {
            "CRITICAL": "🚨",
            "WARNING": "⚠️",
            "RESOLVED": "✅"
        }
        emoji = emoji_map.get(alert_type, "ℹ️")
        
        # Telegram 메시지 포맷
        formatted_message = (
            f"{emoji} *{alert_type}*\n\n"
            f"{message}\n\n"
            f"*디바이스:* {device_id or 'Unknown'}\n"
            f"*타입:* {alert_type}"
        )
        
        # Telegram Bot API URL
        api_url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
        
        # HTTP 요청 전송
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                api_url,
                json={
                    "chat_id": telegram_chat_id,
                    "text": formatted_message,
                    "parse_mode": "Markdown"
                },
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
        logger.info(f"✅ Telegram 알림 전송 성공: {alert_type} - {message[:50]}")
        return True
        
    except httpx.HTTPError as e:
        logger.error(f"❌ Telegram 알림 전송 실패 (HTTP): {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Telegram 알림 전송 실패: {e}", exc_info=True)
        return False


async def send_messenger_notifications(
    message: str,
    alert_type: str = "CRITICAL",
    device_id: Optional[str] = None
) -> Dict[str, bool]:
    """
    모든 활성화된 메신저로 알림을 전송합니다.
    
    Args:
        message: 전송할 메시지
        alert_type: 알림 타입 (CRITICAL, WARNING, RESOLVED)
        device_id: 디바이스 ID
        
    Returns:
        각 메신저별 전송 결과 딕셔너리
    """
    results = {}
    
    # Slack 알림 전송
    try:
        results['slack'] = await send_slack_notification(
            message=message,
            alert_type=alert_type,
            device_id=device_id
        )
    except Exception as e:
        logger.error(f"Slack 알림 전송 중 예외 발생: {e}", exc_info=True)
        results['slack'] = False
    
    # Telegram 알림 전송
    try:
        results['telegram'] = await send_telegram_notification(
            message=message,
            alert_type=alert_type,
            device_id=device_id
        )
    except Exception as e:
        logger.error(f"Telegram 알림 전송 중 예외 발생: {e}", exc_info=True)
        results['telegram'] = False
    
    return results

