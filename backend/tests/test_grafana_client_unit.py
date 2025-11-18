"""
Grafana 클라이언트 단위 테스트
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx
from backend.api.services.grafana_client import GrafanaClient, get_grafana_client
from backend.api.services.schemas.models.core.config import settings


class TestGrafanaClient:
    """GrafanaClient 클래스 테스트"""
    
    def test_init_success(self):
        """초기화 성공 테스트"""
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-api-key'):
            client = GrafanaClient()
            
            assert client.base_url == 'http://localhost:3000'
            assert client.api_key == 'test-api-key'
            assert 'Authorization' in client.headers
            assert client.headers['Authorization'] == 'Bearer test-api-key'
    
    def test_init_with_custom_params(self):
        """커스텀 파라미터로 초기화 테스트"""
        client = GrafanaClient(
            base_url='http://custom:3000',
            api_key='custom-key'
        )
        
        assert client.base_url == 'http://custom:3000'
        assert client.api_key == 'custom-key'
    
    def test_init_missing_url(self):
        """URL이 없을 때 에러 테스트"""
        with patch.object(settings, 'GRAFANA_URL', ''), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            with pytest.raises(ValueError, match="GRAFANA_URL"):
                GrafanaClient()
    
    def test_init_missing_api_key(self):
        """API 키가 없을 때 에러 테스트"""
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', ''):
            with pytest.raises(ValueError, match="GRAFANA_API_KEY"):
                GrafanaClient()
    
    def test_init_url_trailing_slash_removed(self):
        """URL 끝의 슬래시 제거 테스트"""
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000/'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            client = GrafanaClient()
            assert client.base_url == 'http://localhost:3000'
    
    @patch('httpx.Client')
    def test_request_success(self, mock_client_class):
        """요청 성공 테스트"""
        mock_response = Mock()
        mock_response.content = b'{"status": "ok"}'
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            client = GrafanaClient()
            result = client._request("GET", "/api/health")
            
            assert result == {"status": "ok"}
            mock_client.request.assert_called_once()
            mock_response.raise_for_status.assert_called_once()
    
    @patch('httpx.Client')
    def test_request_empty_response(self, mock_client_class):
        """빈 응답 처리 테스트"""
        mock_response = Mock()
        mock_response.content = b''
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            client = GrafanaClient()
            result = client._request("GET", "/api/health")
            
            assert result == {}
    
    @patch('httpx.Client')
    def test_request_http_error(self, mock_client_class):
        """HTTP 에러 처리 테스트"""
        mock_client = MagicMock()
        mock_client.request.side_effect = httpx.HTTPError("Connection error")
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            client = GrafanaClient()
            
            with pytest.raises(httpx.HTTPError):
                client._request("GET", "/api/health")
    
    @patch('httpx.Client')
    def test_test_connection_success(self, mock_client_class):
        """연결 테스트 성공"""
        mock_response = Mock()
        mock_response.content = b'{"status": "ok"}'
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            client = GrafanaClient()
            result = client.test_connection()
            
            assert result is True
    
    @patch('httpx.Client')
    def test_test_connection_failure(self, mock_client_class):
        """연결 테스트 실패"""
        mock_client = MagicMock()
        mock_client.request.side_effect = httpx.HTTPError("Connection error")
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            client = GrafanaClient()
            result = client.test_connection()
            
            assert result is False
    
    @patch('httpx.Client')
    def test_create_datasource_success(self, mock_client_class):
        """데이터 소스 생성 성공"""
        mock_response = Mock()
        mock_response.content = b'{"datasource": {"id": 1, "name": "InfluxDB"}}'
        mock_response.json.return_value = {"datasource": {"id": 1, "name": "InfluxDB"}}
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'), \
             patch.object(settings, 'INFLUX_URL', 'http://influx:8086'), \
             patch.object(settings, 'INFLUX_ORG', 'test-org'), \
             patch.object(settings, 'INFLUX_BUCKET', 'test-bucket'), \
             patch.object(settings, 'INFLUX_TOKEN', 'test-token'):
            client = GrafanaClient()
            result = client.create_datasource(name="InfluxDB")
            
            assert result["datasource"]["name"] == "InfluxDB"
            mock_client.request.assert_called_once()
    
    @patch('httpx.Client')
    def test_create_datasource_conflict(self, mock_client_class):
        """데이터 소스 중복 생성 처리"""
        # 첫 번째 요청: 409 Conflict
        conflict_response = Mock()
        conflict_response.status_code = 409
        conflict_error = httpx.HTTPStatusError("Conflict", request=Mock(), response=conflict_response)
        
        # 두 번째 요청: 데이터 소스 목록 조회
        list_response = Mock()
        list_response.content = b'[{"id": 1, "name": "InfluxDB"}]'
        list_response.json.return_value = [{"id": 1, "name": "InfluxDB"}]
        list_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.side_effect = [conflict_error, list_response]
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'), \
             patch.object(settings, 'INFLUX_URL', 'http://influx:8086'), \
             patch.object(settings, 'INFLUX_ORG', 'test-org'), \
             patch.object(settings, 'INFLUX_BUCKET', 'test-bucket'), \
             patch.object(settings, 'INFLUX_TOKEN', 'test-token'):
            client = GrafanaClient()
            result = client.create_datasource(name="InfluxDB")
            
            assert result["name"] == "InfluxDB"
            assert mock_client.request.call_count == 2
    
    @patch('httpx.Client')
    def test_get_datasource_by_name_found(self, mock_client_class):
        """데이터 소스 조회 성공"""
        mock_response = Mock()
        mock_response.content = b'[{"id": 1, "name": "InfluxDB"}, {"id": 2, "name": "Other"}]'
        mock_response.json.return_value = [
            {"id": 1, "name": "InfluxDB"},
            {"id": 2, "name": "Other"}
        ]
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            client = GrafanaClient()
            result = client.get_datasource_by_name("InfluxDB")
            
            assert result is not None
            assert result["name"] == "InfluxDB"
    
    @patch('httpx.Client')
    def test_get_datasource_by_name_not_found(self, mock_client_class):
        """데이터 소스 조회 실패"""
        mock_response = Mock()
        mock_response.content = b'[{"id": 1, "name": "Other"}]'
        mock_response.json.return_value = [{"id": 1, "name": "Other"}]
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            client = GrafanaClient()
            result = client.get_datasource_by_name("InfluxDB")
            
            assert result is None
    
    @patch('httpx.Client')
    def test_get_datasource_by_name_error(self, mock_client_class):
        """데이터 소스 조회 중 에러 처리"""
        mock_client = MagicMock()
        mock_client.request.side_effect = httpx.HTTPError("Error")
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            client = GrafanaClient()
            result = client.get_datasource_by_name("InfluxDB")
            
            assert result is None
    
    @patch('httpx.Client')
    def test_create_dashboard_success(self, mock_client_class):
        """대시보드 생성 성공"""
        mock_response = Mock()
        mock_response.content = b'{"dashboard": {"id": 1, "title": "Test"}}'
        mock_response.json.return_value = {"dashboard": {"id": 1, "title": "Test"}}
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            client = GrafanaClient()
            panels = [{"id": 1, "title": "Panel 1"}]
            result = client.create_dashboard(title="Test Dashboard", panels=panels)
            
            assert result["dashboard"]["title"] == "Test"
            mock_client.request.assert_called_once()
    
    @patch('httpx.Client')
    def test_create_dashboard_error(self, mock_client_class):
        """대시보드 생성 실패"""
        mock_client = MagicMock()
        mock_client.request.side_effect = httpx.HTTPError("Error")
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            client = GrafanaClient()
            panels = [{"id": 1, "title": "Panel 1"}]
            
            with pytest.raises(httpx.HTTPError):
                client.create_dashboard(title="Test Dashboard", panels=panels)
    
    @patch('httpx.Client')
    def test_create_sensor_dashboard_success(self, mock_client_class):
        """센서 대시보드 생성 성공"""
        # 데이터 소스 조회 응답
        datasource_response = Mock()
        datasource_response.content = b'[{"id": 1, "name": "InfluxDB", "uid": "ds-uid"}]'
        datasource_response.json.return_value = [{"id": 1, "name": "InfluxDB", "uid": "ds-uid"}]
        datasource_response.raise_for_status = Mock()
        
        # 대시보드 생성 응답
        dashboard_response = Mock()
        dashboard_response.content = b'{"dashboard": {"id": 1, "title": "MOBY Sensor Dashboard"}}'
        dashboard_response.json.return_value = {"dashboard": {"id": 1, "title": "MOBY Sensor Dashboard"}}
        dashboard_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.side_effect = [datasource_response, dashboard_response]
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'), \
             patch.object(settings, 'INFLUX_BUCKET', 'test-bucket'):
            client = GrafanaClient()
            result = client.create_sensor_dashboard()
            
            assert result["dashboard"]["title"] == "MOBY Sensor Dashboard"
            assert mock_client.request.call_count == 2
    
    @patch('httpx.Client')
    def test_create_sensor_dashboard_datasource_not_found(self, mock_client_class):
        """센서 대시보드 생성 시 데이터 소스 없음"""
        mock_response = Mock()
        mock_response.content = b'[]'
        mock_response.json.return_value = []
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            client = GrafanaClient()
            
            with pytest.raises(ValueError, match="데이터 소스를 찾을 수 없습니다"):
                client.create_sensor_dashboard()


class TestGetGrafanaClient:
    """get_grafana_client 함수 테스트"""
    
    def test_get_grafana_client_success(self):
        """싱글톤 인스턴스 반환 성공"""
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            # 모듈 레벨 변수 초기화
            import backend.api.services.grafana_client as grafana_module
            grafana_module._grafana_client = None
            
            client1 = get_grafana_client()
            client2 = get_grafana_client()
            
            assert client1 is not None
            assert client2 is not None
            assert client1 is client2  # 싱글톤 확인
    
    def test_get_grafana_client_failure(self):
        """초기화 실패 시 None 반환"""
        with patch.object(settings, 'GRAFANA_URL', ''), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            # 모듈 레벨 변수 초기화
            import backend.api.services.grafana_client as grafana_module
            grafana_module._grafana_client = None
            
            client = get_grafana_client()
            
            assert client is None
    
    @patch('httpx.Client')
    def test_request_with_params(self, mock_client_class):
        """쿼리 파라미터가 있는 요청 테스트"""
        mock_response = Mock()
        mock_response.content = b'{"result": "ok"}'
        mock_response.json.return_value = {"result": "ok"}
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            client = GrafanaClient()
            result = client._request("GET", "/api/datasources", params={"type": "influxdb"})
            
            assert result == {"result": "ok"}
            call_args = mock_client.request.call_args
            assert call_args.kwargs["params"] == {"type": "influxdb"}
    
    @patch('httpx.Client')
    def test_request_post_with_data(self, mock_client_class):
        """POST 요청 데이터 전송 테스트"""
        mock_response = Mock()
        mock_response.content = b'{"id": 1}'
        mock_response.json.return_value = {"id": 1}
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            client = GrafanaClient()
            result = client._request("POST", "/api/datasources", data={"name": "Test"})
            
            assert result == {"id": 1}
            call_args = mock_client.request.call_args
            assert call_args.kwargs["json"] == {"name": "Test"}
    
    @patch('httpx.Client')
    def test_request_generic_exception(self, mock_client_class):
        """일반 예외 처리 테스트"""
        mock_client = MagicMock()
        mock_client.request.side_effect = ValueError("Unexpected error")
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            client = GrafanaClient()
            
            with pytest.raises(ValueError):
                client._request("GET", "/api/health")
    
    @patch('httpx.Client')
    def test_create_datasource_with_custom_json_data(self, mock_client_class):
        """커스텀 JSON 데이터로 데이터 소스 생성"""
        mock_response = Mock()
        mock_response.content = b'{"datasource": {"id": 1, "name": "Custom"}}'
        mock_response.json.return_value = {"datasource": {"id": 1, "name": "Custom"}}
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'), \
             patch.object(settings, 'INFLUX_URL', 'http://influx:8086'), \
             patch.object(settings, 'INFLUX_ORG', 'test-org'), \
             patch.object(settings, 'INFLUX_BUCKET', 'test-bucket'), \
             patch.object(settings, 'INFLUX_TOKEN', 'test-token'):
            client = GrafanaClient()
            custom_json = {"version": "Flux", "customField": "value"}
            custom_secure = {"token": "custom-token"}
            
            result = client.create_datasource(
                name="Custom",
                json_data=custom_json,
                secure_json_data=custom_secure
            )
            
            assert result["datasource"]["name"] == "Custom"
            call_args = mock_client.request.call_args
            assert call_args.kwargs["json"]["jsonData"] == custom_json
            assert call_args.kwargs["json"]["secureJsonData"] == custom_secure
    
    @patch('httpx.Client')
    def test_create_datasource_with_custom_url(self, mock_client_class):
        """커스텀 URL로 데이터 소스 생성"""
        mock_response = Mock()
        mock_response.content = b'{"datasource": {"id": 1, "name": "Custom"}}'
        mock_response.json.return_value = {"datasource": {"id": 1, "name": "Custom"}}
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'), \
             patch.object(settings, 'INFLUX_ORG', 'test-org'), \
             patch.object(settings, 'INFLUX_BUCKET', 'test-bucket'), \
             patch.object(settings, 'INFLUX_TOKEN', 'test-token'):
            client = GrafanaClient()
            
            result = client.create_datasource(
                name="Custom",
                url="http://custom-influx:8086"
            )
            
            assert result["datasource"]["name"] == "Custom"
            call_args = mock_client.request.call_args
            assert call_args.kwargs["json"]["url"] == "http://custom-influx:8086"
    
    @patch('httpx.Client')
    def test_create_datasource_with_access_direct(self, mock_client_class):
        """direct 접근 방식으로 데이터 소스 생성"""
        mock_response = Mock()
        mock_response.content = b'{"datasource": {"id": 1, "name": "Direct"}}'
        mock_response.json.return_value = {"datasource": {"id": 1, "name": "Direct"}}
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'), \
             patch.object(settings, 'INFLUX_URL', 'http://influx:8086'), \
             patch.object(settings, 'INFLUX_ORG', 'test-org'), \
             patch.object(settings, 'INFLUX_BUCKET', 'test-bucket'), \
             patch.object(settings, 'INFLUX_TOKEN', 'test-token'):
            client = GrafanaClient()
            
            result = client.create_datasource(
                name="Direct",
                access="direct"
            )
            
            assert result["datasource"]["name"] == "Direct"
            call_args = mock_client.request.call_args
            assert call_args.kwargs["json"]["access"] == "direct"
    
    @patch('httpx.Client')
    def test_create_datasource_with_is_default(self, mock_client_class):
        """기본 데이터 소스로 설정"""
        mock_response = Mock()
        mock_response.content = b'{"datasource": {"id": 1, "name": "Default"}}'
        mock_response.json.return_value = {"datasource": {"id": 1, "name": "Default"}}
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'), \
             patch.object(settings, 'INFLUX_URL', 'http://influx:8086'), \
             patch.object(settings, 'INFLUX_ORG', 'test-org'), \
             patch.object(settings, 'INFLUX_BUCKET', 'test-bucket'), \
             patch.object(settings, 'INFLUX_TOKEN', 'test-token'):
            client = GrafanaClient()
            
            result = client.create_datasource(
                name="Default",
                is_default=True
            )
            
            assert result["datasource"]["name"] == "Default"
            call_args = mock_client.request.call_args
            assert call_args.kwargs["json"]["isDefault"] is True
    
    @patch('httpx.Client')
    def test_create_datasource_http_status_error(self, mock_client_class):
        """HTTP 상태 에러 처리 (409 외)"""
        error_response = Mock()
        error_response.status_code = 500
        http_error = httpx.HTTPStatusError("Server error", request=Mock(), response=error_response)
        
        mock_client = MagicMock()
        mock_client.request.side_effect = http_error
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'), \
             patch.object(settings, 'INFLUX_URL', 'http://influx:8086'), \
             patch.object(settings, 'INFLUX_ORG', 'test-org'), \
             patch.object(settings, 'INFLUX_BUCKET', 'test-bucket'), \
             patch.object(settings, 'INFLUX_TOKEN', 'test-token'):
            client = GrafanaClient()
            
            with pytest.raises(httpx.HTTPStatusError):
                client.create_datasource(name="Test")
    
    @patch('httpx.Client')
    def test_create_dashboard_with_folder_id(self, mock_client_class):
        """폴더 ID로 대시보드 생성"""
        mock_response = Mock()
        mock_response.content = b'{"dashboard": {"id": 1, "title": "Test"}}'
        mock_response.json.return_value = {"dashboard": {"id": 1, "title": "Test"}}
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            client = GrafanaClient()
            panels = [{"id": 1, "title": "Panel 1"}]
            
            result = client.create_dashboard(
                title="Test Dashboard",
                panels=panels,
                folder_id=10
            )
            
            assert result["dashboard"]["title"] == "Test"
            call_args = mock_client.request.call_args
            assert call_args.kwargs["json"]["folderId"] == 10
    
    @patch('httpx.Client')
    def test_create_dashboard_with_overwrite(self, mock_client_class):
        """덮어쓰기 옵션으로 대시보드 생성"""
        mock_response = Mock()
        mock_response.content = b'{"dashboard": {"id": 1, "title": "Test"}}'
        mock_response.json.return_value = {"dashboard": {"id": 1, "title": "Test"}}
        mock_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'):
            client = GrafanaClient()
            panels = [{"id": 1, "title": "Panel 1"}]
            
            result = client.create_dashboard(
                title="Test Dashboard",
                panels=panels,
                overwrite=True
            )
            
            assert result["dashboard"]["title"] == "Test"
            call_args = mock_client.request.call_args
            assert call_args.kwargs["json"]["overwrite"] is True
    
    @patch('httpx.Client')
    def test_create_sensor_dashboard_with_custom_title(self, mock_client_class):
        """커스텀 제목으로 센서 대시보드 생성"""
        datasource_response = Mock()
        datasource_response.content = b'[{"id": 1, "name": "InfluxDB", "uid": "ds-uid"}]'
        datasource_response.json.return_value = [{"id": 1, "name": "InfluxDB", "uid": "ds-uid"}]
        datasource_response.raise_for_status = Mock()
        
        dashboard_response = Mock()
        dashboard_response.content = b'{"dashboard": {"id": 1, "title": "Custom Title"}}'
        dashboard_response.json.return_value = {"dashboard": {"id": 1, "title": "Custom Title"}}
        dashboard_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.side_effect = [datasource_response, dashboard_response]
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'), \
             patch.object(settings, 'INFLUX_BUCKET', 'test-bucket'):
            client = GrafanaClient()
            
            result = client.create_sensor_dashboard(dashboard_title="Custom Title")
            
            assert result["dashboard"]["title"] == "Custom Title"
    
    @patch('httpx.Client')
    def test_create_sensor_dashboard_with_custom_datasource(self, mock_client_class):
        """커스텀 데이터 소스로 센서 대시보드 생성"""
        datasource_response = Mock()
        datasource_response.content = b'[{"id": 1, "name": "CustomDS", "uid": "custom-uid"}]'
        datasource_response.json.return_value = [{"id": 1, "name": "CustomDS", "uid": "custom-uid"}]
        datasource_response.raise_for_status = Mock()
        
        dashboard_response = Mock()
        dashboard_response.content = b'{"dashboard": {"id": 1, "title": "Test"}}'
        dashboard_response.json.return_value = {"dashboard": {"id": 1, "title": "Test"}}
        dashboard_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.side_effect = [datasource_response, dashboard_response]
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'), \
             patch.object(settings, 'INFLUX_BUCKET', 'test-bucket'):
            client = GrafanaClient()
            
            result = client.create_sensor_dashboard(datasource_name="CustomDS")
            
            assert result["dashboard"]["title"] == "Test"
            assert mock_client.request.call_count == 2
    
    @patch('httpx.Client')
    def test_create_sensor_dashboard_datasource_with_id_only(self, mock_client_class):
        """데이터 소스에 uid가 없고 id만 있는 경우"""
        datasource_response = Mock()
        datasource_response.content = b'[{"id": 1, "name": "InfluxDB"}]'
        datasource_response.json.return_value = [{"id": 1, "name": "InfluxDB"}]
        datasource_response.raise_for_status = Mock()
        
        dashboard_response = Mock()
        dashboard_response.content = b'{"dashboard": {"id": 1, "title": "Test"}}'
        dashboard_response.json.return_value = {"dashboard": {"id": 1, "title": "Test"}}
        dashboard_response.raise_for_status = Mock()
        
        mock_client = MagicMock()
        mock_client.request.side_effect = [datasource_response, dashboard_response]
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch.object(settings, 'GRAFANA_URL', 'http://localhost:3000'), \
             patch.object(settings, 'GRAFANA_API_KEY', 'test-key'), \
             patch.object(settings, 'INFLUX_BUCKET', 'test-bucket'):
            client = GrafanaClient()
            
            result = client.create_sensor_dashboard()
            
            assert result["dashboard"]["title"] == "Test"

