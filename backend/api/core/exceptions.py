"""
커스텀 예외 클래스 정의

Alert Engine 및 기타 서비스에서 사용하는 표준 예외 클래스입니다.
"""

from typing import Any


class AlertEngineError(Exception):
    """Alert Engine 관련 기본 예외 클래스"""
    pass


class AlertValidationError(AlertEngineError):
    """알람 입력 데이터 검증 실패 예외"""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message)
        self.field = field
        self.value = value
        self.message = message


class AlertProcessingError(AlertEngineError):
    """알람 처리 중 발생한 예외"""
    
    def __init__(self, message: str, alert_id: str = None, sensor_id: str = None):
        super().__init__(message)
        self.alert_id = alert_id
        self.sensor_id = sensor_id
        self.message = message


class LLMSummaryError(AlertEngineError):
    """LLM 요약 생성 실패 예외"""
    
    def __init__(self, message: str, alert_id: str = None, original_error: Exception = None):
        super().__init__(message)
        self.alert_id = alert_id
        self.original_error = original_error
        self.message = message


class AnomalyVectorError(AlertEngineError):
    """이상 벡터 평가 중 발생한 예외"""
    
    def __init__(self, message: str, vector: list = None, threshold: float = None):
        super().__init__(message)
        self.vector = vector
        self.threshold = threshold
        self.message = message
