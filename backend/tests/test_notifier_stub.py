import pytest
from unittest.mock import patch, MagicMock
import logging

# NotifierService가 backend/api/services/notifier_stub.py에 있다고 가정합니다.
from backend.api.services.notifier_stub import NotifierService 


@pytest.fixture
def notifier_service():
    """NotifierService 인스턴스를 제공하는 픽스처"""
    return NotifierService()


def test_send_alert_calls_log(notifier_service, caplog):
    """
    send_alert 메소드가 호출될 때 로그를 남기는지 확인합니다.
    (Stub이므로 로깅만 확인)
    """
    mock_alert_data = {
        "id": "test-001",
        "level": "critical",
        "message": "Engine failure detected.",
        "sensor_id": "temp-01"
    }
    
    # caplog 픽스처를 사용하여 로그 기록을 캡처합니다.
    with caplog.at_level(logging.INFO):
        result = notifier_service.send_alert(mock_alert_data)
        
        # 1. 반환 값이 True인지 확인
        assert result is True
        
        # 2. 로그 메시지가 성공적으로 기록되었는지 확인
        assert "ALERT DISPATCH SUCCESS (STUB) - ID: test-001, Level: CRITICAL" in caplog.text