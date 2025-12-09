"""
헬스체크 및 모니터링 API 엔드포인트

시스템 상태 확인 및 각 서비스별 헬스체크를 제공합니다.
"""

from fastapi import APIRouter, status
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from backend.api.core.responses import SuccessResponse, ErrorResponse
from backend.api.core.api_exceptions import InternalServerError
from backend.api.services.schemas.models.core.logger import get_logger
from backend.api.services.schemas.models.core.config import settings

# 서비스 상태 확인을 위한 임포트
from backend.api.services.mqtt_client import mqtt_manager
from backend.api.services.influx_client import influx_manager
from backend.api.services.grafana_client import get_grafana_client
from backend.api.services.database import SessionLocal

logger = get_logger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])


class ServiceStatus(BaseModel):
    """서비스 상태 모델"""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """헬스체크 응답 모델"""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    version: str
    services: Dict[str, ServiceStatus]
    uptime_seconds: Optional[float] = None


# 애플리케이션 시작 시간
_app_start_time: Optional[datetime] = None


def set_app_start_time():
    """애플리케이션 시작 시간 설정"""
    global _app_start_time
    _app_start_time = datetime.utcnow()


def get_uptime_seconds() -> Optional[float]:
    """애플리케이션 가동 시간 (초) 반환"""
    if _app_start_time is None:
        return None
    return (datetime.utcnow() - _app_start_time).total_seconds()


def check_mqtt_status() -> ServiceStatus:
    """MQTT 연결 상태 확인"""
    try:
        if mqtt_manager is None:
            return ServiceStatus(
                name="mqtt",
                status="unhealthy",
                message="MQTT manager not initialized"
            )
        
        # MQTT 클라이언트 연결 상태 확인
        is_connected = mqtt_manager.client.is_connected() if mqtt_manager.client else False
        
        if is_connected:
            return ServiceStatus(
                name="mqtt",
                status="healthy",
                message="Connected",
                details={
                    "host": settings.MQTT_HOST,
                    "port": settings.MQTT_PORT,
                    "queue_size": len(mqtt_manager.message_queue) if hasattr(mqtt_manager, 'message_queue') else 0
                }
            )
        else:
            return ServiceStatus(
                name="mqtt",
                status="degraded",
                message="Not connected",
                details={
                    "host": settings.MQTT_HOST,
                    "port": settings.MQTT_PORT
                }
            )
    except Exception as e:
        logger.exception("MQTT 상태 확인 중 오류 발생")
        return ServiceStatus(
            name="mqtt",
            status="unhealthy",
            message=f"Error: {str(e)}"
        )


def check_influxdb_status() -> ServiceStatus:
    """InfluxDB 연결 상태 확인"""
    try:
        if influx_manager is None:
            return ServiceStatus(
                name="influxdb",
                status="unhealthy",
                message="InfluxDB manager not initialized"
            )
        
        # InfluxDB 클라이언트 연결 상태 확인
        is_connected = influx_manager.write_api is not None
        
        if is_connected:
            buffer_size = len(influx_manager.buffer) if hasattr(influx_manager, 'buffer') else 0
            return ServiceStatus(
                name="influxdb",
                status="healthy",
                message="Connected",
                details={
                    "url": settings.INFLUX_URL,
                    "org": settings.INFLUX_ORG,
                    "bucket": settings.INFLUX_BUCKET,
                    "buffer_size": buffer_size
                }
            )
        else:
            return ServiceStatus(
                name="influxdb",
                status="unhealthy",
                message="Not connected",
                details={
                    "url": settings.INFLUX_URL
                }
            )
    except Exception as e:
        logger.exception("InfluxDB 상태 확인 중 오류 발생")
        return ServiceStatus(
            name="influxdb",
            status="unhealthy",
            message=f"Error: {str(e)}"
        )


def check_database_status() -> ServiceStatus:
    """데이터베이스 연결 상태 확인"""
    try:
        db = SessionLocal()
        try:
            # 간단한 쿼리로 연결 테스트
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            return ServiceStatus(
                name="database",
                status="healthy",
                message="Connected"
            )
        finally:
            db.close()
    except Exception as e:
        logger.exception("데이터베이스 상태 확인 중 오류 발생")
        return ServiceStatus(
            name="database",
            status="unhealthy",
            message=f"Error: {str(e)}"
        )


