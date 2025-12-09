"""
Grafana API 프록시 엔드포인트

클라이언트에서 직접 Grafana API를 호출할 때 발생하는 CORS 문제를 해결하기 위해
백엔드 서버를 프록시로 사용합니다.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
import httpx
from backend.api.core.responses import SuccessResponse
from backend.api.services.schemas.models.core.logger import get_logger
from backend.api.services.schemas.models.core.config import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/api/proxy-grafana", tags=["Grafana Proxy"])

# Grafana 서버 설정
GRAFANA_BASE_URL = "http://192.168.80.183:8080"
# 환경 변수에서 Grafana API 키 가져오기
import os
GRAFANA_API_KEY = os.getenv("GRAFANA_API_KEY") or (settings.GRAFANA_API_KEY if hasattr(settings, 'GRAFANA_API_KEY') else None)


@router.get("/dashboard/{dashboard_uid}")
async def get_grafana_dashboard(
    dashboard_uid: str,
    org_id: Optional[int] = Query(1, description="Grafana Organization ID")
) -> SuccessResponse[Dict[str, Any]]:
    """
    Grafana 대시보드 정보를 가져옵니다 (프록시)
    
    Args:
        dashboard_uid: Grafana 대시보드 UID
        org_id: Grafana Organization ID (기본값: 1)
        
    Returns:
        대시보드 정보
    """
    if not GRAFANA_API_KEY:
        logger.warning("Grafana API 키가 설정되지 않았습니다.")
        raise HTTPException(
            status_code=500,
            detail="Grafana API 키가 설정되지 않았습니다. 환경 변수 GRAFANA_API_KEY를 확인하세요."
        )
    
    try:
        url = f"{GRAFANA_BASE_URL}/api/dashboards/uid/{dashboard_uid}"
        headers = {
            "Authorization": f"Bearer {GRAFANA_API_KEY}",
            "Content-Type": "application/json",
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 404:
                logger.warning(f"Grafana 대시보드를 찾을 수 없습니다: {dashboard_uid}")
                raise HTTPException(
                    status_code=404,
                    detail=f"대시보드를 찾을 수 없습니다: {dashboard_uid}"
                )
            
            if not response.is_success:
                logger.error(f"Grafana API 요청 실패: {response.status_code} {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Grafana API 요청 실패: {response.status_code}"
                )
            
            data = response.json()
            dashboard = data.get("dashboard", {})
            
            result = {
                "uid": dashboard.get("uid"),
                "title": dashboard.get("title"),
                "url": dashboard.get("url") or f"/d/{dashboard.get('uid')}",
                "version": dashboard.get("version", 1),
                "tags": dashboard.get("tags", []),
            }
            
            logger.info(f"✅ Grafana 대시보드 정보 조회 성공: {dashboard_uid}")
            return SuccessResponse(
                success=True,
                data=result,
                message=f"대시보드 정보 조회 완료: {dashboard_uid}"
            )
            
    except httpx.TimeoutException:
        logger.error(f"Grafana API 요청 타임아웃: {dashboard_uid}")
        raise HTTPException(
            status_code=504,
            detail="Grafana 서버 응답 시간 초과"
        )
    except httpx.RequestError as e:
        logger.error(f"Grafana API 요청 실패: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Grafana 서버 연결 실패: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Grafana 대시보드 조회 중 예상치 못한 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"대시보드 조회 실패: {str(e)}"
        )


@router.get("/health")
async def check_grafana_health() -> SuccessResponse[Dict[str, Any]]:
    """
    Grafana 서버 연결 상태를 확인합니다 (프록시)
    
    Returns:
        Grafana 서버 상태
    """
    try:
        url = f"{GRAFANA_BASE_URL}/api/health"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            
            is_healthy = response.is_success
            logger.info(f"Grafana 서버 상태 확인: {'연결됨' if is_healthy else '연결 실패'}")
            
            return SuccessResponse(
                success=True,
                data={
                    "connected": is_healthy,
                    "status_code": response.status_code,
                },
                message="Grafana 서버 상태 확인 완료"
            )
            
    except httpx.TimeoutException:
        logger.warning("Grafana 서버 상태 확인 타임아웃")
        return SuccessResponse(
            success=False,
            data={"connected": False},
            message="Grafana 서버 응답 시간 초과"
        )
    except Exception as e:
        logger.warning(f"Grafana 서버 상태 확인 실패: {e}")
        return SuccessResponse(
            success=False,
            data={"connected": False},
            message=f"Grafana 서버 연결 실패: {str(e)}"
        )

