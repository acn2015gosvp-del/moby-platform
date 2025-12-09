"""
InfluxDB 전체 데이터 확인 스크립트

모든 기간의 데이터를 확인하여 실제로 센서 데이터가 저장되어 있는지 확인합니다.
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


def check_all_measurements():
    """모든 measurement 확인"""
    print("=" * 60)
    print("InfluxDB Measurement 확인")
    print("=" * 60)
    
    try:
        # 모든 measurement 조회
        query = f'''
        import "influxdata/influxdb/schema"
        schema.measurements(bucket: "{settings.INFLUX_BUCKET}")
        '''
        
        result = influx_manager.query_api.query(query=query, org=settings.INFLUX_ORG)
        
        measurements = []
        for table in result:
            for record in table.records:
                measurement = record.get_value()
                if measurement:
                    measurements.append(measurement)
        
        if measurements:
            print(f"✅ 발견된 Measurement: {len(measurements)}개")
            for m in measurements:
                print(f"   - {m}")
        else:
            print("⚠️ Measurement가 없습니다.")
        
        print()
        return measurements
        
    except Exception as e:
        print(f"❌ Measurement 조회 실패: {e}")
        print()
        return []


def check_all_fields():
    """모든 필드 확인"""
    print("=" * 60)
    print("InfluxDB Field 확인")
    print("=" * 60)
    
    try:
        # 모든 필드 조회
        query = f'''
        import "influxdata/influxdb/schema"
        schema.fieldKeys(bucket: "{settings.INFLUX_BUCKET}")
        '''
        
        result = influx_manager.query_api.query(query=query, org=settings.INFLUX_ORG)
        
        fields = []
        for table in result:
            for record in table.records:
                field = record.get_value()
                if field:
                    fields.append(field)
        
        if fields:
            print(f"✅ 발견된 Field: {len(fields)}개")
            for f in fields:
                print(f"   - {f}")
        else:
            print("⚠️ Field가 없습니다.")
        
        print()
        return fields
        
    except Exception as e:
        print(f"❌ Field 조회 실패: {e}")
        print()
        return []


def check_all_data_wide_range():
    """매우 넓은 범위로 데이터 확인 (최근 30일)"""
    print("=" * 60)
    print("최근 30일 데이터 확인")
    print("=" * 60)
    
    try:
        query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: -30d)
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
            print(f"✅ 최근 30일간 총 {total_count}개의 데이터 포인트 발견")
        else:
            print("⚠️ 최근 30일간 데이터가 없습니다.")
        
        print()
        return total_count > 0
        
    except Exception as e:
        print(f"❌ 데이터 조회 실패: {e}")
        print()
        return False


def check_sensor_data_all_time():
    """sensor_data measurement의 모든 데이터 확인"""
    print("=" * 60)
    print("sensor_data Measurement 전체 데이터 확인")
    print("=" * 60)
    
    try:
        # 모든 시간 범위에서 sensor_data 확인
        query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: -365d)
          |> filter(fn: (r) => r["_measurement"] == "sensor_data")
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
            print(f"✅ sensor_data에서 총 {total_count}개의 데이터 포인트 발견")
            
            # 디바이스별로 확인
            device_query = f'''
            from(bucket: "{settings.INFLUX_BUCKET}")
              |> range(start: -365d)
              |> filter(fn: (r) => r["_measurement"] == "sensor_data")
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
            
            if devices:
                print(f"✅ 발견된 디바이스: {len(devices)}개")
                for device_id in devices:
                    print(f"   - {device_id}")
            
            # 시간 범위 확인
            time_query = f'''
            from(bucket: "{settings.INFLUX_BUCKET}")
              |> range(start: -365d)
              |> filter(fn: (r) => r["_measurement"] == "sensor_data")
              |> group()
              |> first()
            '''
            
            time_result = influx_manager.query_api.query(query=time_query, org=settings.INFLUX_ORG)
            
            earliest_time = None
            for table in time_result:
                for record in table.records:
                    earliest_time = record.get_time()
                    break
            
            if earliest_time:
                print(f"✅ 가장 오래된 데이터: {earliest_time}")
            
        else:
            print("⚠️ sensor_data measurement에 데이터가 없습니다.")
            print("   가능한 원인:")
            print("   1. 센서 데이터가 아직 저장되지 않음")
            print("   2. 다른 measurement 이름 사용")
            print("   3. 다른 bucket 사용")
        
        print()
        return total_count > 0
        
    except Exception as e:
        print(f"❌ sensor_data 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def check_bucket_info():
    """Bucket 정보 확인"""
    print("=" * 60)
    print("Bucket 정보 확인")
    print("=" * 60)
    
    try:
        print(f"Bucket: {settings.INFLUX_BUCKET}")
        print(f"Organization: {settings.INFLUX_ORG}")
        print(f"URL: {settings.INFLUX_URL}")
        print()
        
        # Bucket 존재 확인
        try:
            buckets_api = influx_manager.client.buckets_api()
            buckets = buckets_api.find_buckets()
            
            bucket_names = [b.name for b in buckets.buckets if b]
            print(f"✅ 접근 가능한 Bucket: {len(bucket_names)}개")
            for name in bucket_names:
                marker = " ← 현재 사용 중" if name == settings.INFLUX_BUCKET else ""
                print(f"   - {name}{marker}")
            
        except Exception as e:
            print(f"⚠️ Bucket 목록 조회 실패: {e}")
        
        print()
        
    except Exception as e:
        print(f"❌ Bucket 정보 확인 실패: {e}")
        print()


def main():
    """메인 실행 함수"""
    print("\n" + "=" * 60)
    print("InfluxDB 전체 데이터 확인")
    print("=" * 60 + "\n")
    
    # 1. Bucket 정보 확인
    check_bucket_info()
    
    # 2. 모든 Measurement 확인
    measurements = check_all_measurements()
    
    # 3. 모든 Field 확인
    fields = check_all_fields()
    
    # 4. 넓은 범위 데이터 확인
    has_data_30d = check_all_data_wide_range()
    
    # 5. sensor_data 확인
    has_sensor_data = check_sensor_data_all_time()
    
    # 요약
    print("=" * 60)
    print("요약")
    print("=" * 60)
    print(f"📊 Measurement: {len(measurements)}개")
    print(f"📊 Field: {len(fields)}개")
    print(f"💾 최근 30일 데이터: {'있음' if has_data_30d else '없음'}")
    print(f"📡 sensor_data: {'있음' if has_sensor_data else '없음'}")
    print()
    
    if not has_sensor_data:
        print("⚠️ 센서 데이터가 InfluxDB에 저장되지 않았습니다.")
        print("   다음을 확인하세요:")
        print("   1. MQTT 브로커가 실행 중인지")
        print("   2. 센서 데이터가 MQTT로 전송되는지")
        print("   3. MQTT 클라이언트가 데이터를 수신하는지")
        print("   4. InfluxDB 쓰기가 정상 작동하는지")
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

