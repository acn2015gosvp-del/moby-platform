"""
API 응답 시간 측정 미들웨어

각 요청의 응답 시간을 측정하고 로깅합니다.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from backend.api.services.schemas.models.core.logger import get_logger

logger = get_logger(__name__)


class TimingMiddleware(BaseHTTPMiddleware):
    """API 응답 시간 측정 미들웨어"""
    
    async def dispatch(self, request: Request, call_next):
        """요청 처리 시간 측정"""
        start_time = time.time()
        
        # 요청 처리
        response = await call_next(request)
        
        # 응답 시간 계산
        process_time = time.time() - start_time
        
        # 느린 요청만 로깅 (200ms 이상)
        if process_time > 0.2:
            logger.warning(
                f"⚠️ Slow API request: {request.method} {request.url.path} "
                f"took {process_time*1000:.1f}ms"
            )
        elif process_time > 1.0:
            logger.error(
                f"❌ Very slow API request: {request.method} {request.url.path} "
                f"took {process_time*1000:.1f}ms"
            )
        
        # 응답 헤더에 처리 시간 추가
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


