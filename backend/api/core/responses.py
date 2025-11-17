"""
표준화된 API 응답 모델

모든 API 엔드포인트에서 일관된 응답 형식을 제공합니다.
"""

from typing import Optional, Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')


class ErrorDetail(BaseModel):
    """에러 상세 정보"""
    code: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")
    field: Optional[str] = Field(None, description="에러가 발생한 필드 (검증 오류인 경우)")


class ErrorResponse(BaseModel):
    """표준화된 에러 응답 모델"""
    success: bool = Field(False, description="요청 성공 여부")
    error: ErrorDetail = Field(..., description="에러 상세 정보")
    timestamp: Optional[str] = Field(None, description="에러 발생 시각")


class SuccessResponse(BaseModel, Generic[T]):
    """표준화된 성공 응답 모델"""
    success: bool = Field(True, description="요청 성공 여부")
    data: T = Field(..., description="응답 데이터")
    message: Optional[str] = Field(None, description="추가 메시지")


class PaginatedResponse(BaseModel, Generic[T]):
    """페이지네이션 응답 모델"""
    success: bool = Field(True, description="요청 성공 여부")
    data: list[T] = Field(..., description="데이터 리스트")
    total: int = Field(..., description="전체 항목 수")
    page: int = Field(..., description="현재 페이지 번호")
    page_size: int = Field(..., description="페이지 크기")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")
    has_prev: bool = Field(..., description="이전 페이지 존재 여부")

