"""
anomaly_vector_service 모듈 단위 테스트
"""

import pytest
import math
from backend.api.services.anomaly_vector_service import (
    calculate_vector_norm,
    calculate_vector_norm_squared,
    check_threshold,
    check_threshold_with_severity,
    evaluate_anomaly_vector,
    evaluate_anomaly_vector_with_severity,
)


class TestCalculateVectorNorm:
    """calculate_vector_norm 함수 테스트"""

    def test_normal_vector(self):
        """정상적인 벡터의 norm 계산"""
        vector = [3.0, 4.0]
        result = calculate_vector_norm(vector)
        assert result == 5.0  # 3^2 + 4^2 = 25, sqrt(25) = 5

    def test_single_element_vector(self):
        """단일 요소 벡터"""
        vector = [5.0]
        result = calculate_vector_norm(vector)
        assert result == 5.0

    def test_zero_vector(self):
        """영 벡터"""
        vector = [0.0, 0.0, 0.0]
        result = calculate_vector_norm(vector)
        assert result == 0.0

    def test_negative_values(self):
        """음수 값 포함 벡터"""
        vector = [-3.0, 4.0]
        result = calculate_vector_norm(vector)
        assert result == 5.0  # (-3)^2 + 4^2 = 25

    def test_multi_dimensional_vector(self):
        """다차원 벡터"""
        vector = [1.0, 2.0, 3.0]
        result = calculate_vector_norm(vector)
        expected = math.sqrt(1.0 + 4.0 + 9.0)  # sqrt(14)
        assert abs(result - expected) < 1e-10

    def test_empty_vector_raises_error(self):
        """빈 벡터는 ValueError 발생"""
        with pytest.raises(ValueError, match="Vector cannot be empty"):
            calculate_vector_norm([])

    def test_non_numeric_vector_raises_error(self):
        """숫자가 아닌 값 포함 시 ValueError 발생"""
        with pytest.raises(ValueError, match="Vector must contain only numeric values"):
            calculate_vector_norm([1.0, "invalid", 3.0])


class TestCalculateVectorNormSquared:
    """calculate_vector_norm_squared 함수 테스트"""

    def test_normal_vector(self):
        """정상적인 벡터의 norm 제곱 계산"""
        vector = [3.0, 4.0]
        result = calculate_vector_norm_squared(vector)
        assert result == 25.0  # 3^2 + 4^2 = 25

    def test_single_element_vector(self):
        """단일 요소 벡터"""
        vector = [5.0]
        result = calculate_vector_norm_squared(vector)
        assert result == 25.0

    def test_empty_vector_raises_error(self):
        """빈 벡터는 ValueError 발생"""
        with pytest.raises(ValueError, match="Vector cannot be empty"):
            calculate_vector_norm_squared([])


class TestCheckThreshold:
    """check_threshold 함수 테스트"""

    def test_norm_exceeds_threshold(self):
        """norm이 threshold 초과"""
        assert check_threshold(5.0, 3.0) is True

    def test_norm_equals_threshold(self):
        """norm이 threshold와 같음"""
        assert check_threshold(5.0, 5.0) is False  # norm > threshold이므로 False

    def test_norm_below_threshold(self):
        """norm이 threshold 미만"""
        assert check_threshold(3.0, 5.0) is False

    def test_zero_threshold(self):
        """threshold가 0인 경우"""
        assert check_threshold(0.1, 0.0) is True
        assert check_threshold(0.0, 0.0) is False

    def test_negative_threshold_raises_error(self):
        """음수 threshold는 ValueError 발생"""
        with pytest.raises(ValueError, match="Threshold must be non-negative"):
            check_threshold(5.0, -1.0)


