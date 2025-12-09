"""
실제 DB 데이터로 보고서 생성 테스트 스크립트

DB에 저장된 알람 데이터와 InfluxDB의 센서 데이터를 사용하여
보고서 생성 API를 테스트합니다.
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timezone, timedelta
from backend.api.services.report_service import get_report_service
from backend.api.services.schemas.models.core.config import settings
from backend.api.services.database import get_db, init_db
from backend.api.services.alert_storage import get_latest_alerts
from backend.api.services.influx_client import influx_manager


def check_database_alerts():
    """DB에 저장된 알람 데이터 확인"""
    print("=" * 60)
    print("DB 알람 데이터 확인")
    print("=" * 60)
    
    try:
        db = next(get_db())
        
        try:
            # 최근 알람 조회
            alerts = get_latest_alerts(db=db, limit=100)
            
            print(f"✅ 총 {len(alerts)}개의 알람이 발견되었습니다.\n")
            
            if len(alerts) == 0:
                print("⚠️ DB에 알람 데이터가 없습니다.")
                return None, None, []
            
            # 알람 시간 범위 확인
            alert_times = []
            device_ids = set()
            
            for alert in alerts:
                try:
                    alert_ts_str = alert.ts.replace('Z', '+00:00') if 'Z' in alert.ts else alert.ts
                    alert_ts = datetime.fromisoformat(alert_ts_str)
                    if alert_ts.tzinfo is None:
                        alert_ts = alert_ts.replace(tzinfo=timezone.utc)
                    alert_times.append(alert_ts)
                    device_ids.add(alert.sensor_id)
                except (ValueError, AttributeError):
                    continue
            
            if alert_times:
                earliest = min(alert_times)
                latest = max(alert_times)
                
                print(f"📅 알람 시간 범위:")
                print(f"   최초: {earliest.isoformat()}")
                print(f"   최신: {latest.isoformat()}")
                print(f"   기간: {(latest - earliest).total_seconds() / 3600:.1f}시간")
                print()
                
                print(f"📱 발견된 디바이스 ID:")
                for device_id in sorted(device_ids):
                    count = sum(1 for a in alerts if a.sensor_id == device_id)
                    print(f"   - {device_id}: {count}개 알람")
                print()
                
                return earliest, latest, list(device_ids)
            else:
                print("⚠️ 유효한 시간 정보가 있는 알람이 없습니다.")
                return None, None, []
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 알람 데이터 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return None, None, []


def check_influxdb_data(device_ids, start_time, end_time):
    """InfluxDB에 저장된 센서 데이터 확인"""
    print("=" * 60)
    print("InfluxDB 센서 데이터 확인")
    print("=" * 60)
    
    try:
        start_rfc3339 = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_rfc3339 = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # 디바이스 필터 구성
        if device_ids:
            device_filter = ' or '.join([f'r["device_id"] == "{did}"' for did in device_ids[:5]])  # 최대 5개만
            filter_clause = f'|> filter(fn: (r) => {device_filter})'
        else:
            filter_clause = ''
        
        query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: {start_rfc3339}, stop: {end_rfc3339})
          |> filter(fn: (r) => r["_measurement"] == "sensor_data")
          {filter_clause}
          |> group(columns: ["device_id", "_field"])
          |> count()
        '''
        
        result = influx_manager.query_api.query(query=query, org=settings.INFLUX_ORG)
        
        data_summary = {}
        total_count = 0
        
        for table in result:
            for record in table.records:
                device_id = record.values.get("device_id", "unknown")
                field = record.get_field()
                count = int(record.get_value())
                
                if device_id not in data_summary:
                    data_summary[device_id] = {}
                
                data_summary[device_id][field] = count
                total_count += count
        
        if total_count > 0:
            print(f"✅ 총 {total_count}개의 데이터 포인트를 찾았습니다.\n")
            
            for device_id, fields in sorted(data_summary.items()):
                print(f"📊 Device: {device_id}")
                for field, count in sorted(fields.items()):
                    print(f"   {field:15s}: {count}개 포인트")
                print()
            
            return True
        else:
            print(f"⚠️ 기간 내 InfluxDB 데이터가 없습니다.")
            print(f"   기간: {start_time.isoformat()} ~ {end_time.isoformat()}")
            return False
            
    except Exception as e:
        print(f"❌ InfluxDB 데이터 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_report_generation(equipment_id, start_time, end_time):
    """실제 데이터로 보고서 생성 테스트"""
    print("=" * 60)
    print("보고서 생성 테스트")
    print("=" * 60)
    
    try:
        # 보고서 서비스 초기화
        service = get_report_service()
        
        # 데이터베이스 세션 가져오기
        db = next(get_db())
        
        try:
            print(f"기간: {start_time.isoformat()} ~ {end_time.isoformat()}")
            print(f"설비 ID: {equipment_id}")
            print()
            
            print("📊 보고서 데이터 수집 중...")
            report_data = service.fetch_report_data(
                start_time=start_time,
                end_time=end_time,
                equipment_id=equipment_id,
                db=db
            )
            
            print("✅ 보고서 데이터 수집 완료\n")
            
            # 데이터 요약 출력
            print("=" * 60)
            print("수집된 데이터 요약")
            print("=" * 60)
            
            metadata = report_data.get("metadata", {})
            print(f"📅 보고 기간: {metadata.get('period_start')} ~ {metadata.get('period_end')}")
            print(f"🏭 설비: {metadata.get('equipment')}")
            print(f"⏰ 생성 시각: {metadata.get('generated_at')}")
            print()
            
            sensor_stats = report_data.get("sensor_stats", {})
            print(f"📈 센서 통계: {len(sensor_stats)}개 센서")
            for sensor_name, stats in sensor_stats.items():
                if isinstance(stats, dict):
                    if "mean" in stats:
                        print(f"   - {sensor_name}: 평균={stats.get('mean', 'N/A'):.2f}, 최대={stats.get('max', 'N/A'):.2f}")
                    elif isinstance(stats, dict) and len(stats) > 0:
                        print(f"   - {sensor_name}: {len(stats)}개 항목")
            print()
            
            alarms = report_data.get("alarms", [])
            print(f"⚠️ 알람: {len(alarms)}개")
            if alarms:
                for i, alarm in enumerate(alarms[:5], 1):  # 최대 5개만 표시
                    print(f"   {i}. {alarm.get('level', 'N/A')}: {alarm.get('message', 'N/A')[:50]}")
                if len(alarms) > 5:
                    print(f"   ... 외 {len(alarms) - 5}개")
            print()
            
            mlp_anomalies = report_data.get("mlp_anomalies", [])
            print(f"🔍 MLP 이상 탐지: {len(mlp_anomalies)}개")
            print()
            
            if_anomalies = report_data.get("if_anomalies", [])
            print(f"🔍 IF 이상 탐지: {len(if_anomalies)}개")
            print()
            
            correlations = report_data.get("correlations", {})
            print(f"🔗 상관계수: {len(correlations)}개")
            print()
            
            # 보고서 데이터 구조 검증
            print("=" * 60)
            print("데이터 구조 검증")
            print("=" * 60)
            
            required_keys = ["metadata", "sensor_stats", "alarms", "mlp_anomalies", "if_anomalies", "correlations"]
            all_present = all(key in report_data for key in required_keys)
            
            if all_present:
                print("✅ 모든 필수 데이터 구조가 존재합니다.")
            else:
                missing = [key for key in required_keys if key not in report_data]
                print(f"❌ 누락된 데이터 구조: {', '.join(missing)}")
            
            print()
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 보고서 생성 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 실행 함수"""
    print("\n" + "=" * 60)
    print("실제 DB 데이터로 보고서 생성 테스트")
    print("=" * 60 + "\n")
    
    # 1. DB 초기화
    try:
        init_db()
        print("✅ 데이터베이스 초기화 완료\n")
    except Exception as e:
        print(f"⚠️ 데이터베이스 초기화 경고: {e}\n")
    
    # 2. DB 알람 데이터 확인
    earliest, latest, device_ids = check_database_alerts()
    
    if not earliest or not latest:
        print("⚠️ DB에 알람 데이터가 없어 테스트를 진행할 수 없습니다.")
        print("   더미 데이터로 테스트하시겠습니까? (현재는 종료합니다)")
        return
    
    # 3. InfluxDB 데이터 확인
    print()
    has_influx_data = check_influxdb_data(device_ids, earliest, latest)
    
    # 4. 보고서 생성 테스트
    # 첫 번째 디바이스 ID 사용 (또는 test_equipment)
    equipment_id = device_ids[0] if device_ids else "test_equipment"
    
    # 기간을 약간 확장 (알람 시간 범위의 앞뒤로 1시간씩 추가)
    test_start = earliest - timedelta(hours=1)
    test_end = latest + timedelta(hours=1)
    
    print()
    success = test_report_generation(equipment_id, test_start, test_end)
    
    # 결과 요약
    print("=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    print(f"✅ DB 알람 데이터: {len(device_ids)}개 디바이스, {earliest} ~ {latest}")
    print(f"{'✅' if has_influx_data else '⚠️'} InfluxDB 센서 데이터: {'있음' if has_influx_data else '없음 (더미 데이터 사용)'}")
    print(f"{'✅' if success else '❌'} 보고서 생성 테스트: {'성공' if success else '실패'}")
    print()
    
    if success:
        print("✅ 모든 테스트를 통과했습니다!")
        print(f"\n다음 단계: 실제 API 엔드포인트로 보고서 생성 테스트")
        print(f"   POST /api/reports/generate")
        print(f"   기간: {test_start.isoformat()} ~ {test_end.isoformat()}")
        print(f"   설비: {equipment_id}")
    else:
        print("❌ 일부 테스트에 실패했습니다. 위의 오류 메시지를 확인하세요.")
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

