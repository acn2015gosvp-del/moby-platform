"""
InfluxDB 데이터 저장 상태 확인 스크립트

InfluxDB에 데이터가 저장되고 있는지 확인합니다.
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

def check_influxdb_connection():
    """InfluxDB 연결 상태 확인"""
    print("=" * 60)
    print("InfluxDB 연결 상태 확인")
    print("=" * 60)
    
    try:
        # 클라이언트 연결 테스트
        health = influx_manager.client.health()
        print(f"✅ InfluxDB 연결 성공")
        print(f"   URL: {settings.INFLUX_URL}")
        print(f"   Organization: {settings.INFLUX_ORG}")
        print(f"   Bucket: {settings.INFLUX_BUCKET}")
        print(f"   Status: {health.status if hasattr(health, 'status') else 'OK'}")
        return True
    except Exception as e:
        print(f"❌ InfluxDB 연결 실패: {e}")
        print(f"   URL: {settings.INFLUX_URL}")
        print(f"   Organization: {settings.INFLUX_ORG}")
        print(f"   Bucket: {settings.INFLUX_BUCKET}")
        return False

def query_recent_data(minutes: int = 60):
    """최근 N분간의 데이터 조회"""
    print("\n" + "=" * 60)
    print(f"최근 {minutes}분간의 데이터 조회")
    print("=" * 60)
    
    try:
        query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: -{minutes}m)
          |> filter(fn: (r) => r["_measurement"] == "sensor_data")
          |> filter(fn: (r) => r["_field"] == "temperature" or r["_field"] == "humidity" or r["_field"] == "vibration" or r["_field"] == "sound")
          |> group(columns: ["device_id", "_field"])
          |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
          |> yield(name: "mean")
        '''
        
        result = influx_manager.query_api.query(query=query, org=settings.INFLUX_ORG)
        
        # 결과 파싱
        data_by_device = {}
        total_records = 0
        
        for table in result:
            for record in table.records:
                device_id = record.values.get("device_id", "unknown")
                field = record.get_field()
                value = record.get_value()
                time = record.get_time()
                
                if device_id not in data_by_device:
                    data_by_device[device_id] = {}
                
                if field not in data_by_device[device_id]:
                    data_by_device[device_id][field] = []
                
                data_by_device[device_id][field].append({
                    "value": value,
                    "time": time
                })
                total_records += 1
        
        if total_records == 0:
            print(f"⚠️ 최근 {minutes}분간 저장된 데이터가 없습니다.")
            print("   가능한 원인:")
            print("   1. MQTT 브로커에 센서 데이터가 전송되지 않음")
            print("   2. MQTT 클라이언트가 연결되지 않음")
            print("   3. 데이터가 버퍼에만 있고 아직 플러시되지 않음")
            print("\n   버퍼를 수동으로 플러시합니다...")
            influx_manager.flush()
            print("   플러시 완료. 잠시 후 다시 확인해주세요.")
        else:
            print(f"✅ 총 {total_records}개의 레코드를 찾았습니다.\n")
            
            for device_id, fields in data_by_device.items():
                print(f"📊 Device: {device_id}")
                for field, values in fields.items():
                    if values:
                        latest = values[-1]
                        avg_value = sum(v["value"] for v in values if v["value"] is not None) / len(values)
                        print(f"   {field:15s}: 최신값={latest['value']:.2f}, 평균={avg_value:.2f}, 레코드 수={len(values)}")
                print()
        
        return total_records > 0
        
    except Exception as e:
        print(f"❌ 데이터 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def query_device_list():
    """저장된 디바이스 목록 조회"""
    print("\n" + "=" * 60)
    print("저장된 디바이스 목록 조회")
    print("=" * 60)
    
    try:
        query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: -24h)
          |> filter(fn: (r) => r["_measurement"] == "sensor_data")
          |> distinct(column: "device_id")
          |> keep(columns: ["device_id"])
        '''
        
        result = influx_manager.query_api.query(query=query, org=settings.INFLUX_ORG)
        
        devices = set()
        for table in result:
            for record in table.records:
                device_id = record.values.get("device_id")
                if device_id:
                    devices.add(device_id)
        
        if devices:
            print(f"✅ 총 {len(devices)}개의 디바이스가 발견되었습니다:")
            for device_id in sorted(devices):
                print(f"   - {device_id}")
        else:
            print("⚠️ 저장된 디바이스가 없습니다.")
        
        return list(devices)
        
    except Exception as e:
        print(f"❌ 디바이스 목록 조회 실패: {e}")
        return []

def check_buffer_status():
    """버퍼 상태 확인"""
    print("\n" + "=" * 60)
    print("InfluxDB 버퍼 상태 확인")
    print("=" * 60)
    
    try:
        buffer_size = len(influx_manager.buffer)
        print(f"📦 현재 버퍼 크기: {buffer_size}/{influx_manager.buffer_size}")
        
        if buffer_size > 0:
            print(f"⚠️ 버퍼에 {buffer_size}개의 포인트가 대기 중입니다.")
            print("   버퍼를 플러시합니다...")
            influx_manager.flush()
            print("   ✅ 플러시 완료")
        else:
            print("✅ 버퍼가 비어있습니다 (모든 데이터가 저장됨)")
        
        return buffer_size
        
    except Exception as e:
        print(f"❌ 버퍼 상태 확인 실패: {e}")
        return 0

def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("InfluxDB 데이터 저장 상태 확인")
    print("=" * 60)
    print()
    
    # 1. 연결 상태 확인
    if not check_influxdb_connection():
        print("\n❌ InfluxDB에 연결할 수 없습니다. 설정을 확인해주세요.")
        return
    
    # 2. 버퍼 상태 확인
    buffer_size = check_buffer_status()
    
    # 3. 디바이스 목록 조회
    devices = query_device_list()
    
    # 4. 최근 데이터 조회 (1시간)
    has_data_1h = query_recent_data(minutes=60)
    
    # 5. 최근 데이터 조회 (24시간)
    if not has_data_1h:
        print("\n" + "=" * 60)
        print("최근 24시간 데이터 확인")
        print("=" * 60)
        query_recent_data(minutes=1440)
    
    # 요약
    print("\n" + "=" * 60)
    print("요약")
    print("=" * 60)
    print(f"✅ InfluxDB 연결: 성공")
    print(f"📦 버퍼 상태: {buffer_size}개 대기 중")
    print(f"📊 발견된 디바이스: {len(devices)}개")
    print(f"💾 최근 1시간 데이터: {'있음' if has_data_1h else '없음'}")
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

