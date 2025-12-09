"""
Grafana 대시보드 데이터 소스 확인 스크립트

운영관리 대시보드에서 사용하는 데이터가 InfluxDB에 있는지 확인합니다.
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timedelta
from backend.api.services.schemas.models.core.config import settings
from backend.api.services.influx_client import influx_manager

def check_measurement_data(measurement: str, field: str, minutes: int = 60):
    """특정 measurement와 field의 데이터 확인"""
    print(f"\n{'='*60}")
    print(f"Measurement: {measurement}, Field: {field}")
    print(f"{'='*60}")
    
    try:
        query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: -{minutes}m)
          |> filter(fn: (r) => r["_measurement"] == "{measurement}")
          |> filter(fn: (r) => r["_field"] == "{field}")
          |> last()
        '''
        
        result = influx_manager.query_api.query(query=query, org=settings.INFLUX_ORG)
        
        records = []
        for table in result:
            for record in table.records:
                records.append({
                    "time": record.get_time(),
                    "value": record.get_value(),
                    "device_id": record.values.get("device_id", "N/A"),
                })
        
        if records:
            print(f"✅ 데이터 발견: {len(records)}개 레코드")
            for record in records:
                print(f"   - Device: {record['device_id']}, Value: {record['value']}, Time: {record['time']}")
            return True
        else:
            print(f"⚠️ 데이터 없음 (최근 {minutes}분)")
            return False
            
    except Exception as e:
        print(f"❌ 쿼리 실패: {e}")
        return False

def check_all_measurements():
    """모든 measurement 확인"""
    print(f"\n{'='*60}")
    print("모든 Measurement 목록 확인")
    print(f"{'='*60}")
    
    try:
        query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: -24h)
          |> group()
          |> distinct(column: "_measurement")
        '''
        
        result = influx_manager.query_api.query(query=query, org=settings.INFLUX_ORG)
        
        measurements = set()
        for table in result:
            for record in table.records:
                measurement = record.get_value()
                if measurement:
                    measurements.add(measurement)
        
        if measurements:
            print(f"✅ 발견된 Measurement: {len(measurements)}개")
            for m in sorted(measurements):
                print(f"   - {m}")
        else:
            print("⚠️ Measurement가 없습니다.")
        
        return list(measurements)
        
    except Exception as e:
        print(f"❌ 쿼리 실패: {e}")
        return []

def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("Grafana 대시보드 데이터 소스 확인")
    print("=" * 60)
    
    # InfluxDB 연결 확인
    try:
        health = influx_manager.client.health()
        print(f"✅ InfluxDB 연결 성공")
        print(f"   URL: {settings.INFLUX_URL}")
        print(f"   Bucket: {settings.INFLUX_BUCKET}")
    except Exception as e:
        print(f"❌ InfluxDB 연결 실패: {e}")
        return
    
    # 모든 measurement 확인
    measurements = check_all_measurements()
    
    # 운영관리 대시보드에서 사용하는 데이터 확인
    print(f"\n{'='*60}")
    print("운영관리 대시보드 데이터 확인")
    print(f"{'='*60}")
    
    # 1. 설비 상태 (health 필드)
    has_health = check_measurement_data("conveyor_cycle", "health", minutes=60)
    
    # 2. 예상 고장 시각 (fail_time 필드)
    has_fail_time = check_measurement_data("conveyor_cycle", "fail_time", minutes=60)
    
    # 3. RUL (rul_hours 필드)
    has_rul = check_measurement_data("conveyor_cycle", "rul_hours", minutes=60)
    
    # 4. Cycle Time (avg_cycle_ms 필드)
    has_cycle = check_measurement_data("conveyor_cycle", "avg_cycle_ms", minutes=60)
    
    # 요약
    print(f"\n{'='*60}")
    print("요약")
    print(f"{'='*60}")
    print(f"📊 Measurement 목록: {len(measurements)}개")
    print(f"   {', '.join(measurements) if measurements else '없음'}")
    print()
    print(f"🔍 운영관리 대시보드 데이터:")
    print(f"   설비 상태 (health): {'✅ 있음' if has_health else '❌ 없음'}")
    print(f"   예상 고장 시각 (fail_time): {'✅ 있음' if has_fail_time else '❌ 없음'}")
    print(f"   남은 수명 (rul_hours): {'✅ 있음' if has_rul else '❌ 없음'}")
    print(f"   Cycle Time (avg_cycle_ms): {'✅ 있음' if has_cycle else '❌ 없음'}")
    print()
    
    if not has_health or not has_fail_time:
        print("💡 문제 원인:")
        print("   Grafana 대시보드는 'conveyor_cycle' measurement의 데이터를 필요로 합니다.")
        print("   하지만 현재 InfluxDB에는 'sensor_data' measurement만 저장되고 있습니다.")
        print()
        print("   해결 방법:")
        print("   1. 실제 센서에서 'conveyor_cycle' measurement로 데이터 전송")
        print("   2. 또는 'sensor_data'를 'conveyor_cycle'로 변환하는 스크립트 작성")
        print("   3. 또는 Grafana 대시보드 쿼리를 'sensor_data' measurement로 수정")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

