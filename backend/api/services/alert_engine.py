"""
알림 평가 엔진 모듈

오케스트레이터 역할을 수행하며, 이상 탐지 벡터 평가와 LLM 요약 생성 등을 조율합니다.
"""
from typing import Any, Dict, Optional
from schemas.alert_schema import AlertResponse
from services.alerts_summary import generate_alert_summary
from services.anomaly_vector_service import evaluate_anomaly_vector_with_severity
from schemas.models.core.logger import logger


# 기본 임계값 설정 (환경 변수나 설정 파일에서 가져올 수 있음)
DEFAULT_WARNING_THRESHOLD = 0.5
DEFAULT_CRITICAL_THRESHOLD = 0.7


def process_alert(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    알림 데이터를 처리하여 최종 알림 딕셔너리를 생성합니다.
    
    오케스트레이터 역할:
    1. 이상 벡터 norm 계산 및 심각도 판단
    2. 이상이 감지되면 LLM 요약 생성
    3. 최종 알림 딕셔너리 반환
    
    Args:
        alert_data: 처리할 알림 데이터 (dict)
            - vector: List[float] - 이상 탐지 벡터 (선택적)
            - warning_threshold: float - 경고 임계값 (선택적, 기본값: 0.5)
            - critical_threshold: float - 심각 임계값 (선택적, 기본값: 0.7)
            - 기타 알림 관련 메타데이터
            
    Returns:
        최종 알림 딕셔너리:
        {
            "level": str,           # "normal", "warning", "critical"
            "severity": str,        # "normal", "warning", "critical" (level과 동일)
            "is_anomaly": bool,     # 이상 여부
            "norm": float,          # 계산된 벡터 norm 값 (벡터가 있는 경우)
            "summary": str | None,  # LLM 요약 (이상이 있는 경우에만)
            "message": str,         # 알림 메시지
            ... 기타 alert_data의 필드들
        }
        
    Example:
        >>> alert_data = {
        ...     "vector": [0.4, 0.33],
        ...     "sensor_id": "temp_01",
        ...     "timestamp": "2025-01-01T10:00:00Z"
        ... }
        >>> result = process_alert(alert_data)
        >>> print(result["severity"])  # "warning" or "normal"
    """
    try:
        # 1. 벡터 추출 및 이상 탐지 평가
        vector = alert_data.get("vector")
        norm = None
        is_anomaly = False
        severity = "normal"
        level = "normal"
        
        if vector and isinstance(vector, list) and len(vector) > 0:
            # 벡터가 있는 경우 norm 계산 및 심각도 판단
            try:
                warning_threshold = alert_data.get(
                    "warning_threshold", 
                    DEFAULT_WARNING_THRESHOLD
                )
                critical_threshold = alert_data.get(
                    "critical_threshold", 
                    DEFAULT_CRITICAL_THRESHOLD
                )
                
                norm, is_anomaly, severity = evaluate_anomaly_vector_with_severity(
                    vector=vector,
                    warning_threshold=float(warning_threshold),
                    critical_threshold=float(critical_threshold)
                )
                level = severity
                
                logger.info(
                    f"Vector anomaly evaluated: norm={norm:.4f}, "
                    f"severity={severity}, is_anomaly={is_anomaly}"
                )
            except ValueError as e:
                logger.error(f"Invalid vector or threshold values: {e}")
                severity = "normal"
                level = "normal"
            except Exception as e:
                logger.error(f"Error evaluating vector anomaly: {e}")
                severity = "normal"
                level = "normal"
        else:
            # 벡터가 없는 경우 기존 anomaly_score나 다른 방식 사용 가능
            anomaly_score = alert_data.get("anomaly_score")
            if anomaly_score is not None:
                # 간단한 threshold 기반 판단 (벡터가 없는 경우)
                if anomaly_score > 0.8:
                    severity = "critical"
                    level = "critical"
                    is_anomaly = True
                elif anomaly_score > 0.5:
                    severity = "warning"
                    level = "warning"
                    is_anomaly = True
                else:
                    severity = "normal"
                    level = "normal"
                    is_anomaly = False
                logger.info(
                    f"Anomaly score evaluated: score={anomaly_score}, "
                    f"severity={severity}"
                )
        
        # 2. 이상이 감지된 경우에만 LLM 요약 생성
        summary = None
        if severity != "normal" and is_anomaly:
            try:
                # alert_data에 평가 결과 추가
                enhanced_alert_data = {
                    **alert_data,
                    "norm": norm,
                    "severity": severity,
                    "is_anomaly": is_anomaly
                }
                summary = generate_alert_summary(enhanced_alert_data)
                
                if summary:
                    logger.info(f"LLM summary generated for {severity} alert")
                else:
                    logger.warning("LLM summary generation returned None")
            except Exception as e:
                logger.error(f"Error generating LLM summary: {e}")
                summary = None
        
        # 3. 메시지 생성
        if severity == "critical":
            message = "Critical anomaly detected"
        elif severity == "warning":
            message = "Warning: Anomaly detected"
        else:
            message = "Normal operation"
        
        # 4. 최종 알림 딕셔너리 구성
        result = {
            "level": level,
            "severity": severity,
            "is_anomaly": is_anomaly,
            "message": message,
            "summary": summary,
            **{k: v for k, v in alert_data.items() 
               if k not in ["vector", "warning_threshold", "critical_threshold"]}
        }
        
        # norm이 계산된 경우 추가
        if norm is not None:
            result["norm"] = norm
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing alert: {e}")
        # 에러 발생 시 기본값 반환
        return {
            "level": "normal",
            "severity": "normal",
            "is_anomaly": False,
            "message": f"Error processing alert: {str(e)}",
            "summary": None,
            **{k: v for k, v in alert_data.items() 
               if k not in ["vector", "warning_threshold", "critical_threshold"]}
        }


def evaluate_alert(alert_data: Optional[Dict[str, Any]] = None) -> AlertResponse:
    """
    알림을 평가하고 AlertResponse 객체를 반환합니다.
    
    기존 API 호환성을 위한 래퍼 함수입니다.
    내부적으로 process_alert()를 호출하여 처리합니다.
    
    Args:
        alert_data: 처리할 알림 데이터 (dict)
            None인 경우 기본 더미 데이터 사용
            
    Returns:
        AlertResponse 객체
        
    Example:
        >>> response = evaluate_alert({"vector": [0.6, 0.5]})
        >>> print(response.status)  # "warning" or "critical"
    """
    if alert_data is None:
        # 기존 호환성을 위한 더미 데이터
        alert_data = {
            "anomaly_score": 0.82,
            "vector": [0.4, 0.33]
        }
    
    # process_alert로 처리
    result = process_alert(alert_data)
    
    # AlertResponse로 변환
    return AlertResponse(
        status=result.get("severity", "normal"),
        message=result.get("message", "Normal operation"),
        llm_summary=result.get("summary")
    )
