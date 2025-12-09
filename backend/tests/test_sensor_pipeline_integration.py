"""
센서 데이터 파이프라인 통합 테스트

센서 데이터 수신부터 MQTT 발행, InfluxDB 저장까지의 전체 파이프라인을 테스트합니다.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestSensorPipelineIntegration:
    """센서 데이터 파이프라인 통합 테스트"""
    
    @pytest.mark.skipif(
        os.getenv("CI") == "true",
        reason="MQTT broker not available in CI environment"
    )
    @patch('backend.api.routes_sensors.mqtt_manager')
    def test_sensor_data_received_and_published_to_mqtt(
        self,
        mock_mqtt_manager,
        client,
        sample_sensor_data
    ):
        """센서 데이터 수신 및 MQTT 발행 테스트"""
        # MQTT 매니저 모킹
        mock_mqtt_manager.publish_message.return_value = True
        mock_mqtt_manager.is_connected.return_value = True
        
        # 센서 데이터 전송
        response = client.post("/sensors/data", json=sample_sensor_data)
        
        assert response.status_code == 202  # Accepted
        data = response.json()
        assert data["success"] is True
        assert data["data"]["sensor_id"] == sample_sensor_data["device_id"]
        assert data["data"]["status"] == "received"
        
        # MQTT 발행 확인 (연결이 안 되어 있어도 큐에 저장되므로 호출 확인)
        # 실제로는 연결이 안 되어 있으면 큐에 저장되므로, publish_message가 호출되었는지 확인
        assert mock_mqtt_manager.publish_message.called
        call_args = mock_mqtt_manager.publish_message.call_args
        assert call_args[0][0] == f"sensors/{sample_sensor_data['device_id']}/data"
        assert call_args[0][1]["device_id"] == sample_sensor_data["device_id"]
    
    @pytest.mark.skipif(
        os.getenv("CI") == "true",
        reason="MQTT broker not available in CI environment"
    )
    @patch('backend.api.services.influx_client.influx_manager')
    def test_mqtt_message_saved_to_influxdb(
        self,
        mock_influx_manager
    ):
        """MQTT 메시지 수신 시 InfluxDB 저장 테스트"""
        from backend.api.services.mqtt_client import mqtt_manager
        
        # InfluxDB 매니저 모킹
        mock_influx_manager.write_point.return_value = True
        
        # MQTT 메시지 시뮬레이션
        topic = "sensors/sensor_001/data"
        payload = {
            "device_id": "sensor_001",
            "temperature": 25.5,
            "humidity": 60.0,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # _process_sensor_data 메서드 직접 호출
        mqtt_manager._process_sensor_data(topic, payload)
        
        # InfluxDB 저장 확인
        mock_influx_manager.write_point.assert_called_once()
        call_args = mock_influx_manager.write_point.call_args
        assert call_args[1]["measurement"] == "sensor_data"
        assert call_args[1]["tags"]["device_id"] == "sensor_001"
        assert "temperature" in call_args[1]["fields"]
        assert "humidity" in call_args[1]["fields"]
    
    def test_sensor_status_query_from_influxdb(
        self,
        client
    ):
        """InfluxDB에서 센서 상태 조회 테스트"""
        # 센서 상태 조회 (실제 구현은 기본값 반환)
        response = client.get("/sensors/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["count"] >= 0
        assert data["data"]["active"] >= 0
        assert "status" in data["data"]

