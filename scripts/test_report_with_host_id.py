"""
실제 host ID로 보고서 생성 테스트
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timezone, timedelta
from backend.api.services.report_service import get_report_service
from backend.api.services.database import get_db, init_db


def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("실제 host ID로 보고서 생성 테스트")
    print("=" * 60 + "\n")
    
    init_db()
    
    # 실제 host ID 사용 (moby_sensors에서 발견된 ID)
    host_ids = ["44d5516Z", "44d55a9764d9", "816f3194658a", "e41c9041b728", "f98ca03930d2"]
    
    # 최근 7일 데이터로 테스트
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=7)
    
    service = get_report_service()
    db = next(get_db())
    
    try:
        for host_id in host_ids[:2]:  # 처음 2개만 테스트
            print(f"\n{'='*60}")
            print(f"Host ID: {host_id} 테스트")
            print(f"{'='*60}\n")
            
            report_data = service.fetch_report_data(
                start_time=start_time,
                end_time=end_time,
                equipment_id=host_id,
                db=db
            )
            
            sensor_stats = report_data.get("sensor_stats", {})
            
            print(f"✅ 보고서 데이터 수집 완료")
            print(f"📈 센서 통계: {len(sensor_stats)}개 센서")
            
            for sensor_name, stats in sensor_stats.items():
                if isinstance(stats, dict):
                    if "mean" in stats:
                        print(f"   - {sensor_name}: 평균={stats.get('mean', 'N/A'):.2f}, 최대={stats.get('max', 'N/A'):.2f}")
                    elif isinstance(stats, dict) and len(stats) > 0:
                        print(f"   - {sensor_name}: {len(stats)}개 항목")
            
            print(f"⚠️ 알람: {len(report_data.get('alarms', []))}개")
            print()
            
    finally:
        db.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

