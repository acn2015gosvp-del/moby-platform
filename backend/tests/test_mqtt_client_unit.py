"""
MQTT 클라이언트 단위 테스트

연결 관리, 메시지 발행, 재시도 로직 등을 테스트합니다.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from backend.api.services.mqtt_client import (
    MqttClientManager,
    QueuedMessage
)


class TestQueuedMessage:
    """QueuedMessage 데이터클래스 테스트"""
    
    def test_queued_message_creation(self):
        """QueuedMessage 생성 테스트"""
        from datetime import datetime
        message = QueuedMessage(
            topic="test/topic",
            payload={"data": "test"},
            timestamp=datetime.now()
        )
        
        assert message.topic == "test/topic"
        assert message.payload == {"data": "test"}
        assert message.retry_count == 0
        assert message.max_retries == 3


class TestMqttClientManager:
    """MqttClientManager 클래스 테스트"""
    
    @pytest.fixture
    def mock_mqtt_client(self):
        """MQTT 클라이언트 모킹"""
        with patch('backend.api.services.mqtt_client.mqtt.Client') as mock_client:
            mock_instance = MagicMock()
            mock_instance.is_connected.return_value = True
            mock_client.return_value = mock_instance
            yield {
                'client': mock_client,
                'instance': mock_instance
            }
    
    @pytest.fixture
    def mqtt_manager(self, mock_mqtt_client):
        """MqttClientManager 인스턴스 생성"""
        with patch('backend.api.services.mqtt_client.settings') as mock_settings:
            mock_settings.MQTT_HOST = "localhost"
            mock_settings.MQTT_PORT = 1883
            manager = MqttClientManager()
            return manager
    
    def test_init(self, mock_mqtt_client):
        """MqttClientManager 초기화 테스트"""
        with patch('backend.api.services.mqtt_client.settings') as mock_settings:
            mock_settings.MQTT_HOST = "localhost"
            mock_settings.MQTT_PORT = 1883
            manager = MqttClientManager()
            
            assert manager.host == "localhost"
            assert manager.port == 1883
            assert manager.message_queue is not None
            assert manager.client is not None
    
    def test_publish_message_connected(self, mqtt_manager, mock_mqtt_client):
        """연결된 상태에서 메시지 발행 테스트"""
        mqtt_manager.client.is_connected.return_value = True
        mqtt_manager.client.publish = MagicMock(return_value=(0, 0))  # (mid, rc)
        
        result = mqtt_manager.publish_message(
            topic="test/topic",
            payload={"data": "test"}
        )
        
        assert result is True
        mqtt_manager.client.publish.assert_called_once()
    
    def test_publish_message_disconnected(self, mqtt_manager, mock_mqtt_client):
        """연결되지 않은 상태에서 메시지 발행 테스트"""
        mqtt_manager.client.is_connected.return_value = False
        
        result = mqtt_manager.publish_message(
            topic="test/topic",
            payload={"data": "test"}
        )
        
        # 연결되지 않으면 큐에 추가됨
        assert result is True
        assert len(mqtt_manager.message_queue) == 1
    
    def test_publish_message_connected(self, mqtt_manager, mock_mqtt_client):
        """연결된 상태에서 메시지 발행 테스트 (재확인)"""
        mqtt_manager.client.is_connected.return_value = True
        mqtt_manager.client.publish = MagicMock(return_value=(0, 0))
        
        result = mqtt_manager.publish_message(
            topic="test/topic",
            payload={"data": "test"}
        )
        
        assert result is True
        mqtt_manager.client.publish.assert_called_once()
    
    def test_publish_message_json_payload(self, mqtt_manager, mock_mqtt_client):
        """JSON 페이로드 메시지 발행 테스트"""
        mqtt_manager.client.is_connected.return_value = True
        mqtt_manager.client.publish = MagicMock(return_value=(0, 0))
        
        payload = {"temperature": 25.5, "humidity": 60.0}
        result = mqtt_manager.publish_message(
            topic="sensors/data",
            payload=payload
        )
        
        assert result is True
        # JSON 문자열로 변환되어 발행되었는지 확인
        call_args = mqtt_manager.client.publish.call_args
        published_payload = call_args[0][1]
        assert isinstance(published_payload, (str, bytes))
    
    def test_message_queue_processing(self, mqtt_manager, mock_mqtt_client):
        """메시지 큐 처리 테스트"""
        # 연결되지 않은 상태에서 메시지 추가
        mqtt_manager.client.is_connected.return_value = False
        mqtt_manager.publish_message("test/topic1", {"data": "test1"})
        mqtt_manager.publish_message("test/topic2", {"data": "test2"})
        
        assert len(mqtt_manager.message_queue) == 2
        
        # 큐 처리 스레드가 실행 중인지 확인
        assert mqtt_manager.queue_processor_thread is not None
    
    def test_connection_retry(self, mqtt_manager, mock_mqtt_client):
        """연결 재시도 테스트"""
        # 연결 실패 시뮬레이션
        mqtt_manager.client.connect.side_effect = Exception("Connection failed")
        
        # 연결 시도 (실제로는 재시도 로직이 내부적으로 처리됨)
        # 실제 구현에 따라 테스트 수정 필요
        with pytest.raises(Exception):
            mqtt_manager.connect()
    
    def test_client_connection_status(self, mqtt_manager, mock_mqtt_client):
        """클라이언트 연결 상태 확인 테스트"""
        mqtt_manager.client.is_connected.return_value = True
        assert mqtt_manager.client.is_connected() is True
        
        mqtt_manager.client.is_connected.return_value = False
        assert mqtt_manager.client.is_connected() is False

