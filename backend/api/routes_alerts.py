"""
알림(Alert) 관련 API 엔드포인트

이상 탐지 결과를 기반으로 알림을 생성하고 평가하는 API를 제공합니다.
"""

from fastapi import APIRouter, status, Depends, BackgroundTasks
from typing import Optional, List
from datetime import datetime

from .services.schemas.alert_schema import AlertResponse
from .services.schemas.alert_request_schema import AlertRequest
from .services.alert_engine import process_alert, AlertPayloadModel
from .services.notifier_stub import send_alert
from .services.alert_storage import save_alert, get_latest_alerts
from .core.responses import SuccessResponse, ErrorResponse
from .core.api_exceptions import BadRequestError, InternalServerError, NotFoundError
from .core.permissions import require_permissions
from .models.role import Permission
from .models.user import User
from .services.schemas.models.core.logger import get_logger
from backend.api.services.database import get_db
from sqlalchemy.orm import Session

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
async def create_alert(
    alert_request: AlertRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permissions(Permission.ALERT_WRITE)),
    timestamp: str = Depends(get_current_timestamp),
    db: Session = Depends(get_db)
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
        # 동기 함수를 비동기 컨텍스트에서 실행 (블로킹 방지)
        import asyncio
        result = await asyncio.to_thread(process_alert, alert_data)

        if result is None:
            # 이상이 아니거나 처리 실패 시 204 응답
            # FastAPI는 204 응답 시 body를 반환하지 않음
            from fastapi import Response
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        
        # 데이터베이스에 알림 저장
        try:
            save_alert(db, result)
        except Exception as e:
            logger.error(
                f"Failed to save alert to database. Alert ID: {result.id}, Error: {e}",
                exc_info=True
            )
            # 저장 실패해도 알림은 생성되었으므로 계속 진행
        
        # 🚨 Notifier 호출 로직 (Alert Engine이 생성한 페이로드를 발송) 🚨
        # 백그라운드 태스크로 발송하여 응답 지연 최소화
        background_tasks.add_task(send_alert, result.model_dump())
        logger.info(
            f"Alert {result.id} queued for dispatch. "
            f"Sensor: {result.sensor_id}, Level: {result.level}"
        )

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
async def create_alert_legacy(alert_request: AlertRequest) -> SuccessResponse[AlertResponse]:
    """
    레거시 형식으로 알림을 생성하고 평가합니다.
    
    Args:
        alert_request: 알림 생성 요청 데이터
        
    Returns:
        SuccessResponse[AlertResponse]: 레거시 형식의 알림 응답
    """
    try:
        alert_data = alert_request.model_dump(exclude_none=True)
        # 동기 함수를 비동기 컨텍스트에서 실행
        import asyncio
        result = await asyncio.to_thread(process_alert, alert_data)

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


@router.get(
    "/latest",
    response_model=SuccessResponse[List[AlertPayloadModel]],
    summary="최신 알림 조회",
    description="""
    최신 알림 목록을 조회합니다.
    
    **쿼리 파라미터:**
    - `limit`: 조회할 최대 개수 (기본값: 10, 최대: 100)
    - `sensor_id`: 특정 센서 ID로 필터링 (선택)
    - `level`: 특정 레벨로 필터링 (선택: info, warning, critical)
    
    **응답:**
    - `200 OK`: 최신 알림 목록 반환
    - `500 Internal Server Error`: 서버 내부 오류
    
    **예시:**
    - `/alerts/latest?limit=20` - 최신 20개 알림 조회
    - `/alerts/latest?sensor_id=sensor_001` - 특정 센서의 최신 알림 조회
    - `/alerts/latest?level=critical` - Critical 레벨 알림만 조회
    """,
    responses={
        200: {
            "description": "최신 알림 목록 조회 성공",
            "model": SuccessResponse[List[AlertPayloadModel]]
        },
        500: {
            "description": "서버 내부 오류",
            "model": ErrorResponse
        }
    }
)
async def get_latest_alerts_endpoint(
    limit: int = 10,
    sensor_id: Optional[str] = None,
    level: Optional[str] = None,
    current_user: User = Depends(require_permissions(Permission.ALERT_READ)),
    db: Session = Depends(get_db)
) -> SuccessResponse[List[AlertPayloadModel]]:
    """
    최신 알림 목록을 조회합니다.
    
    Args:
        limit: 조회할 최대 개수 (1-100)
        sensor_id: 특정 센서 ID로 필터링 (선택)
        level: 특정 레벨로 필터링 (선택)
        db: 데이터베이스 세션
        
    Returns:
        SuccessResponse[List[AlertPayloadModel]]: 최신 알림 목록
        
    Raises:
        BadRequestError: 잘못된 파라미터
        InternalServerError: 조회 중 내부 오류
    """
    try:
        # limit 검증
        if limit < 1 or limit > 100:
            raise BadRequestError(
                message="limit은 1과 100 사이의 값이어야 합니다.",
                field="limit"
            )
        
        # level 검증
        if level and level not in ["info", "warning", "critical"]:
            raise BadRequestError(
                message="level은 'info', 'warning', 'critical' 중 하나여야 합니다.",
                field="level"
            )
        
        # 데이터베이스에서 최신 알림 조회
        alerts = get_latest_alerts(
            db=db,
            limit=limit,
            sensor_id=sensor_id,
            level=level
        )
        
        # Alert 모델을 AlertPayloadModel로 변환
        alert_payloads = []
        for alert in alerts:
            # details를 AlertDetailsModel로 복원
            from backend.api.services.alert_engine import AlertDetailsModel
            
            details = None
            if alert.details:
                details = AlertDetailsModel(**alert.details)
            
            payload = AlertPayloadModel(
                id=alert.alert_id,
                level=alert.level,
                message=alert.message,
                llm_summary=alert.llm_summary,
                sensor_id=alert.sensor_id,
                source=alert.source,
                ts=alert.ts,
                details=details or AlertDetailsModel(
                    vector=[],
                    norm=0.0,
                    threshold=None,
                    warning_threshold=None,
                    critical_threshold=None,
                    severity="normal",
                    meta={}
                )
            )
            alert_payloads.append(payload)
        
        logger.info(
            f"Retrieved {len(alert_payloads)} latest alerts. "
            f"Filters: sensor_id={sensor_id}, level={level}, limit={limit}"
        )
        
        return SuccessResponse(
            success=True,
            data=alert_payloads,
            message=f"Retrieved {len(alert_payloads)} latest alerts"
        )
        
    except BadRequestError:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error while retrieving latest alerts: {e}")
        raise InternalServerError(
            message="An error occurred while retrieving latest alerts"
        )