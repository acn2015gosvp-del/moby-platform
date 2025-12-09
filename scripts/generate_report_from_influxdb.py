"""
InfluxDB 클라우드에서 센서 데이터를 가져와서 보고서 생성
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timezone, timedelta
from backend.api.services.report_service import get_report_service
from backend.api.services.database import get_db, init_db
from backend.api.services.report_generator import get_report_generator


def generate_report():
    """InfluxDB에서 데이터를 가져와 보고서 생성"""
    print("=" * 60)
    print("InfluxDB 클라우드 데이터로 보고서 생성")
    print("=" * 60)
    
    init_db()
    
    # 이전에 확인한 실제 Host ID 사용
    host_id = "44d5516Z"  # 실제 데이터가 있는 Host ID
    
    # 최근 7일 데이터로 보고서 생성
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=7)
    
    print(f"\n📅 보고서 기간:")
    print(f"   시작: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"   종료: {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"   Host ID: {host_id}")
    print()
    
    service = get_report_service()
    db = next(get_db())
    
    try:
        print("📊 InfluxDB에서 센서 데이터 수집 중...")
        report_data = service.fetch_report_data(
            start_time=start_time,
            end_time=end_time,
            equipment_id=host_id,
            db=db
        )
        
        print("✅ 데이터 수집 완료")
        print()
        
        # 수집된 데이터 요약
        sensor_stats = report_data.get("sensor_stats", {})
        print(f"📈 센서 통계: {len(sensor_stats)}개 센서")
        for sensor_name, stats in sensor_stats.items():
            if isinstance(stats, dict):
                if "mean" in stats:
                    print(f"   - {sensor_name}: 평균={stats.get('mean', 0):.2f}, 최대={stats.get('max', 0):.2f}")
                elif isinstance(stats, dict) and len(stats) > 0:
                    print(f"   - {sensor_name}: {len(stats)}개 항목")
        
        print(f"⚠️ 알람: {len(report_data.get('alarms', []))}개")
        print(f"🔍 MLP 이상: {len(report_data.get('mlp_anomalies', []))}개")
        print(f"🔍 IF 이상: {len(report_data.get('if_anomalies', []))}개")
        print()
        
        # 보고서 생성
        print("📝 LLM으로 보고서 생성 중...")
        generator = get_report_generator()
        
        report_result = generator.generate_report(report_data)
        
        # report_result가 문자열인 경우와 딕셔너리인 경우 모두 처리
        if isinstance(report_result, str):
            report_text = report_result
        elif report_result and "report" in report_result:
            report_text = report_result["report"]
        elif report_result:
            report_text = str(report_result)
        else:
            report_text = None
        
        if report_text:
            print("✅ 보고서 생성 완료!")
            print()
            print("=" * 60)
            print("생성된 보고서 (일부)")
            print("=" * 60)
            print(report_text[:2000])  # 처음 2000자만 출력
            if len(report_text) > 2000:
                print(f"\n... (총 {len(report_text)}자, 나머지 생략)")
            print()
            print("=" * 60)
            
            # PDF로 보고서 저장
            from backend.api.services.pdf_generator import markdown_to_pdf
            
            output_file = Path("reports") / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_file.parent.mkdir(exist_ok=True)
            
            metadata = {
                "보고 기간": f"{start_time.strftime('%Y-%m-%d %H:%M:%S UTC')} ~ {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                "설비 ID": host_id,
                "생성 시각": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            }
            
            success = markdown_to_pdf(
                markdown_text=report_text,
                output_path=output_file,
                title="MOBY 설비 상태 보고서",
                metadata=metadata
            )
            
            if success:
                print(f"💾 PDF 보고서가 저장되었습니다: {output_file}")
                print(f"   파일 크기: {output_file.stat().st_size / 1024:.2f} KB")
            else:
                # PDF 생성 실패 시 텍스트 파일로 대체 저장
                txt_file = output_file.with_suffix('.txt')
                with open(txt_file, "w", encoding="utf-8") as f:
                    f.write("=" * 60 + "\n")
                    f.write("MOBY 설비 상태 보고서\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(f"보고 기간: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')} ~ {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
                    f.write(f"설비 ID: {host_id}\n")
                    f.write(f"생성 시각: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(report_text)
                print(f"⚠️ PDF 생성 실패. 텍스트 파일로 저장되었습니다: {txt_file}")
                print("   PDF 생성을 위해 다음 라이브러리를 설치하세요:")
                print("   pip install markdown weasyprint")
            print()
        else:
            print("❌ 보고서 생성 실패")
            if report_result:
                print(f"   결과 타입: {type(report_result)}")
                print(f"   결과 내용 (처음 500자): {str(report_result)[:500]}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    generate_report()

