"""
알림 전송 서비스

Track A (Grafana)와 Track B (AI Model)에서 받은 알림을
WebSocket을 통해 React 프론트엔드로 전송합니다.
"""

import logging
from typing import Dict, Any
import asyncio

from backend.api.services.websocket_notifier import get_websocket_notifier
from backend.api.services.schemas.models.core.logger import get_logger

logger = get_logger(__name__)


def send_alert(alert_payload: Dict[str, Any]) -> bool:
    """
    Alert Engine에서 생성된 페이로드를 받아서 WebSocket으로 전송합니다.
    
    Track B (AI Model)에서 생성된 알림을 React 프론트엔드로 실시간 전송합니다.
    우선순위 로직(Critical > Warning > Info)이 이미 적용된 상태로 전송됩니다.
    
    Args:
        alert_payload: 전송할 알림 페이로드
        
    Returns:
        전송 성공 여부 (bool)
    """
    try:
        alert_id = alert_payload.get('id', 'N/A')
        alert_level = alert_payload.get('level', 'UNKNOWN')
        
        logger.info(f"📤 알림 전송 시작 (Track B): ID={alert_id}, Level={alert_level}")
        
        # WebSocket Notifier 가져오기
        notifier = get_websocket_notifier()
        
        # 비동기 함수를 동기 컨텍스트에서 실행
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 이미 실행 중인 이벤트 루프가 있으면 태스크로 실행
                asyncio.create_task(notifier.send_alert(alert_payload))
                logger.info(f"🚨 알림 전송 큐에 추가됨 (Track B): ID={alert_id}, Level={alert_level}")
                return True
            else:
                # 이벤트 루프가 없으면 실행
                success = loop.run_until_complete(notifier.send_alert(alert_payload))
                return success
        except RuntimeError:
            # 이벤트 루프가 없는 경우 새로 생성
            success = asyncio.run(notifier.send_alert(alert_payload))
            return success
            
    except Exception as e:
        logger.error(
            f"❌ 알림 전송 실패 (Track B): ID={alert_payload.get('id', 'N/A')}, Error: {e}",
            exc_info=True
        )
        return False