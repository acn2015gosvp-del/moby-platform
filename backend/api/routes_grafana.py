"""
Grafana 연동 API 엔드포인트

Grafana 데이터 소스 및 대시보드 관리를 위한 API를 제공합니다.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from backend.api.core.responses import SuccessResponse, ErrorResponse
from backend.api.core.api_exceptions import BadRequestError, InternalServerError
from backend.api.core.permissions import require_permissions
from backend.api.models.role import Permission
from backend.api.models.user import User
from backend.api.services.grafana_client import get_grafana_client, GrafanaClient
from backend.api.services.schemas.models.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/grafana", tags=["Grafana"])


# 요청/응답 스키마
class DatasourceCreateRequest(BaseModel):
    """데이터 소스 생성 요청"""
    name: str = Field(..., description="데이터 소스 이름")
    type: str = Field(default="influxdb", description="데이터 소스 타입")
    url: Optional[str] = Field(None, description="InfluxDB URL (선택사항)")
    is_default: bool = Field(default=False, description="기본 데이터 소스로 설정할지 여부")


class DashboardCreateRequest(BaseModel):
    """대시보드 생성 요청"""
    title: str = Field(..., description="대시보드 제목")
    datasource_name: str = Field(default="InfluxDB", description="데이터 소스 이름")


def get_grafana_client_dependency() -> GrafanaClient:
    """
    Grafana 클라이언트 의존성
    
    Returns:
        GrafanaClient 인스턴스
        
    Raises:
        HTTPException: Grafana 클라이언트를 초기화할 수 없는 경우
    """
    client = get_grafana_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Grafana 클라이언트를 초기화할 수 없습니다. GRAFANA_URL과 GRAFANA_API_KEY를 확인하세요."
        )
    return client


@router.get("/health", response_model=SuccessResponse)
async def check_grafana_connection(
    client: GrafanaClient = Depends(get_grafana_client_dependency)
):
    """
    Grafana 연결 상태 확인
    
    Returns:
        연결 상태 정보
    """
    try:
        is_connected = client.test_connection()
        if is_connected:
            return SuccessResponse(
                data={"status": "connected", "url": client.base_url},
                message="Grafana 연결 성공"
            )
        else:
            return SuccessResponse(
                data={"status": "disconnected", "url": client.base_url},
                message="Grafana 연결 실패"
            )
    except Exception as e:
        logger.exception("Grafana 연결 확인 중 오류 발생")
        raise InternalServerError(message=f"Grafana 연결 확인 실패: {str(e)}")


@router.post("/datasources", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_datasource(
    request: DatasourceCreateRequest,
    current_user: User = Depends(require_permissions(Permission.GRAFANA_WRITE)),
    client: GrafanaClient = Depends(get_grafana_client_dependency)
):
    """
    InfluxDB 데이터 소스 생성
    
    Args:
        request: 데이터 소스 생성 요청
        
    Returns:
        생성된 데이터 소스 정보
    """
    try:
        result = client.create_datasource(
            name=request.name,
            type=request.type,
            url=request.url,
            is_default=request.is_default
        )
        
        return SuccessResponse(
            data=result,
            message=f"데이터 소스 '{request.name}' 생성 완료"
        )
    except ValueError as e:
        raise BadRequestError(message=str(e))
    except Exception as e:
        logger.exception("데이터 소스 생성 중 오류 발생")
        raise InternalServerError(message=f"데이터 소스 생성 실패: {str(e)}")


@router.get("/datasources/{name}", response_model=SuccessResponse)
async def get_datasource(
    name: str,
    current_user: User = Depends(require_permissions(Permission.GRAFANA_READ)),
    client: GrafanaClient = Depends(get_grafana_client_dependency)
):
    """
    데이터 소스 조회
    
    Args:
        name: 데이터 소스 이름
        
    Returns:
        데이터 소스 정보
    """
    try:
        datasource = client.get_datasource_by_name(name)
        if datasource is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"데이터 소스를 찾을 수 없습니다: {name}"
            )
        
        return SuccessResponse(
            data=datasource,
            message=f"데이터 소스 '{name}' 조회 완료"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("데이터 소스 조회 중 오류 발생")
        raise InternalServerError(message=f"데이터 소스 조회 실패: {str(e)}")


@router.post("/dashboards", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    request: DashboardCreateRequest,
    current_user: User = Depends(require_permissions(Permission.GRAFANA_WRITE)),
    client: GrafanaClient = Depends(get_grafana_client_dependency)
):
    """
    센서 데이터 대시보드 생성
    
    Args:
        request: 대시보드 생성 요청
        
    Returns:
        생성된 대시보드 정보
    """
    try:
        result = client.create_sensor_dashboard(
            dashboard_title=request.title,
            datasource_name=request.datasource_name
        )
        
        return SuccessResponse(
            data=result,
            message=f"대시보드 '{request.title}' 생성 완료"
        )
    except ValueError as e:
        raise BadRequestError(message=str(e))
    except Exception as e:
        logger.exception("대시보드 생성 중 오류 발생")
        raise InternalServerError(message=f"대시보드 생성 실패: {str(e)}")

