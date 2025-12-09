"""
API 예외 클래스 정의

FastAPI에서 사용하는 HTTP 예외를 표준화합니다.
"""

from fastapi import HTTPException, status
from typing import Optional
from .responses import ErrorDetail, ErrorResponse


class APIException(HTTPException):
    """표준화된 API 예외 클래스"""
    
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        field: Optional[str] = None,
        headers: Optional[dict] = None
    ):
        """
        Args:
            status_code: HTTP 상태 코드
            error_code: 애플리케이션 레벨 에러 코드
            message: 에러 메시지
            field: 에러가 발생한 필드 (검증 오류인 경우)
            headers: 추가 HTTP 헤더
        """
        super().__init__(status_code=status_code, detail=message, headers=headers)
        self.error_code = error_code
        self.field = field
    
    def to_error_response(self) -> ErrorResponse:
        """ErrorResponse 모델로 변환"""
        from datetime import datetime
        
        return ErrorResponse(
            success=False,
            error=ErrorDetail(
                code=self.error_code,
                message=self.detail,
                field=self.field
            ),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )


class ValidationError(APIException):
    """입력 데이터 검증 오류"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            message=message,
            field=field
        )


class NotFoundError(APIException):
    """리소스를 찾을 수 없음"""
    
    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            message=message
        )


class InternalServerError(APIException):
    """내부 서버 오류"""
    
    def __init__(self, message: str = "Internal server error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_ERROR",
            message=message
        )


class BadRequestError(APIException):
    """잘못된 요청"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BAD_REQUEST",
            message=message,
            field=field
        )


class UnauthorizedError(APIException):
    """인증 실패"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
            message=message
        )

