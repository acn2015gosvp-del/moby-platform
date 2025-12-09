"""
현재 사용 중인 Gemini 모델 확인 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / '.env')

try:
    from backend.api.services.report_generator import get_report_generator, reset_report_generator
    
    print("="*60)
    print("현재 사용 중인 Gemini 모델 확인")
    print("="*60)
    
    # 보고서 생성기 리셋 후 새로 가져오기
    reset_report_generator()
    generator = get_report_generator()
    
    if generator and generator.model_name:
        print(f"\n✅ 현재 사용 중인 모델: {generator.model_name}")
        print(f"   모델 타입: {type(generator.model)}")
        
        # 모델 설정 확인
        if hasattr(generator.model, 'model_name'):
            print(f"   실제 모델명: {generator.model.model_name}")
        
        # generation_config 확인
        if hasattr(generator.model, '_generation_config'):
            config = generator.model._generation_config
            print(f"   max_output_tokens: {config.get('max_output_tokens', 'N/A')}")
            print(f"   temperature: {config.get('temperature', 'N/A')}")
    else:
        print("\n❌ 보고서 생성기를 초기화할 수 없습니다.")
        print("   GEMINI_API_KEY를 확인하세요.")
        
except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()

