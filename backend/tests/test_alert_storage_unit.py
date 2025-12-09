"""
Alert Storage 단위 테스트

알림 저장 및 조회 로직을 테스트합니다.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.api.services.alert_storage import (
    save_alert,
    get_latest_alerts
)
from backend.api.models.alert import Alert


class TestSaveAlert:
    """save_alert 함수 테스트"""
    
    @pytest.fixture
    def mock_db_session(self):
        """데이터베이스 세션 모킹"""
        session = MagicMock(spec=Session)
        session.add = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock()
        return session
    
    def test_save_alert_success(self, mock_db_session):
        """알림 저장 성공 테스트"""
        from backend.api.services.alert_engine import AlertPayloadModel, AlertDetailsModel
        
        alert_payload = AlertPayloadModel(
            id="test-alert-001",
            level="warning",
            message="Test alert message",
            sensor_id="sensor_001",
            source="test",
            ts=datetime.now().isoformat(),
            details=AlertDetailsModel(
                vector=[3.0, 4.0],
                norm=5.0,
                threshold=None,
                warning_threshold=4.0,
                critical_threshold=6.0,
                severity="warning",
                meta={}
            )
        )
        
        # Alert 모델 인스턴스 생성 모킹
        mock_alert = MagicMock(spec=Alert)
        with patch('backend.api.services.alert_storage.Alert', return_value=mock_alert):
            result = save_alert(mock_db_session, alert_payload)
            
            assert result is not None
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
    
    def test_save_alert_with_llm_summary(self, mock_db_session):
        """LLM 요약이 포함된 알림 저장 테스트"""
        from backend.api.services.alert_engine import AlertPayloadModel, AlertDetailsModel
        
        alert_payload = AlertPayloadModel(
            id="test-alert-002",
            level="critical",
            message="Critical alert",
            llm_summary="This is a critical alert that requires immediate attention.",
            sensor_id="sensor_002",
            source="test",
            ts=datetime.now().isoformat(),
            details=AlertDetailsModel(
                vector=[5.0, 5.0],
                norm=10.0,
                threshold=None,
                warning_threshold=4.0,
                critical_threshold=6.0,
                severity="critical",
                meta={}
            )
        )
        
        mock_alert = MagicMock(spec=Alert)
        with patch('backend.api.services.alert_storage.Alert', return_value=mock_alert):
            result = save_alert(mock_db_session, alert_payload)
            
            assert result is not None
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()


class TestGetLatestAlerts:
    """get_latest_alerts 함수 테스트"""
    
    @pytest.fixture
    def mock_db_session(self):
        """데이터베이스 세션 모킹"""
        session = MagicMock(spec=Session)
        return session
    
    def test_get_latest_alerts_default(self, mock_db_session):
        """기본 파라미터로 최신 알림 조회 테스트"""
        # 모킹된 쿼리 결과
        mock_alerts = [
            MagicMock(spec=Alert, alert_id="alert-1", level="warning"),
            MagicMock(spec=Alert, alert_id="alert-2", level="info"),
        ]
        
        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_alerts
        mock_db_session.query.return_value = mock_query
        
        result = get_latest_alerts(mock_db_session)
        
        assert len(result) == 2
        mock_db_session.query.assert_called_once_with(Alert)
        mock_query.order_by.assert_called_once()
        mock_query.limit.assert_called_once_with(10)  # 기본값
    
    def test_get_latest_alerts_with_limit(self, mock_db_session):
        """limit 파라미터로 최신 알림 조회 테스트"""
        mock_alerts = [MagicMock(spec=Alert) for _ in range(5)]
        
        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_alerts
        mock_db_session.query.return_value = mock_query
        
        result = get_latest_alerts(mock_db_session, limit=5)
        
        assert len(result) == 5
        mock_query.limit.assert_called_once_with(5)
    
    def test_get_latest_alerts_with_sensor_id_filter(self, mock_db_session):
        """sensor_id 필터로 알림 조회 테스트"""
        mock_alerts = [MagicMock(spec=Alert, sensor_id="sensor_001")]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_alerts
        mock_db_session.query.return_value = mock_query
        
        result = get_latest_alerts(mock_db_session, sensor_id="sensor_001")
        
        assert len(result) == 1
        mock_query.filter.assert_called()
    
    def test_get_latest_alerts_with_level_filter(self, mock_db_session):
        """level 필터로 알림 조회 테스트"""
        mock_alerts = [MagicMock(spec=Alert, level="critical")]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_alerts
        mock_db_session.query.return_value = mock_query
        
        result = get_latest_alerts(mock_db_session, level="critical")
        
        assert len(result) == 1
        mock_query.filter.assert_called()
    
    def test_get_latest_alerts_with_multiple_filters(self, mock_db_session):
        """여러 필터 조합으로 알림 조회 테스트"""
        mock_alerts = [
            MagicMock(spec=Alert, sensor_id="sensor_001", level="warning")
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_alerts
        mock_db_session.query.return_value = mock_query
        
        result = get_latest_alerts(
            mock_db_session,
            sensor_id="sensor_001",
            level="warning",
            limit=20
        )
        
        assert len(result) == 1
        # filter가 여러 번 호출되었는지 확인
        assert mock_query.filter.call_count >= 2
    
    def test_get_latest_alerts_empty_result(self, mock_db_session):
        """결과가 없는 경우 테스트"""
        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        result = get_latest_alerts(mock_db_session)
        
        assert len(result) == 0
        assert result == []

