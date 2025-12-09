"""
WebSocket 알림 전송 서비스

React 프론트엔드로 실시간 알림을 WebSocket을 통해 전송합니다.
"""

import json
import logging
from typing import Dict, Any, Set
from fastapi import WebSocket, WebSocketDisconnect
from backend.api.services.schemas.models.core.logger import get_logger

logger = get_logger(__name__)


class WebSocketNotifier:
    """WebSocket 연결 관리 및 알림 전송 클래스"""
    
    def __init__(self):
        """WebSocket 연결을 관리하는 클래스 초기화"""
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        """
        WebSocket 클라이언트를 관리 목록에 추가합니다.
        
        ⚠️ 주의: websocket.accept()는 호출하기 전에 이미 실행되어 있어야 합니다!
        
        Args:
            websocket: 이미 accept()된 WebSocket 인스턴스
        """
        # websocket.accept()는 routes_websocket.py에서 이미 호출됨
        # 여기서는 관리 목록에만 추가
        self.active_connections.add(websocket)
        logger.info(f"WebSocket 클라이언트 등록됨. 총 연결 수: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """
        WebSocket 클라이언트 연결을 제거합니다.
        
        Args:
            websocket: 연결 해제할 WebSocket 인스턴스
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket 클라이언트 연결 해제됨. 총 연결 수: {len(self.active_connections)}")
    
    async def send_all(self, alert_payload: Dict[str, Any]) -> bool:
        """
        모든 연결된 WebSocket 클라이언트에게 알림을 전송합니다.
        
        이 메서드는 모든 활성 WebSocket 연결에 동시에 알림을 브로드캐스트합니다.
        
        Args:
            alert_payload: 전송할 알림 페이로드 (dict)
                - type: "CRITICAL" | "WARNING" | "RESOLVED"
                - message: 알림 메시지 (str)
                - color: 색상 (str, optional)
                - device_id: 디바이스 ID (str, optional)
                - timestamp: 타임스탬프 (str, optional)
            
        Returns:
            전송 성공 여부 (최소 한 명에게라도 전송되면 True)
        """
        alert_type = alert_payload.get('type', 'UNKNOWN')
        alert_message = alert_payload.get('message', 'N/A')[:50]
        
        logger.info(
            f"🚀 [WebSocketNotifier] send_all 호출됨. "
            f"Type: {alert_type}, Message: {alert_message}, 연결 수: {len(self.active_connections)}"
        )
        logger.debug(f"[WebSocketNotifier] 전송할 페이로드: {alert_payload}")
        
        if not self.active_connections:
            logger.warning(
                f"⚠️ [WebSocketNotifier] 전송할 WebSocket 연결이 없습니다. "
                f"Type: {alert_type}, Message: {alert_message}"
            )
            return False
        
        # JSON 문자열로 변환
        try:
            message = json.dumps(alert_payload, ensure_ascii=False, default=str)
            logger.debug(f"[WebSocketNotifier] JSON 변환 완료. 메시지 길이: {len(message)} bytes")
        except Exception as e:
            logger.error(f"[WebSocketNotifier] 알림 페이로드 JSON 변환 실패: {e}", exc_info=True)
            return False
        
        # 모든 연결된 클라이언트에게 전송
        success_count = 0
        disconnected_clients = []
        connection_count = len(self.active_connections)
        
        logger.info(f"[WebSocketNotifier] {connection_count}개 클라이언트에게 전송 시작...")
        
        for idx, connection in enumerate(self.active_connections.copy(), 1):
            try:
                logger.debug(f"[WebSocketNotifier] 클라이언트 {idx}/{connection_count}에게 전송 시도...")
                await connection.send_text(message)
                success_count += 1
                logger.debug(f"[WebSocketNotifier] 클라이언트 {idx} 전송 성공")
            except WebSocketDisconnect:
                logger.warning(f"[WebSocketNotifier] 클라이언트 {idx} 연결 해제됨 (WebSocketDisconnect)")
                disconnected_clients.append(connection)
            except Exception as e:
                logger.warning(
                    f"[WebSocketNotifier] 클라이언트 {idx} 전송 실패 (연결 제거): {type(e).__name__}: {e}",
                    exc_info=True
                )
                disconnected_clients.append(connection)
        
        # 연결이 끊어진 클라이언트 제거
        for client in disconnected_clients:
            self.disconnect(client)
        
        if success_count > 0:
            logger.info(
                f"✅ [WebSocketNotifier] 알림 전송 성공: {success_count}/{connection_count}개 클라이언트에게 전송됨. "
                f"Type: {alert_payload.get('type', 'UNKNOWN')}, Message: {alert_payload.get('message', 'N/A')[:50]}"
            )
            return True
        else:
            logger.error(f"❌ [WebSocketNotifier] 알림 전송 실패: 모든 클라이언트 연결 실패 ({connection_count}개 연결)")
            return False
    
    async def send_alert(self, alert_payload: Dict[str, Any]) -> bool:
        """
        모든 연결된 WebSocket 클라이언트에게 알림을 전송합니다.
        
        이 메서드는 send_all()의 별칭입니다. 모든 연결된 클라이언트에게 동시에 전송합니다.
        
        Args:
            alert_payload: 전송할 알림 페이로드 (dict)
                - type: "CRITICAL" | "WARNING" | "RESOLVED"
                - message: 알림 메시지 (str)
                - color: 색상 (str, optional)
                - device_id: 디바이스 ID (str, optional)
                - timestamp: 타임스탬프 (str, optional)
            
        Returns:
            전송 성공 여부 (최소 한 명에게라도 전송되면 True)
        """
        return await self.send_all(alert_payload)


# 전역 WebSocket Notifier 인스턴스
_websocket_notifier: WebSocketNotifier = None


def get_websocket_notifier() -> WebSocketNotifier:
    """
    WebSocket Notifier 인스턴스를 싱글톤 패턴으로 반환합니다.
    
    Returns:
        WebSocketNotifier: WebSocket Notifier 인스턴스
    """
    global _websocket_notifier
    if _websocket_notifier is None:
        _websocket_notifier = WebSocketNotifier()
    return _websocket_notifier

