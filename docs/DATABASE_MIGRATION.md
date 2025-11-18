# 데이터베이스 마이그레이션 가이드

MOBY Platform의 데이터베이스 마이그레이션에 대한 가이드입니다.

## 📋 개요

데이터베이스 스키마 변경 시 마이그레이션 스크립트를 사용하여 안전하게 업데이트할 수 있습니다.

**현재 데이터베이스**: SQLite (`moby.db`)

---

## 🚀 사용 방법

### 기본 마이그레이션

```bash
# 프로젝트 루트 디렉토리에서 실행
python scripts/migrate_db.py
```

이 명령은:
- 누락된 테이블을 자동으로 생성
- 테이블 구조를 검증
- 변경사항을 로그로 출력

### 백업 후 마이그레이션

```bash
# 데이터베이스 백업 후 마이그레이션 실행
python scripts/migrate_db.py --backup
```

백업 파일은 `moby.db.backup.YYYYMMDD_HHMMSS` 형식으로 생성됩니다.

### Dry Run (실제 변경 없이 확인)

```bash
# 실제 변경 없이 확인만 수행
python scripts/migrate_db.py --dry-run
```

---

## 📊 현재 데이터베이스 스키마

### 테이블 목록

1. **users** - 사용자 정보
2. **alerts** - 알림 정보

### users 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer | 기본 키 |
| email | String | 이메일 (고유) |
| username | String | 사용자명 (고유) |
| hashed_password | String | 해시된 비밀번호 |
| is_active | Boolean | 활성 상태 |
| role | String | 사용자 역할 (admin, user, viewer) |
| created_at | DateTime | 생성 시간 |
| updated_at | DateTime | 수정 시간 |

**인덱스**:
- `id` (기본 키)
- `email` (고유 인덱스)
- `username` (고유 인덱스)

### alerts 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer | 기본 키 |
| alert_id | String | Alert Engine에서 생성한 ID (고유) |
| level | String | 알림 레벨 (info, warning, critical) |
| message | Text | 알림 메시지 |
| llm_summary | Text | LLM 요약 (선택사항) |
| sensor_id | String | 센서 ID |
| source | String | 알림 소스 (기본값: "alert-engine") |
| ts | String | ISO 8601 타임스탬프 |
| details | JSON | AlertDetailsModel (JSON 형식) |
| created_at | DateTime | 생성 시간 |
| updated_at | DateTime | 수정 시간 |

**인덱스**:
- `id` (기본 키)
- `alert_id` (고유 인덱스)
- `level` (인덱스)
- `sensor_id` (인덱스)
- `created_at` (인덱스)
- `idx_alert_sensor_level` (복합 인덱스: sensor_id, level)
- `idx_alert_level_created` (복합 인덱스: level, created_at)

---

## 🔄 모델 변경 시 마이그레이션

### 1. 모델 수정

`backend/api/models/` 디렉토리에서 모델을 수정합니다.

예시: `backend/api/models/user.py`
```python
class User(Base):
    __tablename__ = "users"
    
    # 기존 컬럼...
    new_field = Column(String, nullable=True)  # 새 컬럼 추가
```

### 2. 마이그레이션 스크립트 실행

```bash
# 백업 후 마이그레이션
python scripts/migrate_db.py --backup
```

**주의**: SQLite는 일부 ALTER TABLE 작업을 지원하지 않습니다. 복잡한 변경(컬럼 삭제, 타입 변경 등)은 수동 마이그레이션이 필요할 수 있습니다.

### 3. 수동 마이그레이션 (필요 시)

복잡한 스키마 변경이 필요한 경우:

1. **데이터베이스 백업**
   ```bash
   python scripts/migrate_db.py --backup
   ```

2. **새 테이블 생성 및 데이터 마이그레이션**
   ```python
   # scripts/manual_migration.py 예시
   from backend.api.services.database import SessionLocal, engine
   from sqlalchemy import text
   
   db = SessionLocal()
   try:
       # 1. 새 테이블 생성
       # 2. 기존 데이터 복사
       # 3. 기존 테이블 삭제
       # 4. 새 테이블 이름 변경
       pass
   finally:
       db.close()
   ```

---

## ⚠️ 주의사항

### SQLite 제한사항

1. **ALTER TABLE 제한**: SQLite는 다음 작업만 지원합니다:
   - 새 컬럼 추가 (`ADD COLUMN`)
   - 컬럼 이름 변경 (`RENAME COLUMN`)
   - 테이블 이름 변경 (`RENAME TO`)

2. **지원하지 않는 작업**:
   - 컬럼 삭제
   - 컬럼 타입 변경
   - 컬럼 순서 변경
   - NOT NULL 제약 조건 추가/제거

3. **해결 방법**:
   - 새 테이블 생성 → 데이터 마이그레이션 → 기존 테이블 삭제 → 이름 변경

### 프로덕션 환경

프로덕션 환경에서는:
1. **반드시 백업 수행**
2. **Dry Run으로 먼저 확인**
3. **유지보수 시간대에 실행**
4. **롤백 계획 수립**

---

## 🔧 고급 사용법

### Alembic 사용 (선택사항)

향후 더 복잡한 마이그레이션이 필요한 경우 Alembic을 사용할 수 있습니다:

```bash
# Alembic 설치
pip install alembic

# Alembic 초기화
alembic init alembic

# 마이그레이션 생성
alembic revision --autogenerate -m "Add new field"

# 마이그레이션 실행
alembic upgrade head
```

---

## 📚 참고 자료

- [SQLAlchemy 공식 문서](https://docs.sqlalchemy.org/)
- [SQLite ALTER TABLE 문서](https://www.sqlite.org/lang_altertable.html)
- [Alembic 공식 문서](https://alembic.sqlalchemy.org/)

---

## 🐛 문제 해결

### 테이블이 생성되지 않는 경우

1. 모델이 올바르게 임포트되었는지 확인
2. `backend/api/models/__init__.py`에 모델이 등록되어 있는지 확인
3. 데이터베이스 파일 권한 확인

### 마이그레이션 실패 시

1. 백업 파일에서 복원:
   ```bash
   cp moby.db.backup.YYYYMMDD_HHMMSS moby.db
   ```

2. 로그 확인:
   ```bash
   python scripts/migrate_db.py --dry-run
   ```

---

**최종 업데이트**: 2025-01-XX

