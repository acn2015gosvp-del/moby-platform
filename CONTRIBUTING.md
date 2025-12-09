# 기여 가이드 (Contributing Guide)

MOBY Platform 프로젝트에 기여해주셔서 감사합니다! 이 문서는 프로젝트에 기여하는 방법을 안내합니다.

## 🚀 시작하기

### 1. 저장소 포크 및 클론

1. GitHub에서 저장소를 포크합니다
2. 포크한 저장소를 클론합니다:
```bash
git clone https://github.com/your-username/moby-platform.git
cd moby-platform
```

### 2. 개발 환경 설정

1. 가상 환경 생성 및 활성화
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
`.env` 파일을 생성하고 필요한 환경 변수를 설정합니다.

### 3. 브랜치 생성

새로운 기능이나 버그 수정을 시작하기 전에 브랜치를 생성합니다:

```bash
git checkout -b feature/your-feature-name
# 또는
git checkout -b fix/your-bug-fix
```

## 📝 코딩 규칙

### Python 코드 스타일

- **PEP 8** 스타일 가이드를 따릅니다
- 타입 힌트를 사용합니다
- 함수와 클래스에 docstring을 작성합니다
- 코드는 모듈화되고 재사용 가능하게 작성합니다

**예시:**
```python
from typing import List, Optional
from pydantic import BaseModel

def process_sensor_data(
    sensor_id: str,
    data: List[float],
    threshold: Optional[float] = None
) -> dict:
    """
    센서 데이터를 처리합니다.
    
    Args:
        sensor_id: 센서 ID
        data: 센서 데이터 리스트
        threshold: 임계값 (선택사항)
    
    Returns:
        처리된 데이터 딕셔너리
    """
    # 구현
    pass
```

### 파일 구조 규칙

- **라우터**: `routes_*.py` 형식으로 명명
- **서비스**: `services/` 디렉토리에 비즈니스 로직 배치
- **스키마**: `schemas/` 디렉토리에 Pydantic 모델 정의
- **테스트**: `tests/` 디렉토리에 테스트 코드 작성

### 커밋 메시지 규칙

커밋 메시지는 다음 형식을 따릅니다:

```
<type>: <subject>

<body>

<footer>
```

**Type 종류:**
- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 포맷팅 (기능 변경 없음)
- `refactor`: 코드 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드 설정, 의존성 관리 등

**예시:**
```
feat: 알림 엔진에 이상 벡터 계산 기능 추가

MLP_composite 타입의 이상 벡터를 계산하고
벡터 크기를 기반으로 알림 레벨을 결정하는 로직을 추가했습니다.

Closes #123
```

## 🧪 테스트

### 테스트 작성

- 새로운 기능을 추가할 때는 테스트 코드도 함께 작성합니다
- 테스트는 `tests/` 디렉토리에 작성합니다
- 테스트 파일명은 `test_*.py` 형식을 따릅니다

**예시:**
```python
import pytest
from backend.api.services.alert_engine import process_alert

def test_process_alert_with_valid_data():
    """유효한 데이터로 알림 처리 테스트"""
    data = {
        "sensor_id": "sensor_001",
        "value": 100.0,
        "threshold": 80.0
    }
    result = process_alert(data)
    assert result is not None
    assert result.level == "warning"
```

### 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 파일 테스트
pytest tests/test_alert_engine.py

# 커버리지 포함
pytest --cov=backend
```

## 🔄 Pull Request 프로세스

### 1. 변경사항 커밋

```bash
git add .
git commit -m "feat: 새로운 기능 추가"
```

### 2. 원격 저장소에 푸시

```bash
git push origin feature/your-feature-name
```

### 3. Pull Request 생성

1. GitHub에서 포크한 저장소로 이동
2. "New Pull Request" 버튼 클릭
3. base 브랜치를 `main` 또는 `develop`으로 설정
4. PR 제목과 설명 작성:
   - 변경 사항 요약
   - 관련 이슈 번호 (있는 경우)
   - 테스트 방법

### 4. 코드 리뷰

- 팀원들의 코드 리뷰를 기다립니다
- 리뷰 피드백에 따라 코드를 수정합니다
- 수정 후 다시 커밋하고 푸시합니다

### 5. 병합

- 리뷰가 승인되면 관리자가 병합합니다
- 병합 후 브랜치는 삭제됩니다

## 📋 체크리스트

PR을 제출하기 전에 다음 사항을 확인하세요:

- [ ] 코드가 PEP 8 스타일 가이드를 따릅니다
- [ ] 타입 힌트가 추가되었습니다
- [ ] docstring이 작성되었습니다
- [ ] 테스트 코드가 작성되었고 통과합니다
- [ ] `.env` 파일이 커밋되지 않았습니다
- [ ] 커밋 메시지가 규칙을 따릅니다
- [ ] 관련 문서가 업데이트되었습니다 (필요한 경우)

## 🐛 버그 리포트

버그를 발견하셨다면:

1. GitHub Issues에서 동일한 버그가 이미 보고되었는지 확인
2. 없다면 새 이슈 생성
3. 다음 정보 포함:
   - 버그 설명
   - 재현 단계
   - 예상 동작
   - 실제 동작
   - 환경 정보 (OS, Python 버전 등)

## 💡 기능 제안

새로운 기능을 제안하고 싶으시다면:

1. GitHub Issues에서 "Feature Request" 템플릿 사용
2. 다음 정보 포함:
   - 기능 설명
   - 사용 사례
   - 구현 아이디어 (있는 경우)

## ❓ 질문

질문이 있으시면:
- GitHub Discussions 사용
- 또는 팀 채널에 문의

## 📚 추가 자료

- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [Pydantic 문서](https://docs.pydantic.dev/)
- [InfluxDB 문서](https://docs.influxdata.com/)

---

감사합니다! 🎉