class TestCheckThresholdWithSeverity:
    """check_threshold_with_severity 함수 테스트"""

    def test_critical_severity(self):
        """norm이 critical threshold 초과"""
        is_anomaly, severity = check_threshold_with_severity(10.0, 5.0, 8.0)
        assert is_anomaly is True
        assert severity == "critical"

    def test_warning_severity(self):
        """norm이 warning threshold 초과, critical 미만"""
        is_anomaly, severity = check_threshold_with_severity(6.0, 5.0, 8.0)
        assert is_anomaly is True
        assert severity == "warning"

    def test_normal_severity(self):
        """norm이 warning threshold 미만"""
        is_anomaly, severity = check_threshold_with_severity(3.0, 5.0, 8.0)
        assert is_anomaly is False
        assert severity == "normal"

    def test_exactly_warning_threshold(self):
        """norm이 warning threshold와 정확히 같음"""
        is_anomaly, severity = check_threshold_with_severity(5.0, 5.0, 8.0)
        assert is_anomaly is False  # norm > warning_threshold이므로 False (정확히 같으면 False)
        assert severity == "normal"

    def test_exactly_critical_threshold(self):
        """norm이 critical threshold와 정확히 같음"""
        is_anomaly, severity = check_threshold_with_severity(8.0, 5.0, 8.0)
        # norm == critical_threshold이면 norm > critical_threshold는 False,
        # 하지만 norm > warning_threshold는 True이므로 warning
        assert is_anomaly is True
        assert severity == "warning"

    def test_negative_thresholds_raise_error(self):
        """음수 threshold는 ValueError 발생"""
        with pytest.raises(ValueError, match="Thresholds must be non-negative"):
            check_threshold_with_severity(5.0, -1.0, 8.0)

    def test_critical_less_than_warning_raises_error(self):
        """critical threshold가 warning보다 작거나 같으면 ValueError 발생"""
        with pytest.raises(ValueError, match="Critical threshold must be greater than warning threshold"):
            check_threshold_with_severity(5.0, 8.0, 5.0)


class TestEvaluateAnomalyVector:
    """evaluate_anomaly_vector 함수 테스트"""

    def test_anomaly_detected(self):
        """이상 탐지 성공"""
        vector = [3.0, 4.0]  # norm = 5.0
        threshold = 3.0
        norm, is_anomaly = evaluate_anomaly_vector(vector, threshold)
        assert norm == 5.0
        assert is_anomaly is True

    def test_no_anomaly(self):
        """이상 없음"""
        vector = [1.0, 1.0]  # norm = sqrt(2) ≈ 1.414
        threshold = 3.0
        norm, is_anomaly = evaluate_anomaly_vector(vector, threshold)
        assert abs(norm - math.sqrt(2)) < 1e-10
        assert is_anomaly is False

    def test_empty_vector_raises_error(self):
        """빈 벡터는 ValueError 발생"""
        with pytest.raises(ValueError):
            evaluate_anomaly_vector([], 3.0)


class TestEvaluateAnomalyVectorWithSeverity:
    """evaluate_anomaly_vector_with_severity 함수 테스트"""

    def test_critical_anomaly(self):
        """심각한 이상 탐지"""
        vector = [10.0, 0.0]  # norm = 10.0
        warning_threshold = 5.0
        critical_threshold = 8.0
        norm, is_anomaly, severity = evaluate_anomaly_vector_with_severity(
            vector, warning_threshold, critical_threshold
        )
        assert norm == 10.0
        assert is_anomaly is True
        assert severity == "critical"

    def test_warning_anomaly(self):
        """경고 수준 이상 탐지"""
        vector = [6.0, 0.0]  # norm = 6.0
        warning_threshold = 5.0
        critical_threshold = 8.0
        norm, is_anomaly, severity = evaluate_anomaly_vector_with_severity(
            vector, warning_threshold, critical_threshold
        )
        assert norm == 6.0
        assert is_anomaly is True
        assert severity == "warning"

    def test_normal_no_anomaly(self):
        """정상 상태, 이상 없음"""
        vector = [3.0, 0.0]  # norm = 3.0
        warning_threshold = 5.0
        critical_threshold = 8.0
        norm, is_anomaly, severity = evaluate_anomaly_vector_with_severity(
            vector, warning_threshold, critical_threshold
        )
        assert norm == 3.0
        assert is_anomaly is False
        assert severity == "normal"

    def test_empty_vector_raises_error(self):
        """빈 벡터는 ValueError 발생"""
        with pytest.raises(ValueError):
            evaluate_anomaly_vector_with_severity([], 5.0, 8.0)

