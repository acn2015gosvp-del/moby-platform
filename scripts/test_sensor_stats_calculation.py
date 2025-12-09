"""
센서 통계 계산 테스트
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timezone, timedelta
from backend.api.services.report_service import get_report_service
from backend.api.services.database import get_db, init_db


def test_sensor_stats():
    """센서 통계 계산 테스트"""
    print("=" * 60)
    print("센서 통계 계산 테스트")
    print("=" * 60)
    
    init_db()
    
    # 실제 Host ID 사용
    host_id = "44d5516Z"
    
    # 최근 7일 데이터로 테스트
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=7)
    
    print(f"\n📅 테스트 기간:")
    print(f"   시작: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"   종료: {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"   Host ID: {host_id}")
    print()
    
    service = get_report_service()
    db = next(get_db())
    
    try:
        print("📊 센서 통계 계산 중...")
        sensor_stats = service._fetch_sensor_stats(
            start_time=start_time,
            end_time=end_time,
            equipment_id=host_id,
            sensor_ids=None
        )
        
        print("✅ 센서 통계 계산 완료")
        print()
        print("=" * 60)
        print("계산된 센서 통계")
        print("=" * 60)
        
        for sensor_name, stats in sensor_stats.items():
            print(f"\n📈 {sensor_name}:")
            if isinstance(stats, dict):
                if "mean" in stats:
                    # Temperature/Humidity/Sound 형식
                    print(f"   Mean: {stats.get('mean', 0):.2f}")
                    print(f"   Min: {stats.get('min', 0):.2f}")
                    print(f"   Max: {stats.get('max', 0):.2f}")
                    print(f"   Std: {stats.get('std', 0):.2f}")
                    print(f"   P95: {stats.get('p95', 0):.2f}")
                elif "x" in stats or "y" in stats or "z" in stats:
                    # Vibration 형식
                    for axis in ["x", "y", "z"]:
                        if axis in stats:
                            axis_data = stats[axis]
                            print(f"   {axis.upper()}축:")
                            print(f"      Mean: {axis_data.get('mean', 0):.2f}")
                            print(f"      Peak: {axis_data.get('peak', 0):.2f}")
                            print(f"      RMS: {axis_data.get('rms', 0):.2f}")
        
        print()
        print("=" * 60)
        print("전체 보고서 데이터 조회 테스트")
        print("=" * 60)
        
        report_data = service.fetch_report_data(
            start_time=start_time,
            end_time=end_time,
            equipment_id=host_id,
            db=db
        )
        
        print(f"✅ 보고서 데이터 수집 완료")
        print(f"   센서 통계: {len(report_data.get('sensor_stats', {}))}개")
        print(f"   알람: {len(report_data.get('alarms', []))}개")
        print(f"   MLP 이상: {len(report_data.get('mlp_anomalies', []))}개")
        print(f"   IF 이상: {len(report_data.get('if_anomalies', []))}개")
        
        # 센서 통계 상세 출력
        sensor_stats_detail = report_data.get('sensor_stats', {})
        print(f"\n📊 센서 통계 상세:")
        import json
        print(json.dumps(sensor_stats_detail, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_sensor_stats()

