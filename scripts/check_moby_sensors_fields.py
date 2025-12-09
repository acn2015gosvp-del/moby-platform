"""
moby_sensors measurement의 실제 필드 확인
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.api.services.schemas.models.core.config import settings
from backend.api.services.influx_client import influx_manager


def check_moby_sensors_fields():
    """moby_sensors의 필드와 태그 확인"""
    print("=" * 60)
    print("moby_sensors Measurement 상세 확인")
    print("=" * 60)
    
    try:
        # 필드 확인
        query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: -7d)
          |> filter(fn: (r) => r["_measurement"] == "moby_sensors")
          |> group(columns: ["_field"])
          |> distinct(column: "_field")
          |> keep(columns: ["_field"])
          |> limit(n: 50)
        '''
        
        result = influx_manager.query_api.query(query=query, org=settings.INFLUX_ORG)
        
        fields = []
        for table in result:
            for record in table.records:
                field = record.get_field()
                if field:
                    fields.append(field)
        
        print(f"✅ 발견된 필드: {len(fields)}개")
        for field in sorted(fields):
            print(f"   - {field}")
        print()
        
        # 태그 확인
        tag_query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: -7d)
          |> filter(fn: (r) => r["_measurement"] == "moby_sensors")
          |> group()
          |> limit(n: 1)
        '''
        
        tag_result = influx_manager.query_api.query(query=tag_query, org=settings.INFLUX_ORG)
        
        tags = set()
        for table in tag_result:
            for record in table.records:
                for key, value in record.values.items():
                    if key not in ['_time', '_value', '_field', '_measurement', '_start', '_stop']:
                        tags.add(key)
        
        print(f"✅ 발견된 태그: {len(tags)}개")
        for tag in sorted(tags):
            print(f"   - {tag}")
        print()
        
        # 샘플 데이터 확인
        sample_query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: -7d)
          |> filter(fn: (r) => r["_measurement"] == "moby_sensors")
          |> limit(n: 5)
        '''
        
        sample_result = influx_manager.query_api.query(query=sample_query, org=settings.INFLUX_ORG)
        
        print("📊 샘플 데이터 (최근 5개):")
        for table in sample_result:
            for record in table.records:
                print(f"   시간: {record.get_time()}")
                print(f"   필드: {record.get_field()}")
                print(f"   값: {record.get_value()}")
                print(f"   태그: {dict((k, v) for k, v in record.values.items() if k not in ['_time', '_value', '_field', '_measurement', '_start', '_stop'])}")
                print()
        
        return fields, tags
        
    except Exception as e:
        print(f"❌ 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return [], []


if __name__ == "__main__":
    fields, tags = check_moby_sensors_fields()
    
    print("=" * 60)
    print("요약")
    print("=" * 60)
    print(f"필드 수: {len(fields)}")
    print(f"태그 수: {len(tags)}")
    
    # 온도/습도/진동/음압 관련 필드 찾기
    temp_fields = [f for f in fields if 'temp' in f.lower()]
    humidity_fields = [f for f in fields if 'humidity' in f.lower()]
    vibration_fields = [f for f in fields if 'vibration' in f.lower()]
    sound_fields = [f for f in fields if 'sound' in f.lower()]
    
    print(f"\n온도 관련 필드: {temp_fields}")
    print(f"습도 관련 필드: {humidity_fields}")
    print(f"진동 관련 필드: {vibration_fields}")
    print(f"음압 관련 필드: {sound_fields}")

