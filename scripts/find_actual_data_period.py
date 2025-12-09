"""
InfluxDB에서 실제 데이터가 있는 기간 찾기
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.api.services.schemas.models.core.config import settings
from backend.api.services.influx_client import influx_manager


def find_data_period():
    """실제 데이터가 있는 기간 찾기"""
    print("=" * 60)
    print("InfluxDB 실제 데이터 기간 확인")
    print("=" * 60)
    
    try:
        # moby_sensors에서 데이터 범위 확인
        query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: -30d)
          |> filter(fn: (r) => r["_measurement"] == "moby_sensors")
          |> group()
          |> sort(columns: ["_time"])
          |> first()
        '''
        
        result = influx_manager.query_api.query(query=query, org=settings.INFLUX_ORG)
        
        first_time = None
        for table in result:
            for record in table.records:
                first_time = record.get_time()
                break
            if first_time:
                break
        
        # 마지막 데이터 확인
        query_last = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: -30d)
          |> filter(fn: (r) => r["_measurement"] == "moby_sensors")
          |> group()
          |> sort(columns: ["_time"], desc: true)
          |> first()
        '''
        
        result_last = influx_manager.query_api.query(query=query_last, org=settings.INFLUX_ORG)
        
        last_time = None
        for table in result_last:
            for record in table.records:
                last_time = record.get_time()
                break
            if last_time:
                break
        
        # Host ID 목록 확인
        query_hosts = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: -30d)
          |> filter(fn: (r) => r["_measurement"] == "moby_sensors")
          |> group(columns: ["host"])
          |> distinct(column: "host")
          |> limit(n: 10)
        '''
        
        result_hosts = influx_manager.query_api.query(query=query_hosts, org=settings.INFLUX_ORG)
        
        hosts = []
        for table in result_hosts:
            for record in table.records:
                host = record.values.get("host")
                if host and host not in hosts:
                    hosts.append(host)
        
        print(f"\n📅 데이터 기간:")
        if first_time and last_time:
            print(f"   시작: {first_time}")
            print(f"   종료: {last_time}")
            print(f"   기간: {(last_time - first_time).days}일")
        else:
            print("   ⚠️ 데이터를 찾을 수 없습니다")
        
        print(f"\n📱 발견된 Host ID:")
        if hosts:
            for i, host in enumerate(hosts, 1):
                print(f"   {i}. {host}")
        else:
            print("   ⚠️ Host ID를 찾을 수 없습니다")
        
        print()
        
        return first_time, last_time, hosts
        
    except Exception as e:
        print(f"❌ 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return None, None, []


if __name__ == "__main__":
    first_time, last_time, hosts = find_data_period()
    
    if first_time and last_time and hosts:
        print("=" * 60)
        print("✅ 실제 데이터 발견!")
        print("=" * 60)
        print(f"\n보고서 생성에 사용할 정보:")
        print(f"   시작 시간: {first_time}")
        print(f"   종료 시간: {last_time}")
        print(f"   Host ID: {hosts[0] if hosts else 'N/A'}")
        print()

