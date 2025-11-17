"""
Grafana 라우터 통합 테스트
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from backend.main import app


class TestGrafanaRoutes:
    """Grafana API 엔드포인트 테스트"""
    
    @pytest.fixture
    def client(self):
        """테스트 클라이언트"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_grafana_client(self):
        """모킹된 Grafana 클라이언트"""
        mock_client = MagicMock()
        mock_client.base_url = "http://localhost:3000"
        mock_client.test_connection.return_value = True
        return mock_client
    
    def test_health_check_success(self, client, mock_grafana_client):
        """헬스체크 성공"""
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.get("/grafana/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["status"] == "connected"
            assert data["data"]["url"] == "http://localhost:3000"
            mock_grafana_client.test_connection.assert_called_once()
    
    def test_health_check_failure(self, client, mock_grafana_client):
        """헬스체크 실패"""
        mock_grafana_client.test_connection.return_value = False
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.get("/grafana/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["status"] == "disconnected"
    
    def test_health_check_client_unavailable(self, client):
        """Grafana 클라이언트 초기화 실패"""
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=None):
            response = client.get("/grafana/health")
            
            assert response.status_code == 503
            data = response.json()
            assert "Grafana 클라이언트를 초기화할 수 없습니다" in data["detail"]
    
    def test_health_check_exception(self, client, mock_grafana_client):
        """헬스체크 중 예외 발생"""
        mock_grafana_client.test_connection.side_effect = Exception("Connection error")
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.get("/grafana/health")
            
            assert response.status_code == 500
            data = response.json()
            assert "Grafana 연결 확인 실패" in data["detail"]
    
    def test_create_datasource_success(self, client, mock_grafana_client):
        """데이터 소스 생성 성공"""
        mock_grafana_client.create_datasource.return_value = {
            "datasource": {"id": 1, "name": "InfluxDB"}
        }
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/datasources",
                json={
                    "name": "InfluxDB",
                    "type": "influxdb",
                    "is_default": False
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["data"]["datasource"]["name"] == "InfluxDB"
            mock_grafana_client.create_datasource.assert_called_once()
    
    def test_create_datasource_with_custom_url(self, client, mock_grafana_client):
        """커스텀 URL로 데이터 소스 생성"""
        mock_grafana_client.create_datasource.return_value = {
            "datasource": {"id": 1, "name": "CustomInfluxDB"}
        }
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/datasources",
                json={
                    "name": "CustomInfluxDB",
                    "type": "influxdb",
                    "url": "http://custom-influx:8086",
                    "is_default": True
                }
            )
            
            assert response.status_code == 201
            call_args = mock_grafana_client.create_datasource.call_args
            assert call_args.kwargs["name"] == "CustomInfluxDB"
            assert call_args.kwargs["url"] == "http://custom-influx:8086"
            assert call_args.kwargs["is_default"] is True
    
    def test_create_datasource_validation_error(self, client, mock_grafana_client):
        """데이터 소스 생성 요청 검증 실패"""
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/datasources",
                json={}  # name 필수 필드 누락
            )
            
            assert response.status_code == 422
    
    def test_create_datasource_value_error(self, client, mock_grafana_client):
        """데이터 소스 생성 중 ValueError 발생"""
        mock_grafana_client.create_datasource.side_effect = ValueError("Invalid configuration")
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/datasources",
                json={"name": "InfluxDB"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "Invalid configuration" in data["detail"]
    
    def test_create_datasource_exception(self, client, mock_grafana_client):
        """데이터 소스 생성 중 예외 발생"""
        mock_grafana_client.create_datasource.side_effect = Exception("Unexpected error")
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/datasources",
                json={"name": "InfluxDB"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "데이터 소스 생성 실패" in data["detail"]
    
    def test_get_datasource_success(self, client, mock_grafana_client):
        """데이터 소스 조회 성공"""
        mock_grafana_client.get_datasource_by_name.return_value = {
            "id": 1,
            "name": "InfluxDB",
            "type": "influxdb"
        }
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.get("/grafana/datasources/InfluxDB")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["name"] == "InfluxDB"
            mock_grafana_client.get_datasource_by_name.assert_called_once_with("InfluxDB")
    
    def test_get_datasource_not_found(self, client, mock_grafana_client):
        """데이터 소스 조회 실패 (없음)"""
        mock_grafana_client.get_datasource_by_name.return_value = None
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.get("/grafana/datasources/NonExistent")
            
            assert response.status_code == 404
            data = response.json()
            assert "데이터 소스를 찾을 수 없습니다" in data["detail"]
    
    def test_get_datasource_exception(self, client, mock_grafana_client):
        """데이터 소스 조회 중 예외 발생"""
        mock_grafana_client.get_datasource_by_name.side_effect = Exception("Unexpected error")
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.get("/grafana/datasources/InfluxDB")
            
            assert response.status_code == 500
            data = response.json()
            assert "데이터 소스 조회 실패" in data["detail"]
    
    def test_create_dashboard_success(self, client, mock_grafana_client):
        """대시보드 생성 성공"""
        mock_grafana_client.create_sensor_dashboard.return_value = {
            "dashboard": {"id": 1, "title": "MOBY Sensor Dashboard"}
        }
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/dashboards",
                json={
                    "title": "MOBY Sensor Dashboard",
                    "datasource_name": "InfluxDB"
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["data"]["dashboard"]["title"] == "MOBY Sensor Dashboard"
            mock_grafana_client.create_sensor_dashboard.assert_called_once()
    
    def test_create_dashboard_with_default_datasource(self, client, mock_grafana_client):
        """기본 데이터 소스로 대시보드 생성"""
        mock_grafana_client.create_sensor_dashboard.return_value = {
            "dashboard": {"id": 1, "title": "Test Dashboard"}
        }
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/dashboards",
                json={"title": "Test Dashboard"}  # datasource_name 생략
            )
            
            assert response.status_code == 201
            call_args = mock_grafana_client.create_sensor_dashboard.call_args
            assert call_args.kwargs["dashboard_title"] == "Test Dashboard"
            assert call_args.kwargs["datasource_name"] == "InfluxDB"  # 기본값
    
    def test_create_dashboard_validation_error(self, client, mock_grafana_client):
        """대시보드 생성 요청 검증 실패"""
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/dashboards",
                json={}  # title 필수 필드 누락
            )
            
            assert response.status_code == 422
    
    def test_create_dashboard_value_error(self, client, mock_grafana_client):
        """대시보드 생성 중 ValueError 발생"""
        mock_grafana_client.create_sensor_dashboard.side_effect = ValueError("Datasource not found")
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/dashboards",
                json={"title": "Test Dashboard"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "Datasource not found" in data["detail"]
    
    def test_create_dashboard_exception(self, client, mock_grafana_client):
        """대시보드 생성 중 예외 발생"""
        mock_grafana_client.create_sensor_dashboard.side_effect = Exception("Unexpected error")
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/dashboards",
                json={"title": "Test Dashboard"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "대시보드 생성 실패" in data["detail"]

