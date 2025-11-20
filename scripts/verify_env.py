#!/usr/bin/env python3
"""
.env 파일의 중요한 환경 변수 검증 스크립트

사용법:
    python scripts/verify_env.py

중요 환경 변수:
    - GEMINI_API_KEY
    - INFLUX_TOKEN
    - GRAFANA_API_KEY
    - SECRET_KEY
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.api.services.schemas.models.core.config import settings

def check_sensitive_key(key_name: str, value: str, min_length: int = 20) -> tuple[bool, str]:
    """
    중요한 환경 변수 검증
    
    Returns:
        (is_valid, message)
    """
    if not value:
        return False, f"❌ 설정되지 않음"
    
    # 예시 값 체크
    example_values = [
        f"your-{key_name.lower().replace('_', '-')}-here",
        f"your_{key_name.lower()}_here",
        "your-api-key-here",
        "your-secret-key-here",
        "실제_API_키_값",
    ]
    
    if value in example_values or any(example in value.lower() for example in ["example", "your-", "your_", "실제_"]):
        return False, f"❌ 예시 값 사용 중 (실제 값으로 변경 필요)"
    
    if len(value) < min_length:
        return False, f"⚠️  길이가 짧음 ({len(value)}자, 최소 {min_length}자 권장)"
    
    return True, f"✅ 설정됨 (길이: {len(value)}자)"

print("=" * 60)
print(".env 파일 환경 변수 검증")
print("=" * 60)
print()

issues = []
warnings = []

# 1. GEMINI_API_KEY 확인
print("1. GEMINI_API_KEY:")
is_valid, message = check_sensitive_key("GEMINI_API_KEY", settings.GEMINI_API_KEY, min_length=20)
print(f"   {message}")
if not is_valid:
    issues.append("GEMINI_API_KEY가 올바르게 설정되지 않았습니다.")
else:
    print(f"      앞 10자: {settings.GEMINI_API_KEY[:10]}...")
    print(f"      뒤 10자: ...{settings.GEMINI_API_KEY[-10:]}")
print()

# 2. INFLUX_TOKEN 확인
print("2. INFLUX_TOKEN:")
is_valid, message = check_sensitive_key("INFLUX_TOKEN", settings.INFLUX_TOKEN, min_length=20)
print(f"   {message}")
if not is_valid:
    issues.append("INFLUX_TOKEN이 올바르게 설정되지 않았습니다.")
print()

# 3. GRAFANA_API_KEY 확인 (선택사항)
print("3. GRAFANA_API_KEY (선택사항):")
if settings.GRAFANA_API_KEY:
    is_valid, message = check_sensitive_key("GRAFANA_API_KEY", settings.GRAFANA_API_KEY, min_length=20)
    print(f"   {message}")
    if not is_valid:
        warnings.append("GRAFANA_API_KEY가 올바르게 설정되지 않았습니다. (선택사항)")
else:
    print("   ⚠️  설정되지 않음 (선택사항)")
print()

# 4. SECRET_KEY 확인
print("4. SECRET_KEY:")
is_valid, message = check_sensitive_key("SECRET_KEY", settings.SECRET_KEY, min_length=32)
print(f"   {message}")
if not is_valid:
    if "예시" in message or "your-" in settings.SECRET_KEY.lower():
        issues.append("SECRET_KEY가 예시 값입니다. 프로덕션 환경에서는 반드시 변경하세요.")
    else:
        warnings.append("SECRET_KEY가 너무 짧습니다. 프로덕션 환경에서는 최소 32자 이상 권장합니다.")
print()

# 5. InfluxDB 설정 확인
print("5. InfluxDB 설정:")
print(f"   URL: {settings.INFLUX_URL}")
print(f"   Org: {settings.INFLUX_ORG}")
print(f"   Bucket: {settings.INFLUX_BUCKET}")
if not settings.INFLUX_URL or "[YOUR_REGION]" in settings.INFLUX_URL:
    warnings.append("INFLUX_URL이 예시 값입니다.")
if not settings.INFLUX_ORG or "your_organization" in settings.INFLUX_ORG.lower():
    warnings.append("INFLUX_ORG가 예시 값입니다.")
if not settings.INFLUX_BUCKET or "your_bucket" in settings.INFLUX_BUCKET.lower():
    warnings.append("INFLUX_BUCKET이 예시 값입니다.")
print()

# 6. 백업 파일 확인
print("6. 백업 파일 확인:")
env_file = Path(".env")
backup_files = sorted(env_file.parent.glob(".env.backup.*"), reverse=True)
if backup_files:
    print(f"   ✅ 백업 파일 {len(backup_files)}개 발견")
    print(f"      최신 백업: {backup_files[0].name}")
    if len(backup_files) > 3:
        print(f"      ⚠️  백업 파일이 많습니다 ({len(backup_files)}개). 정리 권장")
else:
    print("   ℹ️  백업 파일 없음 (정상)")
print()

# 요약
print("=" * 60)
if issues:
    print("❌ 발견된 문제 (수정 필요):")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")
    print()

if warnings:
    print("⚠️  경고 (확인 권장):")
    for i, warning in enumerate(warnings, 1):
        print(f"   {i}. {warning}")
    print()

if not issues and not warnings:
    print("✅ 모든 환경 변수가 정상적으로 설정되었습니다.")
else:
    if issues:
        print("해결 방법:")
        print("   1. .env 파일을 VS Code로 열어서 직접 편집 (UTF-8 인코딩)")
        print("   2. python scripts/edit_env.py set KEY_NAME 'value' 사용")
        print("   3. 절대 API 키를 채팅에 붙여넣지 마세요!")
        print()
        sys.exit(1)
    else:
        print("⚠️  경고만 있습니다. 계속 진행 가능하지만 확인을 권장합니다.")
        sys.exit(0)

print("=" * 60)

