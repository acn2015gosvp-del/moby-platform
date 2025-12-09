"""
보고서 생성 API 직접 테스트
"""

import sys
from pathlib import Path
import requests
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_api():
    """API 직접 테스트"""
    print("=" * 60)
    print("보고서 생성 API 직접 테스트")
    print("=" * 60)
    
    # API 요청 데이터
    request_data = {
        "period_start": "2025-12-01 02:45:00",
        "period_end": "2025-12-08 02:45:00",
        "equipment": "Conveyor A-01",
        "include_mlp_anomalies": True,
        "include_if_anomalies": True
    }
    
    url = "http://localhost:8000/reports/generate"
    
    print(f"\n📡 API 요청:")
    print(f"   URL: {url}")
    print(f"   데이터: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    print()
    
    try:
        print("🔄 요청 전송 중...")
        response = requests.post(
            url,
            json=request_data,
            timeout=180,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📥 응답 상태 코드: {response.status_code}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 성공!")
            print(f"   응답 구조: {list(result.keys())}")
            if "data" in result:
                if "report_content" in result["data"]:
                    print(f"   보고서 길이: {len(result['data']['report_content'])}자")
                    print(f"   보고서 일부:")
                    print(result["data"]["report_content"][:500])
                else:
                    print(f"   data 내용: {list(result['data'].keys())}")
            else:
                print(f"   전체 응답: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
        else:
            print("❌ 실패!")
            print(f"   응답 본문: {response.text[:1000]}")
            try:
                error_data = response.json()
                print(f"   에러 상세: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"   원본 응답: {response.text}")
        
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. FastAPI 서버가 실행 중인지 확인하세요.")
    except requests.exceptions.Timeout:
        print("❌ 요청 시간 초과 (180초)")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_api()

