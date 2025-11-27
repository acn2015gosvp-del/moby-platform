"""
Webhook API 엔드포인트

명세서 요구사항에 따른 Webhook 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, BackgroundTasks
from typing import Dict, Any

from backend.api.core.responses import SuccessResponse
from backend.api.core.api_exceptions import InternalServerError
from backend.api.routes_grafana import receive_grafana_webhook
from backend.api.services.schemas.models.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["Webhook"])


# 명세서 요구사항: POST /api/webhook/grafana
@router.post("/webhook/grafana", response_model=SuccessResponse, status_code=200)
async def webhook_grafana(
    webhook_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Grafana Webhook 엔드포인트 (명세서 요구사항)
    
    명세서에 따라 POST /api/webhook/grafana 엔드포인트를 제공합니다.
    실제 처리는 routes_grafana의 receive_grafana_webhook 함수를 재사용합니다.
    
    Args:
        webhook_data: Grafana에서 전송한 웹훅 데이터
        background_tasks: 백그라운드 작업 처리
        
    Returns:
        처리 결과
    """
    # Grafana 라우터의 웹훅 핸들러를 재사용
    return await receive_grafana_webhook(webhook_data, background_tasks)

