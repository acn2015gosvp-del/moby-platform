from fastapi import APIRouter, HTTPException, status
from typing import Optional
import logging # Notifier 호출 로그를 위해 추가

# 오류 수정: 'services' 패키지에서 각 모듈의 경로를 명시하여 임포트
from .services.schemas.alert_schema import AlertResponse
from .services.schemas.alert_request_schema import AlertRequest
from .services.alert_engine import process_alert, AlertPayloadModel

# NotifierStub.py 파일에서 send_alert 함수를 직접 임포트 (ImportError 해결)
from .services.notifier_stub import send_alert 

router = APIRouter()
logger = logging.getLogger(__name__) # 로거 초기화


@router.post("/evaluate", response_model=AlertPayloadModel, status_code=status.HTTP_201_CREATED)
def create_alert(alert_request: AlertRequest):
    """
    알림을 생성하고 평가합니다.
    새로운 process_alert() 함수를 사용하여 알림을 처리하고 Notifier로 발송합니다.
    """
    alert_data = alert_request.model_dump(exclude_none=True)
    result = process_alert(alert_data)

    if result is None:
        # 이상이 아니거나 처리 실패 (FastAPI가 204를 응답)
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="No alert generated (normal state or invalid input)"
        )
    
    # 🚨 Notifier 호출 로직 (Alert Engine이 생성한 페이로드를 발송) 🚨
    try:
        # send_alert 함수를 직접 호출하며, Pydantic 객체를 dict로 변환하여 전달
        send_alert(result.model_dump())
        logger.info(f"Alert {result.id} successfully dispatched via NotifierStub.")
    except Exception as e:
        logger.error(f"Alert dispatch FAILED for {result.id}: {e}")
        # 발송 실패 시에도 평가는 성공했으므로 201 응답은 유지

    # 알림 페이로드를 클라이언트에게 201 응답으로 반환
    return result


@router.post("/evaluate-legacy", response_model=AlertResponse)
def create_alert_legacy(alert_request: AlertRequest):
    # (레거시 코드 생략 - process_alert 호출은 유지)
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


# TODO: GET /latest 엔드포인트는 실제 최신 알림을 DB에서 조회하는 로직이 필요합니다.
# 현재는 알림 저장소가 없으므로 임시로 제거했습니다.