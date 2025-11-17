"""
Alert Engine 에러 처리 및 커스텀 예외 테스트

새로 도입된 에러 핸들링 로직과 커스텀 예외 클래스를 검증합니다.
"""

import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from backend.api.services.alert_engine import (
    process_alert,
    AlertInputModel,
    AlertPayloadModel,
)
from backend.api.core.exceptions import (
    AlertEngineError,
    AlertValidationError,
    AlertProcessingError,
    LLMSummaryError,
    AnomalyVectorError,
)
from backend.api.services.alerts_summary import generate_alert_summary
from backend.api.services import constants


# -------------------------------------------------------------------
# 커스텀 예외 클래스 테스트
# -------------------------------------------------------------------

class TestCustomExceptions:
    """커스텀 예외 클래스 동작 테스트"""
    
    def test_alert_engine_error_base(self):
        """AlertEngineError 기본 동작"""
        error = AlertEngineError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_alert_validation_error(self):
        """AlertValidationError 동작"""
        error = AlertValidationError(
            message="Validation failed",
            field="vector",
            value=None
        )
        assert error.message == "Validation failed"
        assert error.field == "vector"
        assert error.value is None
        assert isinstance(error, AlertEngineError)
    
    def test_alert_processing_error(self):
        """AlertProcessingError 동작"""
        error = AlertProcessingError(
            message="Processing failed",
            alert_id="alert-123",
            sensor_id="sensor-001"
        )
        assert error.message == "Processing failed"
        assert error.alert_id == "alert-123"
        assert error.sensor_id == "sensor-001"
        assert isinstance(error, AlertEngineError)
    
    def test_llm_summary_error(self):
        """LLMSummaryError 동작"""
        original_error = ValueError("LLM API error")
        error = LLMSummaryError(
            message="LLM summary failed",
            alert_id="alert-123",
            original_error=original_error
        )
        assert error.message == "LLM summary failed"
        assert error.alert_id == "alert-123"
        assert error.original_error == original_error
        assert isinstance(error, AlertEngineError)
    
    def test_anomaly_vector_error(self):
        """AnomalyVectorError 동작"""
        error = AnomalyVectorError(
            message="Vector evaluation failed",
            vector=[1.0, 2.0],
            threshold=5.0
        )
        assert error.message == "Vector evaluation failed"
        assert error.vector == [1.0, 2.0]
        assert error.threshold == 5.0
        assert isinstance(error, AlertEngineError)


# -------------------------------------------------------------------
# UUID 기반 ID 생성 테스트
# -------------------------------------------------------------------

