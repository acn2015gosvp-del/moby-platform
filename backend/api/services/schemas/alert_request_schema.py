"""
알림 요청 스키마

API 엔드포인트에서 받는 알림 입력 데이터 구조를 정의합니다.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class AlertRequest(BaseModel):
    """알림 생성 요청 스키마"""
    
    id: Optional[str] = None
    sensor_id: str = Field(default="unknown_sensor", description="센서 ID")
    source: Optional[str] = Field(default="alert-engine", description="알림 소스")
    ts: Optional[str] = None
    vector: List[float] = Field(..., description="이상 탐지 벡터")
    threshold: Optional[float] = Field(None, description="단일 임계값")
    warning_threshold: Optional[float] = Field(None, description="경고 임계값")
    critical_threshold: Optional[float] = Field(None, description="심각 임계값")
    message: Optional[str] = Field(default="Anomaly detected", description="알림 메시지")
    enable_llm_summary: bool = Field(default=True, description="LLM 요약 생성 여부")
    meta: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")

