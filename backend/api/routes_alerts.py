"""
알림(Alert) 관련 API 엔드포인트

이상 탐지 결과를 기반으로 알림을 생성하고 평가하는 API를 제공합니다.
"""

from fastapi import APIRouter, status, Depends, BackgroundTasks
from typing import Optional, List, Dict, Any
from datetime import datetime

from .services.schemas.alert_schema import AlertResponse
from .services.schemas.alert_request_schema import AlertRequest
from .services.alert_engine import process_alert, AlertPayloadModel
from .services.notifier_stub import send_alert
from .services.alert_storage import save_alert, get_latest_alerts
from .services.alert_history_service import (
    get_unchecked_alerts,
    check_alert as check_alert_history
)
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
        logger.info(f"[get_latest_alerts_endpoint] 요청 수신: limit={limit}, sensor_id={sensor_id}, level={level}, user_id={current_user.id if current_user else 'None'}")
        
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
        
        # 데이터베이스 연결 확인
        try:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            logger.debug("[get_latest_alerts_endpoint] DB 연결 확인 완료")
        except Exception as db_error:
            logger.error(f"[get_latest_alerts_endpoint] DB 연결 실패: {type(db_error).__name__}: {db_error}", exc_info=True)
            raise InternalServerError(
                message=f"데이터베이스 연결 실패: {type(db_error).__name__}: {str(db_error)}"
            )
        
        # 데이터베이스에서 최신 알림 조회
        try:
            alerts = get_latest_alerts(
                db=db,
                limit=limit,
                sensor_id=sensor_id,
                level=level
            )
            logger.info(f"[get_latest_alerts_endpoint] 조회된 알림 개수: {len(alerts)}")
        except Exception as query_error:
            logger.error(f"[get_latest_alerts_endpoint] 알림 조회 실패: {type(query_error).__name__}: {query_error}", exc_info=True)
            raise InternalServerError(
                message=f"알림 조회 중 오류 발생: {type(query_error).__name__}: {str(query_error)}"
            )
        
        # Alert 모델을 AlertPayloadModel로 변환
        alert_payloads = []
        from backend.api.services.alert_engine import AlertDetailsModel
        
        for idx, alert in enumerate(alerts):
            try:
                # alert 객체 검증
                if not alert:
                    logger.warning(f"[get_latest_alerts_endpoint] 알림 {idx+1}이 None입니다. 건너뜁니다.")
                    continue
                
                logger.debug(f"[get_latest_alerts_endpoint] 알림 {idx+1}/{len(alerts)} 변환 시작: alert_id={getattr(alert, 'alert_id', 'unknown')}")
                
                # alert 필드 검증
                alert_id = getattr(alert, 'alert_id', None)
                if not alert_id:
                    logger.warning(f"[get_latest_alerts_endpoint] alert_id가 None입니다. 건너뜁니다.")
                    continue
                
                # details를 AlertDetailsModel로 복원
                details = None
                alert_details = getattr(alert, 'details', None)
                if alert_details:
                    try:
                        # alert_details가 dict인 경우
                        if isinstance(alert_details, dict):
                            # 필수 필드 확인 및 기본값 설정
                            details_dict = {
                                "vector": alert_details.get("vector", []),
                                "norm": alert_details.get("norm", 0.0),
                                "threshold": alert_details.get("threshold"),
                                "warning_threshold": alert_details.get("warning_threshold"),
                                "critical_threshold": alert_details.get("critical_threshold"),
                                "severity": alert_details.get("severity", "normal"),
                                "meta": alert_details.get("meta", {})
                            }
                            details = AlertDetailsModel(**details_dict)
                        else:
                            # 이미 AlertDetailsModel 인스턴스인 경우
                            details = alert_details
                    except Exception as e:
                        logger.warning(
                            f"[get_latest_alerts_endpoint] alert {alert.alert_id}의 details 파싱 실패: {e}. "
                            f"기본 details 사용."
                        )
                        details = None
                
                # 기본 details 생성
                if not details:
                    details = AlertDetailsModel(
                        vector=[],
                        norm=0.0,
                        threshold=None,
                        warning_threshold=None,
                        critical_threshold=None,
                        severity="normal",
                        meta={}
                    )
                
                # AlertPayloadModel 생성 (안전한 필드 접근)
                payload = AlertPayloadModel(
                    id=str(alert_id),  # 문자열로 변환
                    level=getattr(alert, 'level', 'info') or "info",
                    message=getattr(alert, 'message', 'No message') or "No message",
                    llm_summary=getattr(alert, 'llm_summary', None),
                    sensor_id=getattr(alert, 'sensor_id', 'unknown') or "unknown",
                    source=getattr(alert, 'source', 'unknown') or "unknown",
                    ts=getattr(alert, 'ts', None) or datetime.utcnow().isoformat() + "Z",
                    details=details
                )
                alert_payloads.append(payload)
                logger.debug(f"[get_latest_alerts_endpoint] 알림 {idx+1} 변환 완료: {alert_id}")
            except Exception as e:
                logger.error(
                    f"[get_latest_alerts_endpoint] 알림 {alert.alert_id if hasattr(alert, 'alert_id') else 'unknown'} 변환 실패: {e}",
                    exc_info=True
                )
                # 개별 알림 변환 실패 시 건너뛰고 계속 진행
                continue
        
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
    except InternalServerError:
        raise
    except Exception as e:
        logger.exception(
            f"[get_latest_alerts_endpoint] 예상치 못한 오류 발생: {type(e).__name__}: {e}",
            exc_info=True
        )
        raise InternalServerError(
            message=f"알림 조회 중 오류 발생: {type(e).__name__}: {str(e)}"
        )


