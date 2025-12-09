"""
실제 프론트엔드 요청과 동일한 형식으로 테스트
"""

import sys
from pathlib import Path
import requests
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_actual_request():
    """프론트엔드에서 보내는 실제 요청 형식으로 테스트"""
    print("=" * 60)
    print("실제 프론트엔드 요청 형식 테스트")
    print("=" * 60)
    
    # 프론트엔드에서 보내는 실제 요청 데이터 (콘솔 로그 기반)
    request_data = {
        "period_start": "2025-12-01 04:20:00",
        "period_end": "2025-12-08 04:20:00",
        "equipment": "컨베이어 벨트 #1",  # 한글 설비명
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
            timeout=300,
            headers={
                "Content-Type": "application/json",
                # 인증 토큰이 필요할 수 있음
            }
        )
        
        print(f"📥 응답 상태 코드: {response.status_code}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 성공!")
            print(f"   응답 구조: {list(result.keys())}")
        else:
            print("❌ 실패!")
            print(f"   응답 본문: {response.text[:2000]}")
            try:
                error_data = response.json()
                print(f"   에러 상세: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"   원본 응답: {response.text}")
        
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. FastAPI 서버가 실행 중인지 확인하세요.")
    except requests.exceptions.Timeout:
        print("❌ 요청 시간 초과 (300초)")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_actual_request()

