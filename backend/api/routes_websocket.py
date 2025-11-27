"""
WebSocket API 엔드포인트

React 프론트엔드와 실시간 통신을 위한 WebSocket 엔드포인트를 제공합니다.
"""

import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.api.services.websocket_notifier import get_websocket_notifier
from backend.api.services.schemas.models.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
@router.websocket("/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    """
    실시간 알림을 위한 WebSocket 엔드포인트
    
    React 프론트엔드가 이 엔드포인트에 연결하면,
    Track A (Grafana)와 Track B (AI Model)에서 발생한 알림을
    실시간으로 받을 수 있습니다.
    
    Args:
        websocket: WebSocket 연결 인스턴스
    """
    notifier = get_websocket_notifier()
    connection_accepted = False
    
    try:
        # ✅ 중요: websocket.accept()를 가장 먼저 실행해야 합니다!
        try:
            await websocket.accept()
            connection_accepted = True
            logger.info("✅ WebSocket 연결 수락 완료")
        except Exception as accept_error:
            logger.error(f"❌ WebSocket 연결 수락 실패: {accept_error}", exc_info=True)
            # accept 실패 시 함수 종료
            return
        
        # 연결 수락 후, notifier에 등록
        try:
            await notifier.connect(websocket)
            logger.info(f"✅ WebSocket 클라이언트 연결됨. 총 연결 수: {len(notifier.active_connections)}")
        except Exception as connect_error:
            logger.error(f"❌ WebSocket notifier 등록 실패: {connect_error}", exc_info=True)
            # notifier 등록 실패해도 연결은 유지 (메시지 수신은 가능)
        
        # 연결 확인 메시지 전송 (한 번만, 디버깅용)
        # 주의: 프론트엔드에서 CONNECTED 메시지는 무시하므로 실제 알림에는 영향 없음
        # ⚠️ 실제 알림은 Grafana Webhook 또는 MQTT를 통해 전송됨
        try:
            connected_message = {
                "type": "CONNECTED",
                "message": "WebSocket 연결 성공",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(connected_message))
            logger.debug("연결 확인 메시지 전송 완료 (CONNECTED - 실제 알림 아님)")
        except Exception as e:
            logger.warning(f"연결 확인 메시지 전송 실패: {e}")
            # 연결 확인 메시지 실패해도 연결은 유지
        
        # 연결 유지 및 클라이언트 메시지 대기
        while True:
            try:
                # websocket.receive()를 사용하여 연결 상태 확인
                # receive_text()는 연결이 끊어진 경우 오류를 발생시킬 수 있음
                message = await websocket.receive()
                
                # 메시지 타입 확인
                if message.get("type") == "websocket.disconnect":
                    # 클라이언트가 연결 해제
                    logger.info("WebSocket 클라이언트 연결 해제 요청 수신")
                    break
                elif message.get("type") == "websocket.receive":
                    # 텍스트 메시지 수신
                    if "text" in message:
                        data = message["text"]
                        logger.debug(f"WebSocket 클라이언트로부터 메시지 수신: {data}")
                        # 필요시 응답 가능 (현재는 Echo만)
                        # await websocket.send_text(f"Echo: {data}")
                    elif "bytes" in message:
                        logger.debug(f"WebSocket 클라이언트로부터 바이너리 메시지 수신 (무시)")
            except WebSocketDisconnect:
                # 클라이언트가 정상적으로 연결 해제
                logger.info("WebSocket 클라이언트 연결 해제됨 (WebSocketDisconnect)")
                break
            except RuntimeError as e:
                # WebSocket 연결 오류 (연결이 끊어졌거나 accept되지 않음)
                error_msg = str(e)
                if "not connected" in error_msg.lower() or "accept" in error_msg.lower():
                    logger.warning(f"WebSocket 연결 상태 오류: {e}. 연결을 종료합니다.")
                    break
                else:
                    logger.error(f"WebSocket RuntimeError: {e}", exc_info=True)
                    break
            except Exception as e:
                logger.error(f"WebSocket 메시지 수신 중 오류: {e}", exc_info=True)
                # 심각한 오류인 경우 연결 종료
                if "not connected" in str(e).lower() or "accept" in str(e).lower():
                    logger.warning("WebSocket 연결이 끊어진 것으로 보입니다. 연결을 종료합니다.")
                    break
                # 다른 오류는 연결을 유지하고 계속 시도
                continue
            
    except WebSocketDisconnect:
        # 클라이언트 연결 해제 (정상)
        logger.info("WebSocket 클라이언트 연결 해제됨 (정상)")
    except Exception as e:
        # 연결 수락 또는 초기화 중 오류 발생
        logger.error(f"WebSocket 연결 초기화 중 오류 발생: {e}", exc_info=True)
        # 연결이 수락되었다면 해제 시도
        if connection_accepted:
            try:
                if websocket in notifier.active_connections:
                    notifier.disconnect(websocket)
            except Exception as cleanup_error:
                logger.warning(f"WebSocket 정리 중 오류: {cleanup_error}")
    finally:
        # 최종 정리: 연결이 아직 활성 상태면 해제
        try:
            if websocket in notifier.active_connections:
                notifier.disconnect(websocket)
                logger.debug("WebSocket 연결 최종 정리 완료")
        except Exception as e:
            logger.warning(f"WebSocket 연결 정리 중 오류: {e}")


@router.post("/test-alert")
async def test_websocket_alert(
    alert_type: str = "WARNING",
    message: str = "테스트 알림 메시지"
):
    """
    WebSocket 알림 전송 테스트 엔드포인트
    
    개발 및 디버깅 목적으로 사용합니다.
    """
    from datetime import datetime
    
    notifier = get_websocket_notifier()
    
    websocket_payload = {
        "type": alert_type.upper(),
        "message": message,
        "color": "red" if alert_type.upper() == "CRITICAL" else ("orange" if alert_type.upper() == "WARNING" else "green"),
        "device_id": "test_device",
        "timestamp": datetime.now().isoformat()
    }
    
    success = await notifier.send_alert(websocket_payload)
    
    return {
        "success": success,
        "message": f"테스트 알림 전송 {'성공' if success else '실패'}",
        "connections": len(notifier.active_connections),
        "payload": websocket_payload
    }

