"""
Grafana API 클라이언트 서비스 모듈

Grafana API를 사용하여 데이터 소스와 대시보드를 프로그래밍 방식으로 관리합니다.
"""

import logging
from typing import Dict, Any, Optional, List
import httpx
from .schemas.models.core.config import settings

logger = logging.getLogger(__name__)


class GrafanaClient:
    """Grafana API 클라이언트"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Grafana 클라이언트 초기화
        
        Args:
            base_url: Grafana 서버 URL (기본값: 설정 파일의 값)
            api_key: Grafana API 키 (기본값: 설정 파일의 값)
        """
        self.base_url = (base_url or settings.GRAFANA_URL).rstrip('/')
        self.api_key = api_key or settings.GRAFANA_API_KEY
        
        if not self.base_url:
            raise ValueError("GRAFANA_URL이 설정되지 않았습니다.")
        if not self.api_key:
            raise ValueError("GRAFANA_API_KEY가 설정되지 않았습니다.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        logger.info(f"Grafana 클라이언트 초기화 완료. URL: {self.base_url}")
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Grafana API 요청 실행
        
        Args:
            method: HTTP 메서드 (GET, POST, PUT, DELETE)
            endpoint: API 엔드포인트 (예: "/api/datasources")
            data: 요청 본문 데이터
            params: 쿼리 파라미터
            
        Returns:
            API 응답 데이터
            
        Raises:
            httpx.HTTPError: HTTP 요청 실패 시
            ValueError: API 응답이 실패한 경우
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params
                )
                response.raise_for_status()
                
                # 응답이 비어있는 경우
                if not response.content:
                    return {}
                
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Grafana API 요청 실패: {method} {endpoint}, Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Grafana API 요청 중 예상치 못한 오류: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Grafana 연결 테스트
        
        Returns:
            연결 성공 시 True, 실패 시 False
        """
        try:
            self._request("GET", "/api/health")
            logger.info("Grafana 연결 테스트 성공")
            return True
        except Exception as e:
            logger.warning(f"Grafana 연결 테스트 실패: {e}")
            return False
    
    def create_datasource(
        self,
        name: str,
        type: str = "influxdb",
        url: Optional[str] = None,
        access: str = "proxy",
        is_default: bool = False,
        json_data: Optional[Dict[str, Any]] = None,
        secure_json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        InfluxDB 데이터 소스 생성
        
        Args:
            name: 데이터 소스 이름
            type: 데이터 소스 타입 (기본값: "influxdb")
            url: InfluxDB URL (기본값: 설정 파일의 값)
            access: 접근 방식 ("proxy" 또는 "direct", 기본값: "proxy")
            is_default: 기본 데이터 소스로 설정할지 여부
            json_data: JSON 데이터 (예: database, organization 등)
            secure_json_data: 보안 JSON 데이터 (예: token)
            
        Returns:
            생성된 데이터 소스 정보
        """
        if not url:
            url = settings.INFLUX_URL
        
        if not json_data:
            json_data = {
                "version": "Flux",
                "organization": settings.INFLUX_ORG,
                "defaultBucket": settings.INFLUX_BUCKET,
                "tlsSkipVerify": False
            }
        
        if not secure_json_data:
            secure_json_data = {
                "token": settings.INFLUX_TOKEN
            }
        
        datasource_data = {
            "name": name,
            "type": type,
            "url": url,
            "access": access,
            "isDefault": is_default,
            "jsonData": json_data,
            "secureJsonData": secure_json_data
        }
        
        try:
            result = self._request("POST", "/api/datasources", data=datasource_data)
            logger.info(f"데이터 소스 생성 성공: {name}")
            return result
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                logger.warning(f"데이터 소스가 이미 존재합니다: {name}")
                # 기존 데이터 소스 조회
                return self.get_datasource_by_name(name)
            raise
    
    def get_datasource_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        이름으로 데이터 소스 조회
        
        Args:
            name: 데이터 소스 이름
            
        Returns:
            데이터 소스 정보 또는 None
        """
        try:
            datasources = self._request("GET", "/api/datasources")
            for ds in datasources:
                if ds.get("name") == name:
                    return ds
            return None
        except Exception as e:
            logger.error(f"데이터 소스 조회 실패: {e}")
            return None
    
    def create_dashboard(
        self,
        title: str,
        panels: List[Dict[str, Any]],
        folder_id: Optional[int] = None,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        대시보드 생성
        
        Args:
            title: 대시보드 제목
            panels: 패널 목록
            folder_id: 폴더 ID (선택사항)
            overwrite: 기존 대시보드를 덮어쓸지 여부
            
        Returns:
            생성된 대시보드 정보
        """
        dashboard_data = {
            "dashboard": {
                "title": title,
                "panels": panels,
                "timezone": "browser",
                "schemaVersion": 16,
                "version": 0,
                "refresh": "30s"
            },
            "folderId": folder_id,
            "overwrite": overwrite
        }
        
        try:
            result = self._request("POST", "/api/dashboards/db", data=dashboard_data)
            logger.info(f"대시보드 생성 성공: {title}")
            return result
        except Exception as e:
            logger.error(f"대시보드 생성 실패: {e}")
            raise
    
    def create_sensor_dashboard(
        self,
        dashboard_title: str = "MOBY Sensor Dashboard",
        datasource_name: str = "InfluxDB"
    ) -> Dict[str, Any]:
        """
        센서 데이터용 기본 대시보드 생성
        
        Args:
            dashboard_title: 대시보드 제목
            datasource_name: 데이터 소스 이름
            
        Returns:
            생성된 대시보드 정보
        """
        # 데이터 소스 ID 조회
        datasource = self.get_datasource_by_name(datasource_name)
        if not datasource:
            raise ValueError(f"데이터 소스를 찾을 수 없습니다: {datasource_name}")
        
        datasource_uid = datasource.get("uid", datasource.get("id"))
        
        # 패널 정의
        panels = [
            {
                "id": 1,
                "title": "Temperature",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                "targets": [
                    {
                        "datasource": {"type": "influxdb", "uid": datasource_uid},
                        "query": f'''from(bucket: "{settings.INFLUX_BUCKET}")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "sensor_data")
  |> filter(fn: (r) => r["_field"] == "temperature")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")''',
                        "refId": "A"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "unit": "celsius",
                        "color": {"mode": "palette-classic"}
                    }
                }
            },
            {
                "id": 2,
                "title": "Humidity",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                "targets": [
                    {
                        "datasource": {"type": "influxdb", "uid": datasource_uid},
                        "query": f'''from(bucket: "{settings.INFLUX_BUCKET}")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "sensor_data")
  |> filter(fn: (r) => r["_field"] == "humidity")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")''',
                        "refId": "A"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "unit": "percent",
                        "color": {"mode": "palette-classic"}
                    }
                }
            },
            {
                "id": 3,
                "title": "Vibration",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                "targets": [
                    {
                        "datasource": {"type": "influxdb", "uid": datasource_uid},
                        "query": f'''from(bucket: "{settings.INFLUX_BUCKET}")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "sensor_data")
  |> filter(fn: (r) => r["_field"] == "vibration")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")''',
                        "refId": "A"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "unit": "short",
                        "color": {"mode": "palette-classic"}
                    }
                }
            },
            {
                "id": 4,
                "title": "Sound",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                "targets": [
                    {
                        "datasource": {"type": "influxdb", "uid": datasource_uid},
                        "query": f'''from(bucket: "{settings.INFLUX_BUCKET}")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "sensor_data")
  |> filter(fn: (r) => r["_field"] == "sound")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")''',
                        "refId": "A"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "unit": "short",
                        "color": {"mode": "palette-classic"}
                    }
                }
            }
        ]
        
        return self.create_dashboard(
            title=dashboard_title,
            panels=panels,
            overwrite=True
        )


# 싱글톤 인스턴스
_grafana_client: Optional[GrafanaClient] = None


def get_grafana_client() -> Optional[GrafanaClient]:
    """
    Grafana 클라이언트 싱글톤 인스턴스 반환
    
    Returns:
        GrafanaClient 인스턴스 또는 None (설정이 없는 경우)
    """
    global _grafana_client
    
    if _grafana_client is None:
        try:
            _grafana_client = GrafanaClient()
        except (ValueError, Exception) as e:
            logger.warning(f"Grafana 클라이언트 초기화 실패: {e}")
            return None
    
    return _grafana_client

