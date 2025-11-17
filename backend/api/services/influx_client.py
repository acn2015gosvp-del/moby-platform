from influxdb_client import InfluxDBClient as InfluxDBClientLib
from influxdb_client.client.write_api import SYNCHRONOUS
from backend.core.config import settings

# 기존 InfluxDBClient 클래스와 이름이 겹치지 않도록 이름을 InfluxDBClientLib로 변경

class InfluxDBClient:
    def __init__(self, url=settings.INFLUX_URL, token=settings.INFLUX_TOKEN, org=settings.INFLUX_ORG, bucket="moby_data"):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        
        # 1. 클라이언트 연결
        # InfluxDBClientLib는 실제 라이브러리 클래스입니다.
        self.client = InfluxDBClientLib(url=self.url, token=self.token, org=self.org)
        
        # 2. 배치 쓰기 API 설정 (SYNCHRONOUS 옵션은 일단 테스트용)
        # TODO: Dev A는 write_options=ASYNCHRONOUS로 변경하여 비동기 배치 쓰기 로직 구현 (Task 2)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    # 3. 테스트가 요구하는 write_batch 메소드를 구현
    #    (이 메소드가 없어서 오류가 발생했었습니다.)
    def write_batch(self, points):
        """
        테스트가 성공하도록 write_batch 메소드를 최소한으로 구현합니다.
        실제로는 여기서 버퍼링 로직을 구현해야 합니다.
        """
        try:
            # write_api를 사용하여 레코드(points)를 InfluxDB에 기록
            self.write_api.write(
                bucket=self.bucket, 
                org=self.org, 
                record=points
            )
        except Exception as e:
            # 에러 처리 로직
            print(f"InfluxDB write error: {e}")

    # (기존 write_point 로직은 write_batch로 대체되므로 삭제합니다.)