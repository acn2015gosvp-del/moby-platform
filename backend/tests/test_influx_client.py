# backend/tests/test_influx_client.py

import pytest
from unittest.mock import patch, MagicMock

from backend.api.services.influx_client import InfluxDBClient
from backend.core.config import settings

# NOTE: InfluxDBClientLib는 실제 InfluxDB 라이브러리 클래스입니다.

# 1. Fixture: InfluxDBClient 생성자 자체를 Mocking
#    - Mocking할 대상은 InfluxDBClient 클래스가 아니라, 
#      InfluxDBClient가 사용하는 실제 라이브러리 클래스(InfluxDBClientLib)입니다.
@pytest.fixture
def mock_influxdb_client_lib():
    # InfluxDBClient가 사용하는 라이브러리 객체 InfluxDBClientLib를 Mocking합니다.
    with patch('backend.api.services.influx_client.InfluxDBClientLib') as MockLib:
        # Mocking된 라이브러리 인스턴스가 반환될 때 write_api를 Mocking합니다.
        mock_instance = MockLib.return_value
        mock_instance.write_api.return_value = MagicMock()
        yield mock_instance

# 2. Fixture: 테스트용 InfluxDBClient 인스턴스 생성
#    - 이 fixture는 이제 mock_influxdb_client_lib를 사용합니다.
@pytest.fixture
def influx_client(mock_influxdb_client_lib):
    # 인스턴스 생성 시 실제 연결을 시도하지 않습니다.
    client = InfluxDBClient(
        url=settings.INFLUX_URL,
        token=settings.INFLUX_TOKEN,
        org=settings.INFLUX_ORG,
        bucket="test_bucket"
    )
    # 인스턴스 생성 후, Mocking된 write_api 객체를 쉽게 참조할 수 있도록 추가
    client.mock_write_api = mock_influxdb_client_lib.write_api.return_value
    return client

# 3. test_batch_write_called 함수 수정
def test_batch_write_called(influx_client, mock_influxdb_client_lib):
    """
    write_batch 메소드가 WriteApi의 write 메소드를 호출하는지 검증합니다.
    """
    # mock_write_api가 이제 client.mock_write_api에 저장되어 있습니다.
    mock_write_api = influx_client.mock_write_api 
    
    test_points = [
        {"measurement": "sensor_data", "fields": {"value": 10.5}, "time": 1678886400},
        {"measurement": "sensor_data", "fields": {"value": 11.0}, "time": 1678886401},
    ]
    
    influx_client.write_batch(test_points)
    
    # 0번 호출이 아니라, 1번 호출되었는지 확인합니다.
    mock_write_api.write.assert_called_once()