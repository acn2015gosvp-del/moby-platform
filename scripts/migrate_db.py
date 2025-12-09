#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 스크립트

모델 변경 시 데이터베이스 스키마를 업데이트합니다.
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import inspect, text
from backend.api.services.database import engine, Base, SessionLocal
from backend.api.services.schemas.models.core.logger import setup_logging, get_logger
from backend.api.services.schemas.models.core.config import settings

# 모든 모델 임포트 (테이블 생성에 필요)
from backend.api.models.user import User
from backend.api.models.alert import Alert
from backend.api.models.role import Role

logger = get_logger(__name__)


def get_existing_tables():
    """현재 데이터베이스에 존재하는 테이블 목록 반환"""
    inspector = inspect(engine)
    return inspector.get_table_names()


def get_expected_tables():
    """모델에서 예상되는 테이블 목록 반환"""
    return list(Base.metadata.tables.keys())


def check_table_structure(table_name: str):
    """테이블 구조 확인"""
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return None
    
    columns = inspector.get_columns(table_name)
    indexes = inspector.get_indexes(table_name)
    
    return {
        "columns": {col["name"]: col for col in columns},
        "indexes": {idx["name"]: idx for idx in indexes}
    }


def migrate():
    """데이터베이스 마이그레이션 실행"""
    logger.info("=" * 60)
    logger.info("데이터베이스 마이그레이션 시작")
    logger.info("=" * 60)
    
    # 기존 테이블 확인
    existing_tables = get_existing_tables()
    expected_tables = get_expected_tables()
    
    logger.info(f"기존 테이블: {existing_tables}")
    logger.info(f"예상 테이블: {expected_tables}")
    
    # 누락된 테이블 확인
    missing_tables = set(expected_tables) - set(existing_tables)
    if missing_tables:
        logger.info(f"누락된 테이블: {missing_tables}")
    
    # 새로운 테이블 생성
    if missing_tables:
        logger.info("누락된 테이블 생성 중...")
        Base.metadata.create_all(bind=engine, tables=[
            Base.metadata.tables[table] for table in missing_tables
        ])
        logger.info(f"✅ {len(missing_tables)}개 테이블 생성 완료")
    else:
        logger.info("✅ 모든 테이블이 존재합니다.")
    
    # 테이블 구조 검증
    logger.info("\n테이블 구조 검증 중...")
    for table_name in expected_tables:
        structure = check_table_structure(table_name)
        if structure:
            logger.info(f"  {table_name}: {len(structure['columns'])}개 컬럼, {len(structure['indexes'])}개 인덱스")
        else:
            logger.warning(f"  {table_name}: 테이블이 존재하지 않습니다.")
    
    logger.info("\n" + "=" * 60)
    logger.info("마이그레이션 완료")
    logger.info("=" * 60)


def backup_database():
    """데이터베이스 백업 (SQLite 전용)"""
    db_path = Path("moby.db")
    if not db_path.exists():
        logger.warning("백업할 데이터베이스 파일이 없습니다.")
        return
    
    from datetime import datetime
    backup_path = db_path.parent / f"moby.db.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    import shutil
    shutil.copy2(db_path, backup_path)
    logger.info(f"✅ 데이터베이스 백업 완료: {backup_path}")


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="데이터베이스 마이그레이션 스크립트")
    parser.add_argument(
        "--backup",
        action="store_true",
        help="마이그레이션 전 데이터베이스 백업"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 변경 없이 확인만 수행"
    )
    
    args = parser.parse_args()
    
    # 로깅 설정
    setup_logging(
        log_level=settings.LOG_LEVEL,
        log_file=None  # 콘솔만 출력
    )
    
    if args.backup:
        backup_database()
    
    if args.dry_run:
        logger.info("DRY RUN 모드: 실제 변경은 수행하지 않습니다.")
        existing_tables = get_existing_tables()
        expected_tables = get_expected_tables()
        missing_tables = set(expected_tables) - set(existing_tables)
        
        if missing_tables:
            logger.info(f"생성될 테이블: {missing_tables}")
        else:
            logger.info("모든 테이블이 존재합니다. 변경사항 없음.")
        return
    
    migrate()


if __name__ == "__main__":
    main()

