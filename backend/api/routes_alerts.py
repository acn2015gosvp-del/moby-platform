from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect
import logging 

# Notifier Service 인스턴스를 가져옵니다.
from .services.notifier_stub import notifier 
from .services.schemas.alert_schema import AlertResponse
from .services.schemas.alert_request_schema import AlertRequest
from .services.alert_engine import process_alert, AlertPayloadModel

router = APIRouter()
logger = logging.getLogger(__name__) 


@router.post("/evaluate", response_model=AlertPayloadModel, status_code=status.HTTP_201_CREATED)
def create_alert(alert_request: AlertRequest):
    """
    알림을 생성하고 평가합니다.
    """
    alert_data = alert_request.model_dump(exclude_none=True)
    result = process_alert(alert_data)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="No alert generated (normal state or invalid input)"
        )
    
    # 🚨 Notifier 호출 로직 🚨
    try:
        notifier.send_alert(result.model_dump()) 
        logger.info(f"Alert {result.id} successfully dispatched via NotifierStub.")
    except Exception as e:
        logger.error(f"Alert dispatch FAILED for {result.id}: {e}")

    return result


@router.post("/evaluate-legacy", response_model=AlertResponse)
def create_alert_legacy(alert_request: AlertRequest):
    alert_data = alert_request.model_dump(exclude_none=True)
    result = process_alert(alert_data)

    if result is None:
        return AlertResponse(
            status="normal",
            message="No anomaly detected",
            llm_summary=None
        )

    return AlertResponse(
        status=result.level,
        message=result.message,
        llm_summary=result.llm_summary
    )


@router.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept() 
    
    try:
        # ⚠️ 최종 안정화 구조: 클라이언트가 연결을 닫을 때까지 여기서 대기합니다.
        while True:
            # 이 라인은 클라이언트가 메시지를 보내거나 연결을 닫을 때까지 블로킹됩니다.
            # _data로 변수명을 변경하여 Linter 경고를 방지합니다.
            _data = await websocket.receive_text() 
            
    except WebSocketDisconnect:
        logger.info("WS Client disconnected.")
    except Exception as e:
        # 최종적으로 모든 예외는 로깅 후 자동으로 연결 종료됩니다.
        logger.error(f"Critical WS Exception during communication: {e}")