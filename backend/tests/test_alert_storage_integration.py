"""
알림 저장소 통합 테스트

알림 생성, 저장, 조회 기능을 테스트합니다.
"""

import pytest
from fastapi import status
from backend.api.services.alert_engine import process_alert, AlertPayloadModel


class TestAlertStorageIntegration:
    """알림 저장소 통합 테스트"""
    
    def test_alert_created_and_saved_to_database(
        self,
        client,
        db_session,
        sample_alert_data
    ):
        """알림 생성 및 데이터베이스 저장 테스트"""
        # 알림 생성 요청
        response = client.post("/alerts/evaluate", json=sample_alert_data)
        
        # 이상이 탐지되면 201, 아니면 204
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_204_NO_CONTENT]
        
        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            assert data["success"] is True
            assert "id" in data["data"]
            
            # 데이터베이스에서 확인
            from backend.api.models.alert import Alert
            alert = db_session.query(Alert).filter(
                Alert.alert_id == data["data"]["id"]
            ).first()
            
            assert alert is not None
            assert alert.sensor_id == sample_alert_data["sensor_id"]
            assert alert.level in ["info", "warning", "critical"]
    
    def test_get_latest_alerts_success(
        self,
        client,
        db_session,
        sample_alert_data
    ):
        """최신 알림 조회 성공 테스트"""
        # 알림 생성 (여러 개)
        for i in range(3):
            alert_data = sample_alert_data.copy()
            alert_data["vector"] = [1.5 + i, 2.3 + i, 3.1 + i]
            response = client.post("/alerts/evaluate", json=alert_data)
            # 이상이 탐지되지 않을 수 있으므로 204도 허용
        
        # 최신 알림 조회
        response = client.get("/alerts/latest?limit=10")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_get_latest_alerts_with_filters(
        self,
        client,
        db_session,
        sample_alert_data
    ):
        """필터링을 사용한 최신 알림 조회 테스트"""
        # 센서 ID 필터링
        response = client.get(
            f"/alerts/latest?limit=10&sensor_id={sample_alert_data['sensor_id']}"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        
        # 레벨 필터링
        response = client.get("/alerts/latest?limit=10&level=critical")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
    
    def test_get_latest_alerts_invalid_limit(self, client):
        """잘못된 limit 파라미터 테스트"""
        # limit이 0인 경우
        response = client.get("/alerts/latest?limit=0")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # limit이 100을 초과하는 경우
        response = client.get("/alerts/latest?limit=101")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_get_latest_alerts_invalid_level(self, client):
        """잘못된 level 파라미터 테스트"""
        response = client.get("/alerts/latest?level=invalid")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        # 에러 응답 형식 확인
        if "error" in data:
            assert "level" in data["error"]["message"].lower()
        elif "detail" in data:
            # FastAPI 기본 에러 형식
            assert isinstance(data["detail"], (str, dict))

