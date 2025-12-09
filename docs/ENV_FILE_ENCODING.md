# .env 파일 인코딩 가이드

## 문제점

Windows 환경에서 `.env` 파일을 편집할 때 인코딩 문제가 발생할 수 있습니다:
- PowerShell의 `Set-Content`가 기본적으로 UTF-16 또는 다른 인코딩으로 저장
- Windows 메모장이 기본적으로 ANSI 인코딩 사용
- 인코딩 불일치로 인한 `UnicodeDecodeError` 발생

## 해결 방법

### 1. 자동 인코딩 정규화 (권장)

백엔드 서버가 시작될 때 자동으로 `.env` 파일을 UTF-8 (BOM 없음)로 변환합니다.
`config.py`의 `_normalize_env_file_encoding()` 함수가 이를 처리합니다.

### 2. 안전한 편집 도구 사용

#### Python 스크립트 사용 (권장)

```bash
# 환경 변수 설정
python scripts/edit_env.py set INFLUX_URL "https://example.com"

# 환경 변수 조회
python scripts/edit_env.py get INFLUX_URL

# 모든 환경 변수 목록
python scripts/edit_env.py list
```

#### VS Code 사용

1. VS Code에서 `.env` 파일 열기
2. 우측 하단의 인코딩 표시 클릭
3. "Save with Encoding" 선택
4. "UTF-8" 선택

#### PowerShell에서 안전하게 저장

```powershell
# UTF-8 (BOM 없음)로 저장
$content = Get-Content .env -Raw -Encoding UTF8
[System.IO.File]::WriteAllText("$PWD\.env", $content, [System.Text.UTF8Encoding]::new($false))
```

### 3. PowerShell 기본 인코딩 설정

```powershell
# 현재 세션에만 적용
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'

# 영구 적용 (PowerShell 프로필에 추가)
# 프로필 경로 확인: $PROFILE
# 프로필 편집: notepad $PROFILE
```

또는 스크립트 실행:
```powershell
.\scripts\setup_powershell_utf8.ps1
```

## 인코딩 확인

### Python으로 확인

```python
# BOM 확인
with open('.env', 'rb') as f:
    data = f.read(3)
    has_bom = data == b'\xef\xbb\xbf'
    print(f"Has BOM: {has_bom}")

# 인코딩 테스트
try:
    with open('.env', 'r', encoding='utf-8') as f:
        f.read()
    print("✅ UTF-8 인코딩 정상")
except UnicodeDecodeError as e:
    print(f"❌ UTF-8 인코딩 오류: {e}")
```

### PowerShell로 확인

```powershell
# 파일 인코딩 확인
Get-Content .env -Encoding UTF8 -ErrorAction SilentlyContinue | Select-Object -First 1
```

## 권장 사항

1. ✅ **Python 스크립트 사용**: `scripts/edit_env.py` 사용
2. ✅ **VS Code 사용**: UTF-8로 명시적으로 저장
3. ✅ **자동 정규화**: 백엔드 시작 시 자동 변환됨
4. ❌ **Windows 메모장 사용 금지**: 기본 인코딩이 ANSI
5. ❌ **PowerShell Set-Content 주의**: 인코딩 명시 필요

## 문제 발생 시

1. 백엔드 서버 재시작 (자동 정규화 실행)
2. 수동 정규화:
   ```python
   python -c "from backend.api.services.schemas.models.core.config import _normalize_env_file_encoding; from pathlib import Path; _normalize_env_file_encoding(Path('.env'))"
   ```
3. Python 스크립트로 재생성:
   ```bash
   python scripts/edit_env.py list > env_backup.txt
   # .env 파일 삭제 후
   # env_backup.txt를 참고하여 scripts/edit_env.py로 재생성
   ```

