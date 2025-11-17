"""
이상 탐지 벡터 서비스 모듈

vector_norm 계산과 threshold 판단 로직을 분리하여 제공하는 서비스입니다.
벡터 기반 이상 탐지를 위한 norm 계산 및 임계값 판단 기능을 제공합니다.
"""

import math
from typing import List, Tuple


# ------------------------------------------------------
# 1) Norm 계산 함수
# ------------------------------------------------------

def calculate_vector_norm(vector: List[float]) -> float:
    """
    벡터의 L2 norm (유클리드 거리)을 계산합니다.

    Args:
        vector (List[float]): norm을 계산할 벡터

    Returns:
        float: 계산된 L2 norm 값

    Raises:
        ValueError: 벡터가 비어있거나 숫자가 아닌 값이 포함된 경우
    """
    if not vector:
        raise ValueError("Vector cannot be empty")
    if not all(isinstance(x, (int, float)) for x in vector):
        raise ValueError("Vector must contain only numeric values")

    sum_of_squares = sum(x * x for x in vector)
    return math.sqrt(sum_of_squares)


def calculate_vector_norm_squared(vector: List[float]) -> float:
    """
    벡터의 L2 norm의 제곱을 계산합니다. (성능 최적화용)

    Args:
        vector (List[float]): norm을 계산할 벡터

    Returns:
        float: 제곱된 L2 norm 값
    """
    if not vector:
        raise ValueError("Vector cannot be empty")
    if not all(isinstance(x, (int, float)) for x in vector):
        raise ValueError("Vector must contain only numeric values")

    return sum(x * x for x in vector)


# ------------------------------------------------------
# 2) Threshold 평가 함수
# ------------------------------------------------------

def check_threshold(norm: float, threshold: float) -> bool:
    """
    계산된 norm이 threshold를 초과하는지 판단합니다.

    Args:
        norm (float): 계산된 벡터의 norm 값
        threshold (float): 임계값

    Returns:
        bool: threshold 초과 여부
    """
    if threshold < 0:
        raise ValueError("Threshold must be non-negative")

    return norm > threshold


def check_threshold_with_severity(
    norm: float,
    warning_threshold: float,
    critical_threshold: float
) -> Tuple[bool, str]:
    """
    norm에 대해 경고/심각 수준을 판단합니다.

    Args:
        norm (float): 계산된 norm
        warning_threshold (float): 경고 임계값
        critical_threshold (float): 심각 임계값

    Returns:
        Tuple[bool, str]:
            - is_anomaly (bool)
            - severity ("normal", "warning", "critical")

    Raises:
        ValueError: 임계값이 잘못된 경우
    """
    if warning_threshold < 0 or critical_threshold < 0:
        raise ValueError("Thresholds must be non-negative")
    if critical_threshold <= warning_threshold:
        raise ValueError("Critical threshold must be greater than warning threshold")

    if norm > critical_threshold:
        return True, "critical"
    elif norm > warning_threshold:
        return True, "warning"
    else:
        return False, "normal"


# ------------------------------------------------------
# 3) 통합 평가 함수
# ------------------------------------------------------

def evaluate_anomaly_vector(
    vector: List[float],
    threshold: float
) -> Tuple[float, bool]:
    """
    벡터의 norm을 계산하고 임계값 기준으로 이상 여부를 반환합니다.

    Args:
        vector (List[float]): 평가 대상 벡터
        threshold (float): 임계값

    Returns:
        Tuple[float, bool]:
            - norm (float): 계산된 norm
            - is_anomaly (bool): 이상 여부
    """
    norm = calculate_vector_norm(vector)
    is_anomaly = check_threshold(norm, threshold)
    return norm, is_anomaly


def evaluate_anomaly_vector_with_severity(
    vector: List[float],
    warning_threshold: float,
    critical_threshold: float
) -> Tuple[float, bool, str]:
    """
    벡터의 norm을 계산하고 경고/심각도까지 포함한 이상 평가 결과를 반환합니다.

    Args:
        vector (List[float]): 평가 대상 벡터
        warning_threshold (float): 경고 임계값
        critical_threshold (float): 심각 임계값

    Returns:
        Tuple[float, bool, str]:
            - norm (float): 계산된 norm
            - is_anomaly (bool): 이상 여부
            - severity (str): "normal", "warning", "critical"
    """
    norm = calculate_vector_norm(vector)
    is_anomaly, severity = check_threshold_with_severity(
        norm, warning_threshold, critical_threshold
    )
    return norm, is_anomaly, severity