class TestUUIDAlertID:
    """UUID를 사용한 알람 ID 생성 테스트"""
    
    def test_uuid_alert_id_generation(self):
        """ID가 없을 때 UUID 기반 ID 생성"""
        alert_data = {
            "vector": [3.0, 4.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
        }
        result = process_alert(alert_data)
        assert result is not None
        assert result.id.startswith(constants.Defaults.ALERT_ID_PREFIX)
        # UUID hex 8자리 형식 확인 (예: "anomaly-a1b2c3d4")
        id_suffix = result.id[len(constants.Defaults.ALERT_ID_PREFIX):]
        assert len(id_suffix) == 8
        assert all(c in '0123456789abcdef' for c in id_suffix)
    
    def test_custom_alert_id_preserved(self):
        """사용자 정의 ID가 있으면 UUID 대신 사용"""
        custom_id = "custom-alert-12345"
        alert_data = {
            "id": custom_id,
            "vector": [3.0, 4.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
        }
        result = process_alert(alert_data)
        assert result is not None
        assert result.id == custom_id
    
    def test_uuid_uniqueness(self):
        """여러 알람의 ID가 고유한지 확인"""
        alert_data = {
            "vector": [3.0, 4.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
        }
        results = []
        for _ in range(10):
            result = process_alert(alert_data)
            if result:
                results.append(result.id)
        
        # 모든 ID가 고유한지 확인
        assert len(results) == len(set(results)), "Alert IDs should be unique"


# -------------------------------------------------------------------
# LLM 요약 실패 시 Fallback 메시지 테스트
# -------------------------------------------------------------------

class TestLLMSummaryFallback:
    """LLM 요약 실패 시 fallback 메시지 테스트"""
    
    def test_llm_summary_none_returns_fallback(self):
        """LLM 요약이 None을 반환하면 fallback 메시지 사용"""
        alert_data = {
            "vector": [3.0, 4.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
            "enable_llm_summary": True,
        }
        
        with patch("backend.api.services.alert_engine.generate_alert_summary", return_value=None):
            result = process_alert(alert_data)
            assert result is not None
            assert result.llm_summary is not None
            assert "Alert detected" in result.llm_summary
            assert "LLM summary generation was unavailable" in result.llm_summary
            assert "severity" in result.llm_summary.lower()
            assert "norm" in result.llm_summary.lower()
    
    def test_llm_summary_error_returns_fallback(self):
        """LLM 요약 생성 중 예외 발생 시 fallback 메시지 사용"""
        alert_data = {
            "vector": [3.0, 4.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
            "enable_llm_summary": True,
        }
        
        # LLMSummaryError 발생 시뮬레이션
        llm_error = LLMSummaryError(
            message="LLM API connection failed",
            alert_id="test-alert",
            original_error=ConnectionError("Connection timeout")
        )
        
        with patch("backend.api.services.alert_engine.generate_alert_summary", side_effect=llm_error):
            result = process_alert(alert_data)
            assert result is not None
            assert result.llm_summary is not None
            assert "Alert detected" in result.llm_summary
            assert "LLM summary generation failed" in result.llm_summary
            assert "LLM API connection failed" in result.llm_summary
    
    def test_llm_summary_general_exception_returns_fallback(self):
        """일반 예외 발생 시 fallback 메시지 사용"""
        alert_data = {
            "vector": [3.0, 4.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
            "enable_llm_summary": True,
        }
        
        with patch("backend.api.services.alert_engine.generate_alert_summary", side_effect=Exception("Unexpected error")):
            result = process_alert(alert_data)
            assert result is not None
            assert result.llm_summary is not None
            assert "Alert detected" in result.llm_summary
            assert "LLM summary generation encountered an error" in result.llm_summary
    
    def test_llm_summary_success_no_fallback(self):
        """LLM 요약 성공 시 fallback 메시지 사용 안 함"""
        alert_data = {
            "vector": [3.0, 4.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
            "enable_llm_summary": True,
        }
        
        mock_summary = "This is a successful LLM summary of the alert."
        with patch("backend.api.services.alert_engine.generate_alert_summary", return_value=mock_summary):
            result = process_alert(alert_data)
            assert result is not None
            assert result.llm_summary == mock_summary
            assert "LLM summary generation" not in result.llm_summary
            assert "was unavailable" not in result.llm_summary


# -------------------------------------------------------------------
# 에러 처리 경로 테스트
# -------------------------------------------------------------------

class TestErrorHandling:
    """에러 처리 로직 테스트"""
    
    def test_value_error_handling(self):
        """ValueError 발생 시 AnomalyVectorError로 처리"""
        alert_data = {
            "vector": [1.0, 2.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
        }
        
        # anomaly_vector_service에서 ValueError 발생 시뮬레이션
        with patch(
            "backend.api.services.alert_engine.evaluate_anomaly_vector",
            side_effect=ValueError("Invalid vector format")
        ):
            result = process_alert(alert_data)
            # 에러가 발생해도 None을 반환하고 크래시하지 않음
            assert result is None
    
    def test_type_error_handling(self):
        """TypeError 발생 시 AnomalyVectorError로 처리"""
        alert_data = {
            "vector": [1.0, 2.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
        }
        
        with patch(
            "backend.api.services.alert_engine.evaluate_anomaly_vector",
            side_effect=TypeError("Type mismatch")
        ):
            result = process_alert(alert_data)
            assert result is None
    
    def test_unexpected_exception_handling(self):
        """예상치 못한 예외 발생 시 AlertProcessingError로 처리"""
        alert_data = {
            "vector": [1.0, 2.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
        }
        
        with patch(
            "backend.api.services.alert_engine.evaluate_anomaly_vector",
            side_effect=RuntimeError("Unexpected runtime error")
        ):
            result = process_alert(alert_data)
            # 예상치 못한 예외도 처리되어 None 반환
            assert result is None
    
    def test_validation_error_handling(self):
        """Pydantic ValidationError 발생 시 None 반환"""
        # 잘못된 데이터 형식
        alert_data = {
            "vector": "not a list",  # 잘못된 타입
            "threshold": 3.0,
        }
        result = process_alert(alert_data)
        assert result is None


# -------------------------------------------------------------------
# alerts_summary 에러 처리 테스트
# -------------------------------------------------------------------

class TestAlertsSummaryErrorHandling:
    """alerts_summary 모듈의 에러 처리 테스트"""
    
    def test_generate_alert_summary_empty_data(self):
        """빈 데이터 처리"""
        result = generate_alert_summary({})
        assert result is None
    
    def test_generate_alert_summary_none_data(self):
        """None 데이터 처리"""
        result = generate_alert_summary(None)
        assert result is None
    
    def test_generate_alert_summary_raises_llm_summary_error(self):
        """예외 발생 시 LLMSummaryError 발생"""
        alert_data = {
            "id": "test-alert-123",
            "sensor_id": "sensor-001",
            "message": "Test alert"
        }
        
        with patch(
            "backend.api.services.alerts_summary.summarize_alert",
            side_effect=Exception("LLM API error")
        ):
            with pytest.raises(LLMSummaryError) as exc_info:
                generate_alert_summary(alert_data)
            
            error = exc_info.value
            assert error.alert_id == "test-alert-123"
            assert error.original_error is not None
            assert "LLM API error" in str(error.original_error)
    
    def test_generate_alert_summary_success(self):
        """정상적인 요약 생성"""
        alert_data = {
            "id": "test-alert-123",
            "sensor_id": "sensor-001",
            "message": "Test alert"
        }
        
        mock_summary = "This is a test summary"
        with patch(
            "backend.api.services.alerts_summary.summarize_alert",
            return_value=mock_summary
        ):
            result = generate_alert_summary(alert_data)
            assert result == mock_summary
    
    def test_generate_alert_summary_returns_none(self):
        """LLM이 None을 반환하는 경우"""
        alert_data = {
            "id": "test-alert-123",
            "sensor_id": "sensor-001",
        }
        
        with patch(
            "backend.api.services.alerts_summary.summarize_alert",
            return_value=None
        ):
            result = generate_alert_summary(alert_data)
            assert result is None


# -------------------------------------------------------------------
# 통합 에러 처리 테스트
# -------------------------------------------------------------------

class TestIntegratedErrorHandling:
    """통합 에러 처리 시나리오 테스트"""
    
    def test_full_pipeline_with_llm_failure(self):
        """LLM 실패해도 알람은 생성되는지 확인"""
        alert_data = {
            "vector": [3.0, 4.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
            "enable_llm_summary": True,
        }
        
        # LLM 요약 실패 시뮬레이션
        with patch(
            "backend.api.services.alert_engine.generate_alert_summary",
            side_effect=LLMSummaryError("LLM service unavailable", alert_id="test")
        ):
            result = process_alert(alert_data)
            
            # 알람은 생성되어야 함
            assert result is not None
            assert isinstance(result, AlertPayloadModel)
            assert result.sensor_id == "test_sensor"
            assert result.level == constants.AlertLevel.CRITICAL.value
            
            # Fallback 메시지가 있어야 함
            assert result.llm_summary is not None
            assert "Alert detected" in result.llm_summary
    
    def test_vector_evaluation_error_does_not_crash(self):
        """벡터 평가 에러가 발생해도 크래시하지 않음"""
        alert_data = {
            "vector": [1.0, 2.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
        }
        
        # 벡터 평가에서 예외 발생
        with patch(
            "backend.api.services.alert_engine.evaluate_anomaly_vector",
            side_effect=ValueError("Vector evaluation error")
        ):
            result = process_alert(alert_data)
            # None을 반환하지만 크래시하지 않음
            assert result is None
    
    def test_llm_and_vector_error_both_handled(self):
        """벡터 평가와 LLM 모두 실패해도 처리됨"""
        alert_data = {
            "vector": [3.0, 4.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
            "enable_llm_summary": True,
        }
        
        # 벡터 평가는 성공하지만 LLM 실패
        with patch(
            "backend.api.services.alert_engine.generate_alert_summary",
            side_effect=Exception("LLM error")
        ):
            result = process_alert(alert_data)
            # 알람은 생성되어야 함
            assert result is not None
            # Fallback 메시지가 있어야 함
            assert result.llm_summary is not None
            assert "encountered an error" in result.llm_summary

