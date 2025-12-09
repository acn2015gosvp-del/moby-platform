"""
CSRF 방지 미들웨어

Cross-Site Request Forgery (CSRF) 공격을 방지하기 위한 미들웨어입니다.
"""

import secrets
import logging
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF 방지 미들웨어"""

    # 안전한 HTTP 메서드 (CSRF 체크 불필요)
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    def __init__(self, app, secret_key: str, cookie_name: str = "csrf_token"):
        """
        Args:
            app: FastAPI 애플리케이션
            secret_key: CSRF 토큰 서명을 위한 시크릿 키
            cookie_name: CSRF 토큰 쿠키 이름
        """
        super().__init__(app)
        self.secret_key = secret_key
        self.cookie_name = cookie_name

    def _generate_token(self) -> str:
        """CSRF 토큰 생성"""
        return secrets.token_urlsafe(32)

    def _get_token_from_cookie(self, request: Request) -> Optional[str]:
        """쿠키에서 CSRF 토큰 조회"""
        return request.cookies.get(self.cookie_name)

    def _get_token_from_header(self, request: Request) -> Optional[str]:
        """헤더에서 CSRF 토큰 조회"""
        return request.headers.get("X-CSRF-Token")

    def _should_skip_csrf_check(self, request: Request) -> bool:
        """
        CSRF 체크를 건너뛸지 결정
        
        Args:
            request: HTTP 요청
            
        Returns:
            건너뛰면 True, 체크해야 하면 False
        """
        # 안전한 메서드는 체크 불필요
        if request.method in self.SAFE_METHODS:
            return True

        # Health check 및 metrics 엔드포인트는 제외
        path = request.url.path
        if path.startswith("/health") or path.startswith("/metrics"):
            return True

        # 인증 엔드포인트는 제외 (로그인, 회원가입 등)
        if path.startswith("/auth/login") or path.startswith("/auth/register"):
            return True

        return False

    async def dispatch(self, request: Request, call_next):
        """
        요청을 처리하고 CSRF 체크를 수행합니다.
        
        Args:
            request: HTTP 요청
            call_next: 다음 미들웨어/핸들러 호출 함수
            
        Returns:
            HTTP 응답
            
        Raises:
            HTTPException: CSRF 토큰이 유효하지 않은 경우 403 Forbidden
        """
        # CSRF 체크 건너뛰기
        if self._should_skip_csrf_check(request):
            response = await call_next(request)
            # GET 요청 시 CSRF 토큰을 쿠키로 설정
            if request.method == "GET" and not self._get_token_from_cookie(request):
                token = self._generate_token()
                response.set_cookie(
                    key=self.cookie_name,
                    value=token,
                    httponly=False,  # JavaScript에서 접근 가능하도록
                    samesite="lax",
                    secure=False,  # HTTPS 사용 시 True로 변경
                    max_age=3600,  # 1시간
                )
            return response

        # CSRF 토큰 검증
        cookie_token = self._get_token_from_cookie(request)
        header_token = self._get_token_from_header(request)

        if not cookie_token or not header_token:
            logger.warning(
                f"CSRF token missing. Method: {request.method}, "
                f"Path: {request.url.path}, "
                f"Cookie token: {bool(cookie_token)}, "
                f"Header token: {bool(header_token)}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing or invalid"
            )

        if cookie_token != header_token:
            logger.warning(
                f"CSRF token mismatch. Method: {request.method}, "
                f"Path: {request.url.path}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token mismatch"
            )

        # CSRF 체크 통과
        response = await call_next(request)
        return response