def check_grafana_status() -> ServiceStatus:
    """Grafana 연결 상태 확인"""
    try:
        grafana_client = get_grafana_client()
        if grafana_client is None:
            return ServiceStatus(
                name="grafana",
                status="degraded",
                message="Grafana client not configured"
            )
        
        is_connected = grafana_client.test_connection()
        
        if is_connected:
            return ServiceStatus(
                name="grafana",
                status="healthy",
                message="Connected",
                details={
                    "url": grafana_client.base_url
                }
            )
        else:
            return ServiceStatus(
                name="grafana",
                status="degraded",
                message="Connection test failed",
                details={
                    "url": grafana_client.base_url
                }
            )
    except Exception as e:
        logger.exception("Grafana 상태 확인 중 오류 발생")
        return ServiceStatus(
            name="grafana",
            status="degraded",
            message=f"Error: {str(e)}"
        )


@router.get(
    "",
    response_model=SuccessResponse[HealthResponse],
    summary="시스템 헬스체크",
    description="""
    전체 시스템 및 각 서비스의 상태를 확인합니다.
    
    **응답 상태:**
    - `healthy`: 모든 서비스가 정상 작동
    - `degraded`: 일부 서비스가 비정상이지만 핵심 기능은 작동
    - `unhealthy`: 핵심 서비스가 비정상
    
    **확인하는 서비스:**
    - MQTT Broker
    - InfluxDB
    - Database (SQLite)
    - Grafana (선택사항)
    """,
    responses={
        200: {
            "description": "헬스체크 성공",
            "model": SuccessResponse[HealthResponse]
        },
        500: {
            "description": "서버 내부 오류",
            "model": ErrorResponse
        }
    }
)
async def health_check() -> SuccessResponse[HealthResponse]:
    """
    전체 시스템 헬스체크
    
    Returns:
        SuccessResponse[HealthResponse]: 시스템 상태 정보
    """
    try:
        # 각 서비스 상태 확인
        services = {
            "mqtt": check_mqtt_status(),
            "influxdb": check_influxdb_status(),
            "database": check_database_status(),
            "grafana": check_grafana_status()
        }
        
        # 전체 상태 결정
        service_statuses = [s.status for s in services.values()]
        
        if "unhealthy" in service_statuses:
            overall_status = "unhealthy"
        elif "degraded" in service_statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        # 서비스 상태를 딕셔너리로 변환
        services_dict = {name: status for name, status in services.items()}
        
        health_response = HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat() + "Z",
            version="1.0.0",
            services=services_dict,
            uptime_seconds=get_uptime_seconds()
        )
        
        return SuccessResponse(
            success=True,
            data=health_response,
            message="Health check completed"
        )
        
    except Exception as e:
        logger.exception("헬스체크 중 오류 발생")
        raise InternalServerError(message=f"Health check failed: {str(e)}")


@router.get(
    "/liveness",
    response_model=SuccessResponse,
    summary="Liveness 프로브",
    description="""
    Kubernetes Liveness 프로브용 엔드포인트.
    애플리케이션이 살아있는지만 확인합니다.
    """,
    responses={
        200: {
            "description": "애플리케이션 정상",
            "model": SuccessResponse
        }
    }
)
async def liveness() -> SuccessResponse:
    """
    Liveness 프로브
    
    Returns:
        SuccessResponse: 애플리케이션이 살아있음을 나타내는 응답
    """
    return SuccessResponse(
        success=True,
        data={"status": "alive"},
        message="Application is alive"
    )


@router.get(
    "/readiness",
    response_model=SuccessResponse,
    summary="Readiness 프로브",
    description="""
    Kubernetes Readiness 프로브용 엔드포인트.
    애플리케이션이 요청을 처리할 준비가 되었는지 확인합니다.
    """,
    responses={
        200: {
            "description": "애플리케이션 준비 완료",
            "model": SuccessResponse
        },
        503: {
            "description": "애플리케이션 준비되지 않음",
            "model": ErrorResponse
        }
    }
)
async def readiness() -> SuccessResponse:
    """
    Readiness 프로브
    
    Returns:
        SuccessResponse: 애플리케이션이 준비되었음을 나타내는 응답
    """
    try:
        # 핵심 서비스만 확인 (빠른 응답)
        db_status = check_database_status()
        
        if db_status.status == "unhealthy":
            from fastapi import HTTPException
            raise HTTPException(
                status_code=503,
                detail="Application is not ready"
            )
        
        return SuccessResponse(
            success=True,
            data={"status": "ready"},
            message="Application is ready"
        )
    except Exception as e:
        logger.exception("Readiness 체크 중 오류 발생")
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail=f"Application is not ready: {str(e)}"
        )

