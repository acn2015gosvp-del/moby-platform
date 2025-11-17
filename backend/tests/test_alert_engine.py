"""
alert_engine 모듈 단위 테스트
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from backend.api.services.alert_engine import (
    process_alert,
    evaluate_alert,
    AlertInputModel,
    AlertPayloadModel,
    AlertDetailsModel,
)
from backend.api.services import constants


class TestAlertInputModel:
    """AlertInputModel 검증 테스트"""

    def test_valid_input_with_single_threshold(self):
        """단일 threshold 입력 검증"""
        data = {
            "vector": [1.0, 2.0, 3.0],
            "threshold": 5.0,
            "sensor_id": "sensor_001",
        }
        model = AlertInputModel(**data)
        assert model.vector == [1.0, 2.0, 3.0]
        assert model.threshold == 5.0
        assert model.sensor_id == "sensor_001"

    def test_valid_input_with_dual_thresholds(self):
        """warning/critical threshold 입력 검증"""
        data = {
            "vector": [1.0, 2.0, 3.0],
            "warning_threshold": 3.0,
            "critical_threshold": 5.0,
        }
        model = AlertInputModel(**data)
        assert model.warning_threshold == 3.0
        assert model.critical_threshold == 5.0

    def test_empty_vector_raises_error(self):
        """빈 벡터는 ValueError 발생"""
        with pytest.raises(ValueError, match="Vector must not be empty"):
            AlertInputModel(vector=[], threshold=5.0)

    def test_missing_thresholds_raises_error(self):
        """threshold가 모두 없으면 ValueError 발생"""
        with pytest.raises(ValueError, match="Either 'threshold' or both 'warning_threshold' and 'critical_threshold' must be provided"):
            AlertInputModel(vector=[1.0, 2.0])

    def test_default_values(self):
        """기본값 확인"""
        data = {"vector": [1.0, 2.0], "threshold": 5.0}
        model = AlertInputModel(**data)
        assert model.sensor_id == constants.Defaults.SENSOR_ID
        assert model.source == constants.Defaults.SOURCE
        assert model.message == constants.Defaults.MESSAGE
        assert model.enable_llm_summary is True


class TestProcessAlert:
    """process_alert 함수 테스트"""

    def test_normal_case_no_anomaly(self):
        """정상 상태, 이상 없음"""
        alert_data = {
            "vector": [1.0, 1.0],  # norm ≈ 1.414
            "threshold": 5.0,
            "sensor_id": "test_sensor",
        }
        result = process_alert(alert_data)
        assert result is None  # 이상이 없으므로 None 반환

    def test_anomaly_detected_with_single_threshold(self):
        """단일 threshold로 이상 탐지"""
        alert_data = {
            "vector": [3.0, 4.0],  # norm = 5.0
            "threshold": 3.0,
            "sensor_id": "test_sensor",
        }
        result = process_alert(alert_data)
        assert result is not None
        assert isinstance(result, AlertPayloadModel)
        assert result.sensor_id == "test_sensor"
        assert result.level == constants.AlertLevel.CRITICAL.value
        assert result.details.norm == 5.0
        assert result.details.severity == constants.Severity.CRITICAL.value

    def test_anomaly_detected_with_dual_thresholds_warning(self):
        """warning threshold로 이상 탐지"""
        alert_data = {
            "vector": [6.0, 0.0],  # norm = 6.0
            "warning_threshold": 5.0,
            "critical_threshold": 8.0,
            "sensor_id": "test_sensor",
        }
        result = process_alert(alert_data)
        assert result is not None
        assert isinstance(result, AlertPayloadModel)
        assert result.level == constants.AlertLevel.WARNING.value
        assert result.details.severity == constants.Severity.WARNING.value

    def test_anomaly_detected_with_dual_thresholds_critical(self):
        """critical threshold로 이상 탐지"""
        alert_data = {
            "vector": [10.0, 0.0],  # norm = 10.0
            "warning_threshold": 5.0,
            "critical_threshold": 8.0,
            "sensor_id": "test_sensor",
        }
        result = process_alert(alert_data)
        assert result is not None
        assert isinstance(result, AlertPayloadModel)
        assert result.level == constants.AlertLevel.CRITICAL.value
        assert result.details.severity == constants.Severity.CRITICAL.value

    def test_invalid_input_returns_none(self):
        """잘못된 입력은 None 반환"""
        alert_data = {
            "vector": [],  # 빈 벡터
            "threshold": 5.0,
        }
        result = process_alert(alert_data)
        assert result is None

    def test_custom_alert_id(self):
        """사용자 정의 alert ID"""
        alert_id = "custom-alert-123"
        alert_data = {
            "id": alert_id,
            "vector": [3.0, 4.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
        }
        result = process_alert(alert_data)
        assert result is not None
        assert result.id == alert_id

    def test_custom_timestamp(self):
        """사용자 정의 타임스탬프"""
        ts = "2025-11-17T10:00:00Z"
        alert_data = {
            "vector": [3.0, 4.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
            "ts": ts,
        }
        result = process_alert(alert_data)
        assert result is not None
        assert result.ts == ts

    def test_llm_summary_disabled(self):
        """LLM 요약 비활성화"""
        alert_data = {
            "vector": [3.0, 4.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
            "enable_llm_summary": False,
        }
        with patch("backend.api.services.alert_engine.generate_alert_summary") as mock_llm:
            result = process_alert(alert_data)
            assert result is not None
            mock_llm.assert_not_called()  # LLM 요약이 호출되지 않아야 함

    def test_llm_summary_enabled(self):
        """LLM 요약 활성화"""
        alert_data = {
            "vector": [3.0, 4.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
            "enable_llm_summary": True,
        }
        mock_summary = "테스트 요약"
        with patch("backend.api.services.alert_engine.generate_alert_summary", return_value=mock_summary):
            result = process_alert(alert_data)
            assert result is not None
            assert result.llm_summary == mock_summary

    def test_llm_summary_failure_graceful_degradation(self):
        """LLM 요약 실패 시에도 알람은 생성됨"""
        alert_data = {
            "vector": [3.0, 4.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
            "enable_llm_summary": True,
        }
        with patch("backend.api.services.alert_engine.generate_alert_summary", side_effect=Exception("LLM Error")):
            result = process_alert(alert_data)
            assert result is not None
            assert result.llm_summary is None  # 실패 시 None

    def test_meta_data_preserved(self):
        """메타 데이터 보존"""
        meta = {"source": "test", "priority": "high"}
        alert_data = {
            "vector": [3.0, 4.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
            "meta": meta,
        }
        result = process_alert(alert_data)
        assert result is not None
        assert result.details.meta == meta


class TestEvaluateAlert:
    """evaluate_alert 함수 테스트 (기존 호환용 래퍼)"""

    def test_evaluate_alert_calls_process_alert(self):
        """evaluate_alert가 process_alert를 호출하는지 확인"""
        alert_data = {
            "vector": [3.0, 4.0],
            "threshold": 3.0,
            "sensor_id": "test_sensor",
        }
        result = evaluate_alert(alert_data)
        # evaluate_alert는 process_alert를 래핑하므로 로직적으로 동일한 결과
        expected = process_alert(alert_data)
        
        # None이면 둘 다 None이어야 함
        if result is None:
            assert expected is None
        else:
            # 타임스탬프는 다를 수 있으므로 주요 필드만 비교
            assert expected is not None
            assert result.sensor_id == expected.sensor_id
            assert result.level == expected.level
            assert result.details.norm == expected.details.norm
            assert result.details.severity == expected.details.severity


class TestSeverityLevelMapping:
    """Severity와 AlertLevel 매핑 테스트"""

    def test_normal_severity_maps_to_info_level(self):
        """NORMAL severity는 INFO level로 매핑"""
        alert_data = {
            "vector": [1.0, 1.0],  # norm ≈ 1.414, threshold 3.0이면 이상 없음
            "threshold": 3.0,
            "sensor_id": "test_sensor",
        }
        result = process_alert(alert_data)
        # 이상이 없으면 None 반환
        assert result is None

    def test_warning_severity_maps_to_warning_level(self):
        """WARNING severity는 WARNING level로 매핑"""
        alert_data = {
            "vector": [6.0, 0.0],  # norm = 6.0
            "warning_threshold": 5.0,
            "critical_threshold": 8.0,
            "sensor_id": "test_sensor",
        }
        result = process_alert(alert_data)
        assert result is not None
        assert result.level == constants.AlertLevel.WARNING.value

    def test_critical_severity_maps_to_critical_level(self):
        """CRITICAL severity는 CRITICAL level로 매핑"""
        alert_data = {
            "vector": [10.0, 0.0],  # norm = 10.0
            "warning_threshold": 5.0,
            "critical_threshold": 8.0,
            "sensor_id": "test_sensor",
        }
        result = process_alert(alert_data)
        assert result is not None
        assert result.level == constants.AlertLevel.CRITICAL.value

