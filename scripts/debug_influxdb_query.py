"""
InfluxDB 쿼리 디버깅 - 실제 데이터 확인
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timezone
from backend.api.services.schemas.models.core.config import settings
from backend.api.services.influx_client import influx_manager


def debug_query():
    """InfluxDB 쿼리 디버깅"""
    print("=" * 60)
    print("InfluxDB 쿼리 디버깅")
    print("=" * 60)
    
    # 실제 데이터가 있는 기간
    start_rfc3339 = "2025-11-11T00:00:00Z"
    end_rfc3339 = "2025-12-05T23:59:59Z"
    
    # 1. Host ID 필터 없이 데이터 조회
    print("\n1. Host ID 필터 없이 fields_temperature_c 조회:")
    query1 = f'''
    from(bucket: "{settings.INFLUX_BUCKET}")
      |> range(start: {start_rfc3339}, stop: {end_rfc3339})
      |> filter(fn: (r) => r["_measurement"] == "moby_sensors")
      |> filter(fn: (r) => r["_field"] == "fields_temperature_c")
      |> limit(n: 5)
    '''
    
    try:
        result1 = influx_manager.query_api.query(query=query1, org=settings.INFLUX_ORG)
        count = 0
        hosts = set()
        for table in result1:
            for record in table.records:
                count += 1
                host = record.values.get("host")
                if host:
                    hosts.add(host)
                if count <= 3:
                    print(f"   레코드 {count}: host={host}, value={record.get_value()}, time={record.get_time()}")
        
        print(f"   총 {count}개 레코드 발견")
        print(f"   발견된 host 값들: {sorted(hosts)}")
    except Exception as e:
        print(f"   ❌ 오류: {e}")
    
    # 2. 특정 host로 필터링 테스트
    print("\n2. host='44d5516Z'로 필터링 테스트:")
    query2 = f'''
    from(bucket: "{settings.INFLUX_BUCKET}")
      |> range(start: {start_rfc3339}, stop: {end_rfc3339})
      |> filter(fn: (r) => r["_measurement"] == "moby_sensors")
      |> filter(fn: (r) => r["_field"] == "fields_temperature_c")
      |> filter(fn: (r) => r["host"] == "44d5516Z")
      |> limit(n: 5)
    '''
    
    try:
        result2 = influx_manager.query_api.query(query=query2, org=settings.INFLUX_ORG)
        count = 0
        for table in result2:
            for record in table.records:
                count += 1
                if count <= 3:
                    print(f"   레코드 {count}: value={record.get_value()}, time={record.get_time()}")
        
        print(f"   총 {count}개 레코드 발견")
        if count == 0:
            print("   ⚠️ 필터링된 데이터가 없습니다!")
    except Exception as e:
        print(f"   ❌ 오류: {e}")
    
    # 3. 모든 host 목록 조회
    print("\n3. moby_sensors의 모든 host 목록:")
    query3 = f'''
    from(bucket: "{settings.INFLUX_BUCKET}")
      |> range(start: {start_rfc3339}, stop: {end_rfc3339})
      |> filter(fn: (r) => r["_measurement"] == "moby_sensors")
      |> group(columns: ["host"])
      |> distinct(column: "host")
      |> limit(n: 20)
    '''
    
    try:
        result3 = influx_manager.query_api.query(query=query3, org=settings.INFLUX_ORG)
        hosts = []
        for table in result3:
            for record in table.records:
                host = record.values.get("host")
                if host and host not in hosts:
                    hosts.append(host)
        
        print(f"   발견된 host: {sorted(hosts)}")
    except Exception as e:
        print(f"   ❌ 오류: {e}")


if __name__ == "__main__":
    debug_query()

