"""
보고서 서비스 단위 테스트

ReportDataService의 데이터 조회 기능을 테스트합니다.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from backend.api.services.report_service import ReportDataService, get_report_service


class TestReportDataService:
    """ReportDataService 클래스 테스트"""
    
    @pytest.fixture
    def mock_influx_client(self):
        """InfluxDB 클라이언트 모킹"""
        with patch('backend.api.services.report_service.influx_manager') as mock_manager:
            mock_query_api = MagicMock()
            mock_manager.query_api = mock_query_api
            mock_manager.bucket = "test_bucket"
            yield mock_manager
    
    @pytest.fixture
    def mock_db_session(self):
        """데이터베이스 세션 모킹"""
        mock_session = MagicMock(spec=Session)
        return mock_session
    
    @pytest.fixture
    def report_service(self, mock_influx_client):
        """ReportDataService 인스턴스 생성"""
        with patch('backend.api.services.report_service.settings') as mock_settings:
            mock_settings.INFLUX_BUCKET = "test_bucket"
            mock_settings.INFLUX_ORG = "test_org"
            service = ReportDataService()
            service.influx_client = mock_influx_client
            return service
    
    def test_service_initialization(self, mock_influx_client):
        """서비스 초기화 테스트"""
        with patch('backend.api.services.report_service.settings') as mock_settings:
            mock_settings.INFLUX_BUCKET = "test_bucket"
            mock_settings.INFLUX_ORG = "test_org"
            service = ReportDataService()
            assert service.bucket == "test_bucket"
            assert service.org == "test_org"
    
    def test_fetch_report_data_structure(self, report_service, mock_db_session):
        """fetch_report_data가 올바른 구조를 반환하는지 테스트"""
        start_time = datetime.now(timezone.utc) - timedelta(days=7)
        end_time = datetime.now(timezone.utc)
        equipment_id = "test_equipment"
        
        # 알람 데이터 모킹
        with patch.object(report_service, '_fetch_alarms', return_value=[]), \
             patch.object(report_service, '_fetch_sensor_stats', return_value={}), \
             patch.object(report_service, '_fetch_mlp_anomalies', return_value=[]), \
             patch.object(report_service, '_fetch_if_anomalies', return_value=[]), \
             patch.object(report_service, '_calculate_correlations', return_value={}):
            
            result = report_service.fetch_report_data(
                start_time=start_time,
                end_time=end_time,
                equipment_id=equipment_id,
                db=mock_db_session
            )
            
            # 필수 키 확인
            assert "metadata" in result
            assert "sensor_stats" in result
            assert "alarms" in result
            assert "mlp_anomalies" in result
            assert "if_anomalies" in result
            assert "correlations" in result
            
            # 메타데이터 구조 확인
            metadata = result["metadata"]
            assert "period_start" in metadata
            assert "period_end" in metadata
            assert "equipment" in metadata
            assert "generated_at" in metadata
    
    def test_fetch_report_data_with_real_data(self, report_service, mock_db_session):
        """실제 데이터 구조로 fetch_report_data 테스트"""
        start_time = datetime.now(timezone.utc) - timedelta(days=1)
        end_time = datetime.now(timezone.utc)
        equipment_id = "test_equipment"
        
        # 모의 센서 통계 데이터
        mock_sensor_stats = {
            "temperature": {
                "mean": 38.2,
                "min": 22.1,
                "max": 52.3,
                "std": 6.8,
                "p95": 48.5,
                "missing_rate": 0.002
            }
        }
        
        # 모의 알람 데이터
        mock_alarms = [
            {
                "timestamp": (start_time + timedelta(hours=1)).isoformat(),
                "sensor": equipment_id,
                "level": "WARNING",
                "message": "임계값 초과",
                "value": 52.3,
                "threshold": 50.0
            }
        ]
        
        with patch.object(report_service, '_fetch_alarms', return_value=mock_alarms), \
             patch.object(report_service, '_fetch_sensor_stats', return_value=mock_sensor_stats), \
             patch.object(report_service, '_fetch_mlp_anomalies', return_value=[]), \
             patch.object(report_service, '_fetch_if_anomalies', return_value=[]), \
             patch.object(report_service, '_calculate_correlations', return_value={}):
            
            result = report_service.fetch_report_data(
                start_time=start_time,
                end_time=end_time,
                equipment_id=equipment_id,
                db=mock_db_session
            )
            
            assert len(result["alarms"]) == 1
            assert result["alarms"][0]["level"] == "WARNING"
            assert "temperature" in result["sensor_stats"]
    
    def test_fetch_sensor_stats_empty_result(self, report_service):
        """센서 통계 조회 결과가 없을 때 더미 데이터 생성 테스트"""
        start_time = datetime.now(timezone.utc) - timedelta(days=1)
        end_time = datetime.now(timezone.utc)
        
        # InfluxDB 쿼리 결과가 없는 경우 모킹
        mock_query_api = report_service.influx_client.query_api
        mock_query_api.query.return_value = []  # 빈 결과
        
        # InfluxDB 쿼리 결과가 없는 경우 모킹
        mock_query_api = report_service.influx_client.query_api
        mock_query_api.query.return_value = []  # 빈 결과
        
        result = report_service._fetch_sensor_stats(
            start_time=start_time,
            end_time=end_time,
            equipment_id="test_equipment",
            alarms=[]
        )
        
        # 기본 데이터가 생성되었는지 확인
        assert result is not None
        assert isinstance(result, dict)
    
    def test_generate_dummy_data(self, report_service):
        """더미 데이터 생성 함수 테스트"""
        dummy_stats = report_service._get_default_sensor_stats()
        
        assert "temperature" in dummy_stats
        assert "humidity" in dummy_stats
        assert "vibration" in dummy_stats
        assert "sound" in dummy_stats
        
        # temperature 구조 확인
        temp = dummy_stats["temperature"]
        assert "mean" in temp
        assert "min" in temp
        assert "max" in temp
        assert "std" in temp
        assert "p95" in temp
        assert "threshold_violations" in temp
    
    def test_get_report_service_singleton(self):
        """get_report_service가 싱글톤 패턴으로 동작하는지 테스트"""
        with patch('backend.api.services.report_service._report_service', None):
            service1 = get_report_service()
            service2 = get_report_service()
            
            # 같은 인스턴스인지 확인
            assert service1 is service2


class TestReportServiceIntegration:
    """보고서 서비스 통합 테스트"""
    
    @pytest.fixture
    def mock_db_session(self):
        """데이터베이스 세션 모킹"""
        mock_session = MagicMock(spec=Session)
        return mock_session
    
    def test_error_handling_in_fetch_report_data(self, mock_db_session):
        """fetch_report_data의 에러 처리 테스트"""
        with patch('backend.api.services.report_service.ReportDataService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.fetch_report_data.side_effect = Exception("테스트 에러")
            mock_service_class.return_value = mock_service
            
            service = ReportDataService()
            service.influx_client = MagicMock()
            
            # 에러 발생 시 빈 구조 반환하는지 확인
            start_time = datetime.now(timezone.utc) - timedelta(days=1)
            end_time = datetime.now(timezone.utc)
            
            # 실제 서비스의 에러 처리 테스트
            with patch.object(service, '_fetch_sensor_stats', side_effect=Exception("에러")):
                result = service.fetch_report_data(
                    start_time=start_time,
                    end_time=end_time,
                    equipment_id="test",
                    db=mock_db_session
                )
                
                # 에러 발생 시에도 기본 구조는 반환되어야 함
                assert "metadata" in result
                assert "sensor_stats" in result

