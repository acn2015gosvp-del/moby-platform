import pytest
from unittest.mock import patch, MagicMock

# 주의: 아래 import 경로는 Sir의 프로젝트 구조에 따라 달라질 수 있습니다.
# (예: from api.services.mqtt_client import MQTTClient)
from backend.api.services.mqtt_client import MQTTClient 


# 1. Fixture: paho-mqtt의 Client 클래스를 Mocking (가짜 객체로 대체)
#    - 이렇게 하면 테스트 실행 시 실제 외부 서버에 연결하는 것을 방지합니다.
@pytest.fixture
def mock_paho_client():
    # 'paho.mqtt.client'가 사용되는 경로를 patch합니다.
    with patch('backend.api.services.mqtt_client.mqtt.Client') as MockClient:
        # MockClient가 호출될 때 반환될 인스턴스를 설정합니다.
        mock_instance = MockClient.return_value
        yield mock_instance # 테스트 함수에 Mock 인스턴스를 제공


# 2. Fixture: 테스트용 MQTTClient 인스턴스 생성
@pytest.fixture
def mqtt_client(mock_paho_client):
    # 실제 MQTTClient 객체를 생성하며, 내부적으로 Mocking된 paho-mqtt 클라이언트를 사용하게 됩니다.
    client = MQTTClient(
        host="test_host", 
        port=1883, 
        topics=["test/topic"],
        alert_callback=MagicMock() # 콜백 함수도 Mocking
    )
    return client


# 3. 테스트 함수: MQTTClient 객체가 생성되는지 확인
def test_mqtt_client_initializes(mqtt_client):
    """MQTTClient 인스턴스가 성공적으로 생성되었는지 확인"""
    assert isinstance(mqtt_client, MQTTClient)

# 4. 테스트 함수: 연결 로직이 paho-mqtt의 connect를 호출하는지 확인
def test_connect_is_called(mqtt_client, mock_paho_client):
    """
    connect_with_retry() 메소드가 paho-mqtt의 connect()를 호출하는지 확인합니다.
    (연결 시도 로직이 정상 작동하는지 검증)
    """
    mqtt_client.connect_with_retry()
    # Mock 객체의 .connect 메소드가 한 번 호출되었는지 확인합니다.
    mock_paho_client.connect.assert_called_once()
    
# 5. 테스트 함수: 재연결 시도 횟수가 지켜지는지 확인 (간단화)
# 이 부분은 지수 백오프 로직을 직접 검증해야 하므로 복잡합니다.
# 일단 연결 에러 시 재시도 로직이 실행되는지만 확인합니다.
# def test_reconnection_attempts(mqtt_client, mock_paho_client):
#     # 연결이 실패하도록 Mocking (로직에 따라 필요)
#     mock_paho_client.connect.side_effect = ConnectionRefusedError 
#     
#     # ... 재연결 횟수 등을 검증하는 추가 로직 필요
#     pass