@router.get(
    "/unchecked",
    response_model=SuccessResponse[List[Dict[str, Any]]],
    summary="미확인 알림 목록 조회",
    description="""
    미확인 알림 목록을 조회합니다.
    
    **응답:**
    - `200 OK`: 미확인 알림 목록 반환
    - `500 Internal Server Error`: 서버 내부 오류
    
    **예시:**
    - `/alerts/unchecked` - 미확인 알림 목록 조회
    - `/alerts/unchecked?limit=20` - 최대 20개만 조회
    """,
    responses={
        200: {
            "description": "미확인 알림 목록 조회 성공",
            "model": SuccessResponse[List[Dict[str, Any]]]
        },
        500: {
            "description": "서버 내부 오류",
            "model": ErrorResponse
        }
    }
)
async def get_unchecked_alerts_endpoint(
    limit: Optional[int] = None,
    current_user: User = Depends(require_permissions(Permission.ALERT_READ)),
    db: Session = Depends(get_db)
) -> SuccessResponse[List[Dict[str, Any]]]:
    """
    미확인 알림 목록을 조회합니다.
    
    Args:
        limit: 조회할 최대 개수 (없으면 전체)
        db: 데이터베이스 세션
        
    Returns:
        SuccessResponse[List[Dict[str, Any]]]: 미확인 알림 목록
    """
    try:
        # 미확인 알림 조회
        alerts = get_unchecked_alerts(db, limit=limit)
        
        # 딕셔너리로 변환
        alert_list = []
        for alert in alerts:
            alert_dict = {
                "id": alert.id,
                "device_id": alert.device_id,
                "occurred_at": alert.occurred_at.isoformat() if alert.occurred_at else None,
                "error_code": alert.error_code,
                "message": alert.message,
                "raw_value": alert.raw_value,
                "check_status": alert.check_status.value,
                "checked_by": alert.checked_by,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
            }
            alert_list.append(alert_dict)
        
        logger.info(
            f"Retrieved {len(alert_list)} unchecked alerts (limit={limit})"
        )
        
        return SuccessResponse(
            success=True,
            data=alert_list,
            message=f"Retrieved {len(alert_list)} unchecked alerts"
        )
        
    except Exception as e:
        logger.exception(f"Unexpected error while retrieving unchecked alerts: {e}")
        raise InternalServerError(
            message="An error occurred while retrieving unchecked alerts"
        )


@router.post(
    "/check",
    response_model=SuccessResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="알림 확인 처리",
    description="""
    알림을 확인 처리합니다 (DB 상태 업데이트).
    
    **요청 본문:**
    - `alert_id`: 확인할 알림 ID (필수)
    
    **응답:**
    - `200 OK`: 확인 처리 성공
    - `404 Not Found`: 알림을 찾을 수 없음
    - `500 Internal Server Error`: 서버 내부 오류
    """,
    responses={
        200: {
            "description": "알림 확인 처리 성공",
            "model": SuccessResponse[Dict[str, Any]]
        },
        404: {
            "description": "알림을 찾을 수 없음",
            "model": ErrorResponse
        },
        500: {
            "description": "서버 내부 오류",
            "model": ErrorResponse
        }
    }
)
async def check_alert_endpoint(
    alert_id: int,
    current_user: User = Depends(require_permissions(Permission.ALERT_WRITE)),
    db: Session = Depends(get_db)
) -> SuccessResponse[Dict[str, Any]]:
    """
    알림을 확인 처리합니다.
    
    Args:
        alert_id: 확인할 알림 ID
        current_user: 현재 사용자 (확인자로 사용)
        db: 데이터베이스 세션
        
    Returns:
        SuccessResponse[Dict[str, Any]]: 업데이트된 알림 정보
    """
    try:
        # 알림 확인 처리
        checked_by = current_user.email or f"user_{current_user.id}"
        alert = check_alert_history(db, alert_id, checked_by)
        
        if not alert:
            raise NotFoundError(
                message=f"Alert with ID {alert_id} not found",
                field="alert_id"
            )
        
        # 응답 데이터 구성
        alert_data = {
            "id": alert.id,
            "device_id": alert.device_id,
            "occurred_at": alert.occurred_at.isoformat() if alert.occurred_at else None,
            "error_code": alert.error_code,
            "message": alert.message,
            "raw_value": alert.raw_value,
            "check_status": alert.check_status.value,
            "checked_by": alert.checked_by,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
        }
        
        logger.info(
            f"Alert checked. ID: {alert_id}, Checked by: {checked_by}"
        )
        
        return SuccessResponse(
            success=True,
            data=alert_data,
            message=f"Alert {alert_id} checked successfully"
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error while checking alert: {e}")
        raise InternalServerError(
            message="An error occurred while checking alert"
        )