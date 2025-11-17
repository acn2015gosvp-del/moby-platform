"""
알림(Alert) 관련 API 엔드포인트

이상 탐지 결과를 기반으로 알림을 생성하고 평가하는 API를 제공합니다.
"""

from fastapi import APIRouter, status, Depends
from typing import Optional
from datetime import datetime

from .services.schemas.alert_schema import AlertResponse
from .services.schemas.alert_request_schema import AlertRequest
from .services.alert_engine import process_alert, AlertPayloadModel
from .services.notifier_stub import send_alert
from .core.responses import SuccessResponse, ErrorResponse
from .core.api_exceptions import BadRequestError, InternalServerError
from .services.schemas.models.core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


def get_current_timestamp() -> str:
    """현재 타임스탬프를 ISO 8601 형식으로 반환하는 의존성"""
    return datetime.utcnow().isoformat() + "Z"


@router.post(
    "/evaluate",
    response_model=SuccessResponse[AlertPayloadModel],
    status_code=status.HTTP_201_CREATED,
    summary="알림 생성 및 평가",
    description="""
    센서 데이터 벡터를 기반으로 이상 탐지를 수행하고 알림을 생성합니다.
    
    **주요 기능:**
    - 벡터 기반 이상 탐지 (L2 norm 계산)
    - 단일 임계값 또는 경고/심각 임계값 지원
    - LLM 기반 알림 요약 생성 (옵션)
    - 자동 알림 발송 (Notifier)
    
    **입력 파라미터:**
    - `vector`: 이상 탐지에 사용할 벡터 데이터 (필수)
    - `threshold`: 단일 임계값 (threshold 또는 warning_threshold/critical_threshold 중 하나 필수)
    - `warning_threshold`: 경고 임계값 (critical_threshold와 함께 사용)
    - `critical_threshold`: 심각 임계값 (warning_threshold와 함께 사용)
    - `sensor_id`: 센서 ID (기본값: "unknown_sensor")
    - `enable_llm_summary`: LLM 요약 생성 여부 (기본값: true)
    
    **응답:**
    - `201 Created`: 알림이 성공적으로 생성됨
    - `204 No Content`: 이상이 탐지되지 않음 (정상 상태)
    - `400 Bad Request`: 잘못된 요청 데이터
    - `422 Unprocessable Entity`: 입력 데이터 검증 실패
    - `500 Internal Server Error`: 서버 내부 오류
    
    **예시:**
    ```json
    {
        "vector": [1.5, 2.3, 3.1],
        "threshold": 5.0,
        "sensor_id": "sensor_001",
        "enable_llm_summary": true
    }
    ```
    """,
    responses={
        201: {
            "description": "알림이 성공적으로 생성됨",
            "model": SuccessResponse[AlertPayloadModel]
        },
        204: {
            "description": "이상이 탐지되지 않음 (정상 상태)"
        },
        400: {
            "description": "잘못된 요청",
            "model": ErrorResponse
        },
        422: {
            "description": "입력 데이터 검증 실패",
            "model": ErrorResponse
        },
        500: {
            "description": "서버 내부 오류",
            "model": ErrorResponse
        }
    }
)
def create_alert(
    alert_request: AlertRequest,
    timestamp: str = Depends(get_current_timestamp)
) -> SuccessResponse[AlertPayloadModel]:
    """
    알림을 생성하고 평가합니다.
    
    새로운 process_alert() 함수를 사용하여 알림을 처리하고 Notifier로 발송합니다.
    
    Args:
        alert_request: 알림 생성 요청 데이터
        timestamp: 현재 타임스탬프 (의존성 주입)
        
    Returns:
        SuccessResponse[AlertPayloadModel]: 생성된 알림 페이로드
        
    Raises:
        BadRequestError: 잘못된 요청 데이터
        InternalServerError: 알림 처리 중 내부 오류
    """
    try:
        alert_data = alert_request.model_dump(exclude_none=True)
        result = process_alert(alert_data)

        if result is None:
            # 이상이 아니거나 처리 실패 시 204 응답
            # FastAPI는 204 응답 시 body를 반환하지 않음
            from fastapi import Response
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        
        # 🚨 Notifier 호출 로직 (Alert Engine이 생성한 페이로드를 발송) 🚨
        try:
            send_alert(result.model_dump())
            logger.info(
                f"Alert {result.id} successfully dispatched via NotifierStub. "
                f"Sensor: {result.sensor_id}, Level: {result.level}"
            )
        except Exception as e:
            logger.error(
                f"Alert dispatch FAILED for {result.id}: {e}",
                exc_info=True
            )
            # 발송 실패 시에도 평가는 성공했으므로 201 응답은 유지
            # 하지만 로그에는 기록됨

        return SuccessResponse(
            success=True,
            data=result,
            message=f"Alert {result.id} created and dispatched successfully"
        )
        
    except ValueError as e:
        logger.warning(f"Invalid alert request: {e}")
        raise BadRequestError(
            message=f"Invalid request data: {str(e)}",
            field="request"
        )
    except Exception as e:
        logger.exception(f"Unexpected error while processing alert: {e}")
        raise InternalServerError(
            message="An error occurred while processing the alert request"
        )


@router.post(
    "/evaluate-legacy",
    response_model=SuccessResponse[AlertResponse],
    status_code=status.HTTP_200_OK,
    summary="알림 생성 및 평가 (레거시 형식)",
    description="""
    레거시 형식의 알림 응답을 반환하는 엔드포인트입니다.
    
    **참고:** 이 엔드포인트는 하위 호환성을 위해 유지됩니다.
    새로운 프로젝트는 `/evaluate` 엔드포인트를 사용하는 것을 권장합니다.
    
    **응답 형식:**
    - `status`: 알림 레벨 (info, warning, critical)
    - `message`: 알림 메시지
    - `llm_summary`: LLM 요약 (있는 경우)
    """,
    deprecated=True
)
def create_alert_legacy(alert_request: AlertRequest) -> SuccessResponse[AlertResponse]:
    """
    레거시 형식으로 알림을 생성하고 평가합니다.
    
    Args:
        alert_request: 알림 생성 요청 데이터
        
    Returns:
        SuccessResponse[AlertResponse]: 레거시 형식의 알림 응답
    """
    try:
        alert_data = alert_request.model_dump(exclude_none=True)
        result = process_alert(alert_data)

        if result is None:
            return SuccessResponse(
                success=True,
                data=AlertResponse(
                    status="normal",
                    message="No anomaly detected",
                    llm_summary=None
                ),
                message="No anomaly detected"
            )

        return SuccessResponse(
            success=True,
            data=AlertResponse(
                status=result.level,
                message=result.message,
                llm_summary=result.llm_summary
            ),
            message="Alert processed successfully"
        )
    except Exception as e:
        logger.exception(f"Error in legacy alert endpoint: {e}")
        raise InternalServerError(
            message="An error occurred while processing the alert request"
        )


# TODO: GET /latest 엔드포인트는 실제 최신 알림을 DB에서 조회하는 로직이 필요합니다.
# 현재는 알림 저장소가 없으므로 임시로 제거했습니다.