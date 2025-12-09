"""
실제 센서 데이터가 있는 measurement 확인 스크립트
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.api.services.schemas.models.core.config import settings
from backend.api.services.influx_client import influx_manager


def check_measurement_data(measurement_name):
    """특정 measurement의 데이터 확인"""
    try:
        query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: -30d)
          |> filter(fn: (r) => r["_measurement"] == "{measurement_name}")
          |> group()
          |> count()
        '''
        
        result = influx_manager.query_api.query(query=query, org=settings.INFLUX_ORG)
        
        total_count = 0
        for table in result:
            for record in table.records:
                count = record.get_value()
                if count:
                    total_count += int(count)
        
        if total_count > 0:
            # 디바이스 확인
            device_query = f'''
            from(bucket: "{settings.INFLUX_BUCKET}")
              |> range(start: -30d)
              |> filter(fn: (r) => r["_measurement"] == "{measurement_name}")
              |> group(columns: ["device_id"])
              |> distinct(column: "device_id")
              |> keep(columns: ["device_id"])
            '''
            
            device_result = influx_manager.query_api.query(query=device_query, org=settings.INFLUX_ORG)
            
            devices = []
            for table in device_result:
                for record in table.records:
                    device_id = record.values.get("device_id")
                    if device_id:
                        devices.append(device_id)
            
            # 필드 확인
            field_query = f'''
            from(bucket: "{settings.INFLUX_BUCKET}")
              |> range(start: -30d)
              |> filter(fn: (r) => r["_measurement"] == "{measurement_name}")
              |> group(columns: ["_field"])
              |> distinct(column: "_field")
              |> keep(columns: ["_field"])
            '''
            
            field_result = influx_manager.query_api.query(query=field_query, org=settings.INFLUX_ORG)
            
            fields = []
            for table in field_result:
                for record in table.records:
                    field = record.get_field()
                    if field:
                        fields.append(field)
            
            # 시간 범위 확인
            time_query = f'''
            from(bucket: "{settings.INFLUX_BUCKET}")
              |> range(start: -30d)
              |> filter(fn: (r) => r["_measurement"] == "{measurement_name}")
              |> group()
              |> first()
            '''
            
            time_result = influx_manager.query_api.query(query=time_query, org=settings.INFLUX_ORG)
            
            earliest_time = None
            for table in time_result:
                for record in table.records:
                    earliest_time = record.get_time()
                    break
            
            return {
                "count": total_count,
                "devices": devices,
                "fields": fields,
                "earliest": earliest_time
            }
        
        return None
        
    except Exception as e:
        print(f"❌ {measurement_name} 조회 실패: {e}")
        return None


def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("실제 센서 데이터가 있는 Measurement 확인")
    print("=" * 60 + "\n")
    
    measurements = [
        "sensor_data",
        "moby_sensors",
        "moby__sensors",
        "moby",
        "sensor_raw",
        "sensor_reading"
    ]
    
    results = {}
    
    for measurement in measurements:
        print(f"📊 {measurement} 확인 중...")
        data = check_measurement_data(measurement)
        
        if data:
            results[measurement] = data
            print(f"   ✅ {data['count']:,}개 포인트")
            print(f"   📱 디바이스: {len(data['devices'])}개 - {', '.join(data['devices'][:5])}")
            print(f"   📈 필드: {len(data['fields'])}개")
            if data['earliest']:
                print(f"   ⏰ 최초 데이터: {data['earliest']}")
        else:
            print(f"   ⚠️ 데이터 없음")
        print()
    
    # 요약
    print("=" * 60)
    print("요약")
    print("=" * 60)
    
    if results:
        print("✅ 데이터가 있는 Measurement:")
        for measurement, data in sorted(results.items(), key=lambda x: x[1]['count'], reverse=True):
            print(f"   - {measurement}: {data['count']:,}개 포인트, {len(data['devices'])}개 디바이스")
        
        # 가장 많은 데이터가 있는 measurement
        best = max(results.items(), key=lambda x: x[1]['count'])
        print(f"\n📊 가장 많은 데이터: {best[0]} ({best[1]['count']:,}개 포인트)")
        print(f"   디바이스: {', '.join(best[1]['devices'])}")
        print(f"   주요 필드: {', '.join([f for f in best[1]['fields'] if f in ['temperature', 'humidity', 'vibration', 'sound']][:10])}")
    else:
        print("⚠️ 데이터가 있는 Measurement가 없습니다.")
    
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

