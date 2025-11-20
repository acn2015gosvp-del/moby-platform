"""
Gemini API 키 유효성 검증 스크립트

.env 파일에서 GEMINI_API_KEY를 로드하고 실제 Gemini API에 연결을 시도합니다.
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import google.generativeai as genai
except ImportError:
    print("❌ google-generativeai 패키지가 설치되지 않았습니다.")
    print("   pip install google-generativeai를 실행하세요.")
    sys.exit(1)

# .env 파일 로드
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

# 설정에서 API 키 가져오기
try:
    from backend.api.services.schemas.models.core.config import settings
    api_key = settings.GEMINI_API_KEY
    print(f"✅ 설정에서 API 키 로드: {api_key[:10]}...{api_key[-10:]} (길이: {len(api_key)})")
except Exception as e:
    print(f"⚠️  설정에서 로드 실패: {e}")
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        print(f"✅ 환경 변수에서 API 키 로드: {api_key[:10]}...{api_key[-10:]} (길이: {len(api_key)})")
    else:
        print("❌ GEMINI_API_KEY를 찾을 수 없습니다.")
        sys.exit(1)

if not api_key or len(api_key) < 20:
    print(f"❌ API 키가 너무 짧습니다 (길이: {len(api_key) if api_key else 0})")
    sys.exit(1)

# Gemini API 설정
print("\n" + "="*60)
print("Gemini API 연결 테스트 시작")
print("="*60)

try:
    genai.configure(api_key=api_key)
    print("✅ genai.configure() 성공")
except Exception as e:
    print(f"❌ genai.configure() 실패: {e}")
    sys.exit(1)

# 사용 가능한 모델 목록 조회
print("\n📋 사용 가능한 모델 목록 조회 중...")
try:
    models = genai.list_models()
    gemini_models = [
        m.name for m in models 
        if 'generateContent' in m.supported_generation_methods
        and 'gemini' in m.name.lower()
    ]
    print(f"✅ {len(gemini_models)}개의 Gemini 모델 발견:")
    for model in gemini_models[:5]:  # 처음 5개만 표시
        print(f"   - {model}")
    if len(gemini_models) > 5:
        print(f"   ... 외 {len(gemini_models) - 5}개")
except Exception as e:
    print(f"❌ 모델 목록 조회 실패: {e}")
    error_str = str(e)
    if "API key not valid" in error_str or "API_KEY_INVALID" in error_str:
        print("\n" + "="*60)
        print("❌ API 키가 유효하지 않습니다!")
        print("="*60)
        print("\n해결 방법:")
        print("1. Google AI Studio에서 새 API 키 발급:")
        print("   https://makersuite.google.com/app/apikey")
        print("2. .env 파일에 올바른 API 키 설정:")
        print("   GEMINI_API_KEY=실제_API_키_값")
        print("3. API 키가 활성화되어 있는지 확인")
        print("4. API 키에 Generative Language API 권한이 있는지 확인")
    sys.exit(1)

# 간단한 생성 테스트
print("\n🧪 간단한 생성 테스트 중...")
test_models = [
    'gemini-2.5-flash',
    'models/gemini-2.5-flash',
    'models/gemini-1.5-flash',
    'gemini-1.5-flash',
]

success_model = None
for model_name in test_models:
    try:
        print(f"   시도 중: {model_name}...", end=" ")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello")
        if response and response.text:
            print("✅ 성공!")
            success_model = model_name
            print(f"   응답: {response.text[:50]}...")
            break
        else:
            print("❌ 빈 응답")
    except Exception as e:
        error_str = str(e)
        if "API key not valid" in error_str or "API_KEY_INVALID" in error_str:
            print("❌ API 키 오류")
            print("\n" + "="*60)
            print("❌ API 키가 유효하지 않습니다!")
            print("="*60)
            print(f"\n오류: {error_str}")
            print("\n해결 방법:")
            print("1. Google AI Studio에서 새 API 키 발급:")
            print("   https://makersuite.google.com/app/apikey")
            print("2. .env 파일에 올바른 API 키 설정")
            print("3. API 키가 활성화되어 있는지 확인")
            sys.exit(1)
        else:
            print(f"❌ 실패: {error_str[:50]}")

if success_model:
    print("\n" + "="*60)
    print("✅ Gemini API 연결 성공!")
    print("="*60)
    print(f"✅ 작동하는 모델: {success_model}")
    print("\n보고서 생성 기능을 사용할 수 있습니다.")
else:
    print("\n" + "="*60)
    print("⚠️  테스트 모델 중 작동하는 모델을 찾지 못했습니다.")
    print("="*60)
    print("하지만 모델 목록 조회는 성공했으므로, 다른 모델을 시도해보세요.")

