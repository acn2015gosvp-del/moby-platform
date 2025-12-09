# SECRET_KEY 설정 가이드

## 현재 상태
- `.env` 파일에 `SECRET_KEY=your-secret-key-here-change-this-in-production` 기본값 사용 중
- 로그에 경고 메시지 표시: "SECRET_KEY (기본값 사용 중 - 프로덕션 배포 전 변경 필요)"

## 해결 방법

### 1. 안전한 SECRET_KEY 생성

PowerShell에서 다음 명령으로 랜덤 키 생성:

```powershell
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
```

또는 Python에서 직접:

```python
import secrets
secret_key = secrets.token_urlsafe(32)
print(f"SECRET_KEY={secret_key}")
```

### 2. .env 파일 업데이트

`.env` 파일을 열고 다음 줄을 찾아서:

```
SECRET_KEY=your-secret-key-here-change-this-in-production
```

생성된 랜덤 키로 변경:

```
SECRET_KEY=-TQ8bIJoxnHBj2S4RYqMTVkjquR4i7L1wX3U-GF4Ylk
```

**⚠️ 주의사항:**
- 위 예시 키는 예시입니다. 반드시 새로 생성한 키를 사용하세요.
- `.env` 파일은 Git에 커밋하지 마세요 (`.gitignore`에 포함됨)
- 프로덕션 환경에서는 반드시 강력한 랜덤 키를 사용하세요

### 3. 서버 재시작

`.env` 파일 변경 후 백엔드 서버를 재시작하세요:

```powershell
# 현재 서버 종료 (Ctrl+C)
# 그 다음 재시작
cd backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 확인

서버 시작 시 로그에서 경고 메시지가 사라졌는지 확인:

**변경 전:**
```
⚠️ SECRET_KEY (기본값 사용 중 - 프로덕션 배포 전 변경 필요)
```

**변경 후:**
```
✅ 모든 설정 검증 통과
```

## 보안 권장사항

1. **최소 길이**: 32자 이상 권장
2. **랜덤성**: `secrets.token_urlsafe()` 사용 (암호학적으로 안전한 랜덤 생성)
3. **환경별 분리**: 개발/스테이징/프로덕션 환경마다 다른 키 사용
4. **정기 변경**: 보안 사고 발생 시 즉시 변경

## 참고

- `backend/api/services/schemas/models/core/config.py`에서 SECRET_KEY 검증 로직 확인 가능
- 기본값 사용 시 경고 메시지가 표시되지만, 개발 환경에서는 동작합니다
- 프로덕션 환경에서는 기본값 사용 시 치명적 오류로 처리됩니다

