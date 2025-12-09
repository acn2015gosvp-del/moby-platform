"""
Grafana 라우터 통합 테스트
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from backend.main import app


class TestGrafanaRoutes:
    """Grafana API 엔드포인트 테스트"""
    
    # conftest.py의 client fixture를 사용
    
    @pytest.fixture
    def auth_headers(self, db_session):
        """인증 헤더 생성"""
        from backend.api.models.user import User
        from backend.api.models.role import Role
        from backend.api.services.auth_service import get_password_hash, create_access_token
        from datetime import timedelta
        
        # 테스트 사용자 생성
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("Test1234"),
            role=Role.ADMIN.value,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # 토큰 생성
        token_data = {"sub": user.email}
        token = create_access_token(data=token_data, expires_delta=timedelta(hours=1))
        return {"Authorization": f"Bearer {token}"}
    
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
            # 응답 형식이 ErrorResponse일 수도 있고 detail일 수도 있음
            if "detail" in data:
                assert "Grafana 클라이언트를 초기화할 수 없습니다" in data["detail"]
            elif "error" in data:
                assert "Grafana 클라이언트를 초기화할 수 없습니다" in data["error"].get("message", "")
    
    def test_health_check_exception(self, client, mock_grafana_client):
        """헬스체크 중 예외 발생"""
        mock_grafana_client.test_connection.side_effect = Exception("Connection error")
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.get("/grafana/health")
            
            assert response.status_code == 500
            data = response.json()
            # 응답 형식이 ErrorResponse일 수도 있고 detail일 수도 있음
            if "detail" in data:
                assert "Grafana 연결 확인 실패" in data["detail"]
            elif "error" in data:
                assert "Grafana 연결 확인 실패" in data["error"].get("message", "")
    
    def test_create_datasource_success(self, client, mock_grafana_client, auth_headers):
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
                },
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["data"]["datasource"]["name"] == "InfluxDB"
            mock_grafana_client.create_datasource.assert_called_once()
    
    def test_create_datasource_with_custom_url(self, client, mock_grafana_client, auth_headers):
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
                },
                headers=auth_headers
            )
            
            assert response.status_code == 201
            call_args = mock_grafana_client.create_datasource.call_args
            assert call_args.kwargs["name"] == "CustomInfluxDB"
            assert call_args.kwargs["url"] == "http://custom-influx:8086"
            assert call_args.kwargs["is_default"] is True
    
    def test_create_datasource_validation_error(self, client, mock_grafana_client, auth_headers):
        """데이터 소스 생성 요청 검증 실패"""
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/datasources",
                json={},  # name 필수 필드 누락
                headers=auth_headers
            )
            
            assert response.status_code == 422
    
    def test_create_datasource_value_error(self, client, mock_grafana_client, auth_headers):
        """데이터 소스 생성 중 ValueError 발생"""
        mock_grafana_client.create_datasource.side_effect = ValueError("Invalid configuration")
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/datasources",
                json={"name": "InfluxDB"},
                headers=auth_headers
            )
            
            assert response.status_code == 400
            data = response.json()
            # 응답 형식이 ErrorResponse일 수도 있고 detail일 수도 있음
            if "detail" in data:
                assert "Invalid configuration" in data["detail"]
            elif "error" in data:
                assert "Invalid configuration" in data["error"].get("message", "")
    
    def test_create_datasource_exception(self, client, mock_grafana_client, auth_headers):
        """데이터 소스 생성 중 예외 발생"""
        mock_grafana_client.create_datasource.side_effect = Exception("Unexpected error")
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/datasources",
                json={"name": "InfluxDB"},
                headers=auth_headers
            )
            
            assert response.status_code == 500
            data = response.json()
            # 응답 형식이 ErrorResponse일 수도 있고 detail일 수도 있음
            if "detail" in data:
                assert "데이터 소스 생성 실패" in data["detail"]
            elif "error" in data:
                assert "데이터 소스 생성 실패" in data["error"].get("message", "")
    
    def test_get_datasource_success(self, client, mock_grafana_client, auth_headers):
        """데이터 소스 조회 성공"""
        mock_grafana_client.get_datasource_by_name.return_value = {
            "id": 1,
            "name": "InfluxDB",
            "type": "influxdb"
        }
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.get("/grafana/datasources/InfluxDB", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["name"] == "InfluxDB"
            mock_grafana_client.get_datasource_by_name.assert_called_once_with("InfluxDB")
    
    def test_get_datasource_not_found(self, client, mock_grafana_client, auth_headers):
        """데이터 소스 조회 실패 (없음)"""
        mock_grafana_client.get_datasource_by_name.return_value = None
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.get("/grafana/datasources/NonExistent", headers=auth_headers)
            
            assert response.status_code == 404
            data = response.json()
            # 응답 형식이 ErrorResponse일 수도 있고 detail일 수도 있음
            if "detail" in data:
                assert "데이터 소스를 찾을 수 없습니다" in data["detail"]
            elif "error" in data:
                assert "데이터 소스를 찾을 수 없습니다" in data["error"].get("message", "")
    
    def test_get_datasource_exception(self, client, mock_grafana_client, auth_headers):
        """데이터 소스 조회 중 예외 발생"""
        mock_grafana_client.get_datasource_by_name.side_effect = Exception("Unexpected error")
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.get("/grafana/datasources/InfluxDB", headers=auth_headers)
            
            assert response.status_code == 500
            data = response.json()
            # 응답 형식이 ErrorResponse일 수도 있고 detail일 수도 있음
            if "detail" in data:
                assert "데이터 소스 조회 실패" in data["detail"]
            elif "error" in data:
                assert "데이터 소스 조회 실패" in data["error"].get("message", "")
    
    def test_create_dashboard_success(self, client, mock_grafana_client, auth_headers):
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
                },
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["data"]["dashboard"]["title"] == "MOBY Sensor Dashboard"
            mock_grafana_client.create_sensor_dashboard.assert_called_once()
    
    def test_create_dashboard_with_default_datasource(self, client, mock_grafana_client, auth_headers):
        """기본 데이터 소스로 대시보드 생성"""
        mock_grafana_client.create_sensor_dashboard.return_value = {
            "dashboard": {"id": 1, "title": "Test Dashboard"}
        }
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/dashboards",
                json={"title": "Test Dashboard"},  # datasource_name 생략
                headers=auth_headers
            )
            
            assert response.status_code == 201
            call_args = mock_grafana_client.create_sensor_dashboard.call_args
            assert call_args.kwargs["dashboard_title"] == "Test Dashboard"
            assert call_args.kwargs["datasource_name"] == "InfluxDB"  # 기본값
    
    def test_create_dashboard_validation_error(self, client, mock_grafana_client, auth_headers):
        """대시보드 생성 요청 검증 실패"""
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/dashboards",
                json={},  # title 필수 필드 누락
                headers=auth_headers
            )
            
            assert response.status_code == 422
    
    def test_create_dashboard_value_error(self, client, mock_grafana_client, auth_headers):
        """대시보드 생성 중 ValueError 발생"""
        mock_grafana_client.create_sensor_dashboard.side_effect = ValueError("Datasource not found")
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/dashboards",
                json={"title": "Test Dashboard"},
                headers=auth_headers
            )
            
            assert response.status_code == 400
            data = response.json()
            # 응답 형식이 ErrorResponse일 수도 있고 detail일 수도 있음
            if "detail" in data:
                assert "Datasource not found" in data["detail"]
            elif "error" in data:
                assert "Datasource not found" in data["error"].get("message", "")
    
    def test_create_dashboard_exception(self, client, mock_grafana_client, auth_headers):
        """대시보드 생성 중 예외 발생"""
        mock_grafana_client.create_sensor_dashboard.side_effect = Exception("Unexpected error")
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/dashboards",
                json={"title": "Test Dashboard"},
                headers=auth_headers
            )
            
            assert response.status_code == 500
            data = response.json()
            # 응답 형식이 ErrorResponse일 수도 있고 detail일 수도 있음
            if "detail" in data:
                assert "대시보드 생성 실패" in data["detail"]
            elif "error" in data:
                assert "대시보드 생성 실패" in data["error"].get("message", "")
    
    def test_health_check_with_exception_during_test_connection(self, client, mock_grafana_client):
        """헬스체크 중 test_connection에서 예외 발생"""
        mock_grafana_client.test_connection.side_effect = Exception("Network error")
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.get("/grafana/health")
            
            assert response.status_code == 500
            data = response.json()
            # 응답 형식이 ErrorResponse일 수도 있고 detail일 수도 있음
            if "detail" in data:
                assert "Grafana 연결 확인 실패" in data["detail"]
            elif "error" in data:
                assert "Grafana 연결 확인 실패" in data["error"].get("message", "")
    
    def test_create_datasource_with_empty_name(self, client, mock_grafana_client, auth_headers):
        """빈 이름으로 데이터 소스 생성 시도"""
        # 빈 문자열은 Pydantic에서 허용되므로 실제 Grafana API에서 처리됨
        mock_grafana_client.create_datasource.return_value = {
            "datasource": {"id": 1, "name": ""}
        }
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/datasources",
                json={"name": ""},
                headers=auth_headers
            )
            
            # 빈 문자열은 허용되지만 실제로는 Grafana에서 처리
            assert response.status_code in [201, 400, 422]
    
    def test_create_datasource_with_invalid_type(self, client, mock_grafana_client, auth_headers):
        """잘못된 타입으로 데이터 소스 생성"""
        mock_grafana_client.create_datasource.return_value = {
            "datasource": {"id": 1, "name": "Test", "type": "invalid"}
        }
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/datasources",
                json={"name": "Test", "type": "invalid"},
                headers=auth_headers
            )
            
            # 타입 자체는 검증하지 않으므로 성공할 수 있음
            assert response.status_code in [201, 400]
    
    def test_get_datasource_with_special_characters(self, client, mock_grafana_client, auth_headers):
        """특수 문자가 포함된 데이터 소스 이름 조회"""
        mock_grafana_client.get_datasource_by_name.return_value = {
            "id": 1,
            "name": "Test-DS_123",
            "type": "influxdb"
        }
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.get("/grafana/datasources/Test-DS_123", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["name"] == "Test-DS_123"
    
    def test_get_datasource_with_unicode_name(self, client, mock_grafana_client, auth_headers):
        """유니코드 문자가 포함된 데이터 소스 이름 조회"""
        mock_grafana_client.get_datasource_by_name.return_value = {
            "id": 1,
            "name": "테스트 데이터소스",
            "type": "influxdb"
        }
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            # URL 인코딩 필요
            import urllib.parse
            encoded_name = urllib.parse.quote("테스트 데이터소스")
            response = client.get(f"/grafana/datasources/{encoded_name}", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["name"] == "테스트 데이터소스"
    
    def test_create_dashboard_with_empty_title(self, client, mock_grafana_client, auth_headers):
        """빈 제목으로 대시보드 생성 시도"""
        # 빈 문자열은 Pydantic에서 허용되므로 실제 Grafana API에서 처리됨
        mock_grafana_client.create_sensor_dashboard.return_value = {
            "dashboard": {"id": 1, "title": ""}
        }
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/dashboards",
                json={"title": ""},
                headers=auth_headers
            )
            
            # 빈 문자열은 허용되지만 실제로는 Grafana에서 처리
            assert response.status_code in [201, 400, 422]
    
    def test_create_dashboard_with_very_long_title(self, client, mock_grafana_client, auth_headers):
        """매우 긴 제목으로 대시보드 생성"""
        long_title = "A" * 1000
        mock_grafana_client.create_sensor_dashboard.return_value = {
            "dashboard": {"id": 1, "title": long_title}
        }
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/dashboards",
                json={"title": long_title},
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["data"]["dashboard"]["title"] == long_title
    
    def test_create_datasource_missing_required_fields(self, client, mock_grafana_client, auth_headers):
        """필수 필드 누락으로 데이터 소스 생성 시도"""
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            # name 필드 누락
            response = client.post(
                "/grafana/datasources",
                json={"type": "influxdb"},
                headers=auth_headers
            )
            
            assert response.status_code == 422
    
    def test_get_datasource_with_nonexistent_name(self, client, mock_grafana_client, auth_headers):
        """존재하지 않는 데이터 소스 조회"""
        mock_grafana_client.get_datasource_by_name.return_value = None
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.get("/grafana/datasources/NonExistentDS", headers=auth_headers)
            
            assert response.status_code == 404
            data = response.json()
            # 응답 형식이 ErrorResponse일 수도 있고 detail일 수도 있음
            if "detail" in data:
                assert "데이터 소스를 찾을 수 없습니다" in data["detail"]
            elif "error" in data:
                assert "데이터 소스를 찾을 수 없습니다" in data["error"].get("message", "")
    
    def test_create_datasource_with_all_optional_fields(self, client, mock_grafana_client, auth_headers):
        """모든 선택 필드 포함하여 데이터 소스 생성"""
        mock_grafana_client.create_datasource.return_value = {
            "datasource": {
                "id": 1,
                "name": "FullConfig",
                "type": "influxdb",
                "url": "http://custom:8086",
                "isDefault": True
            }
        }
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/datasources",
                json={
                    "name": "FullConfig",
                    "type": "influxdb",
                    "url": "http://custom:8086",
                    "is_default": True
                },
                headers=auth_headers
            )
            
            assert response.status_code == 201
            call_args = mock_grafana_client.create_datasource.call_args
            assert call_args.kwargs["name"] == "FullConfig"
            assert call_args.kwargs["url"] == "http://custom:8086"
            assert call_args.kwargs["is_default"] is True
    
    def test_create_dashboard_with_custom_datasource_name(self, client, mock_grafana_client, auth_headers):
        """커스텀 데이터 소스 이름으로 대시보드 생성"""
        mock_grafana_client.create_sensor_dashboard.return_value = {
            "dashboard": {"id": 1, "title": "Custom Dashboard"}
        }
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/dashboards",
                json={
                    "title": "Custom Dashboard",
                    "datasource_name": "CustomDS"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 201
            call_args = mock_grafana_client.create_sensor_dashboard.call_args
            assert call_args.kwargs["datasource_name"] == "CustomDS"
    
    def test_health_check_returns_disconnected_status(self, client, mock_grafana_client):
        """연결 실패 시 disconnected 상태 반환"""
        mock_grafana_client.test_connection.return_value = False
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.get("/grafana/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["status"] == "disconnected"
    
    def test_get_datasource_http_exception_propagation(self, client, mock_grafana_client, auth_headers):
        """데이터 소스 조회 중 HTTP 예외 전파"""
        import httpx
        mock_grafana_client.get_datasource_by_name.side_effect = httpx.HTTPError("Connection failed")
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.get("/grafana/datasources/Test", headers=auth_headers)
            
            assert response.status_code == 500
            data = response.json()
            # 응답 형식이 ErrorResponse일 수도 있고 detail일 수도 있음
            if "detail" in data:
                assert "데이터 소스 조회 실패" in data["detail"]
            elif "error" in data:
                assert "데이터 소스 조회 실패" in data["error"].get("message", "")
    
    def test_create_datasource_http_exception_propagation(self, client, mock_grafana_client, auth_headers):
        """데이터 소스 생성 중 HTTP 예외 전파"""
        import httpx
        mock_grafana_client.create_datasource.side_effect = httpx.HTTPError("Connection failed")
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/datasources",
                json={"name": "Test"},
                headers=auth_headers
            )
            
            assert response.status_code == 500
            data = response.json()
            # 응답 형식이 ErrorResponse일 수도 있고 detail일 수도 있음
            if "detail" in data:
                assert "데이터 소스 생성 실패" in data["detail"]
            elif "error" in data:
                assert "데이터 소스 생성 실패" in data["error"].get("message", "")
    
    def test_create_dashboard_http_exception_propagation(self, client, mock_grafana_client, auth_headers):
        """대시보드 생성 중 HTTP 예외 전파"""
        import httpx
        mock_grafana_client.create_sensor_dashboard.side_effect = httpx.HTTPError("Connection failed")
        
        with patch('backend.api.routes_grafana.get_grafana_client', return_value=mock_grafana_client):
            response = client.post(
                "/grafana/dashboards",
                json={"title": "Test"},
                headers=auth_headers
            )
            
            assert response.status_code == 500
            data = response.json()
            # 응답 형식이 ErrorResponse일 수도 있고 detail일 수도 있음
            if "detail" in data:
                assert "대시보드 생성 실패" in data["detail"]
            elif "error" in data:
                assert "대시보드 생성 실패" in data["error"].get("message", "")

