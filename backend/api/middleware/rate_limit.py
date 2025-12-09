"""
Rate Limiting 미들웨어

IP 기반 및 사용자별 Rate Limiting을 제공합니다.
"""

import time
import logging
from typing import Dict, Optional
from collections import defaultdict
from threading import Lock
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate Limiter 클래스"""

    def __init__(self):
        # IP별 요청 기록: {ip: [(timestamp, count), ...]}
        self._ip_requests: Dict[str, list] = defaultdict(list)
        # 사용자별 요청 기록: {user_id: [(timestamp, count), ...]}
        self._user_requests: Dict[str, list] = defaultdict(list)
        self._lock = Lock()

    def _cleanup_old_requests(self, requests: list, window_seconds: int) -> list:
        """오래된 요청 기록 정리"""
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        return [
            (ts, count) for ts, count in requests if ts > cutoff_time
        ]

    def _get_total_requests(self, requests: list, window_seconds: int) -> int:
        """시간 창 내 총 요청 수 계산"""
        cleaned = self._cleanup_old_requests(requests, window_seconds)
        return sum(count for _, count in cleaned)

    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int,
        requests_dict: Dict[str, list],
    ) -> tuple[bool, int, int]:
        """
        Rate Limit 체크

        Args:
            identifier: IP 주소 또는 사용자 ID
            max_requests: 최대 요청 수
            window_seconds: 시간 창 (초)
            requests_dict: 요청 기록 딕셔너리

        Returns:
            (allowed, remaining, reset_after): (허용 여부, 남은 요청 수, 리셋까지 남은 시간)
        """
        with self._lock:
            current_time = time.time()
            requests = requests_dict[identifier]

            # 오래된 요청 정리
            requests[:] = self._cleanup_old_requests(requests, window_seconds)

            # 총 요청 수 계산
            total_requests = self._get_total_requests(requests, window_seconds)

            # Rate Limit 체크
            if total_requests >= max_requests:
                # 가장 오래된 요청의 만료 시간 계산
                if requests:
                    oldest_timestamp = min(ts for ts, _ in requests)
                    reset_after = int(window_seconds - (current_time - oldest_timestamp))
                else:
                    reset_after = window_seconds

                return False, 0, reset_after

            # 새 요청 추가
            requests.append((current_time, 1))

            # 남은 요청 수 계산
            remaining = max(0, max_requests - total_requests - 1)

            # 리셋까지 남은 시간 (가장 오래된 요청 기준)
            if requests:
                oldest_timestamp = min(ts for ts, _ in requests)
                reset_after = int(window_seconds - (current_time - oldest_timestamp))
            else:
                reset_after = window_seconds

            return True, remaining, reset_after

    def check_ip_rate_limit(
        self, ip: str, max_requests: int = 100, window_seconds: int = 60
    ) -> tuple[bool, int, int]:
        """IP 기반 Rate Limit 체크"""
        return self.check_rate_limit(
            ip, max_requests, window_seconds, self._ip_requests
        )

    def check_user_rate_limit(
        self, user_id: str, max_requests: int = 200, window_seconds: int = 60
    ) -> tuple[bool, int, int]:
        """사용자별 Rate Limit 체크"""
        return self.check_rate_limit(
            user_id, max_requests, window_seconds, self._user_requests
        )


# 전역 Rate Limiter 인스턴스
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """전역 Rate Limiter 인스턴스 반환"""
    return _rate_limiter


def get_client_ip(request: Request) -> str:
    """클라이언트 IP 주소 추출"""
    # X-Forwarded-For 헤더 확인 (프록시/로드밸런서 뒤에 있을 경우)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # 첫 번째 IP 사용 (실제 클라이언트 IP)
        return forwarded_for.split(",")[0].strip()

    # X-Real-IP 헤더 확인
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 직접 연결인 경우
    if request.client:
        return request.client.host

    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate Limiting 미들웨어"""

    def __init__(self, app, default_limit: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.rate_limiter = get_rate_limiter()

    async def dispatch(self, request: Request, call_next):
        # 테스트 환경에서 rate limit 비활성화
        import os
        if os.getenv("DISABLE_RATE_LIMIT") == "true":
            return await call_next(request)
        
        # Health check 및 인증 엔드포인트는 제외 (성능 최적화)
        path = request.url.path
        if (path.startswith("/health") or 
            path.startswith("/metrics") or 
            path.startswith("/auth/login") or 
            path.startswith("/auth/register")):
            return await call_next(request)

        # IP 주소 추출
        client_ip = get_client_ip(request)

        # Rate Limit 체크
        allowed, remaining, reset_after = self.rate_limiter.check_ip_rate_limit(
            client_ip, self.default_limit, self.window_seconds
        )

        # Rate Limit 헤더 추가
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.default_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_after)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for IP: {client_ip}, "
                f"path: {request.url.path}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": "Rate limit exceeded",
                    "retry_after": reset_after,
                },
                headers={
                    "X-RateLimit-Limit": str(self.default_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_after),
                    "Retry-After": str(reset_after),
                },
            )

        return response

