#!/usr/bin/env python3
"""
.env 파일을 안전하게 편집하는 헬퍼 스크립트

사용법:
    python scripts/edit_env.py set INFLUX_URL "https://example.com"
    python scripts/edit_env.py get INFLUX_URL
    python scripts/edit_env.py list
"""

import sys
import re
from pathlib import Path
from typing import Optional

def get_env_file_path() -> Path:
    """프로젝트 루트의 .env 파일 경로 반환"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    return project_root / ".env"

def read_env_file() -> dict[str, str]:
    """.env 파일을 읽어서 딕셔너리로 반환"""
    env_file = get_env_file_path()
    
    if not env_file.exists():
        return {}
    
    # 여러 인코딩으로 읽기 시도
    content = None
    for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp949']:
        try:
            with open(env_file, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if content is None:
        raise ValueError("Could not decode .env file")
    
    # 환경 변수 파싱
    env_vars = {}
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            # 주석 제거 (값에 #이 있을 수 있으므로 주의)
            if ' #' in line:
                line = line[:line.index(' #')]
            key, value = line.split('=', 1)
            env_vars[key.strip()] = value.strip().strip('"').strip("'")
    
    return env_vars

def write_env_file(env_vars: dict[str, str], comments: dict[str, str] = None):
    """.env 파일을 UTF-8 (BOM 없음)로 저장"""
    env_file = get_env_file_path()
    
    # 기존 파일 읽기 (주석 보존)
    original_content = ""
    if env_file.exists():
        for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp949']:
            try:
                with open(env_file, 'r', encoding=encoding) as f:
                    original_content = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
    
    # 주석과 구조 보존하면서 변수 업데이트
    lines = original_content.split('\n')
    output_lines = []
    seen_vars = set()
    
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            if key in env_vars:
                # 기존 주석 보존
                if line.strip().startswith(key):
                    indent = len(line) - len(line.lstrip())
                    output_lines.append(' ' * indent + f"{key}={env_vars[key]}")
                else:
                    output_lines.append(f"{key}={env_vars[key]}")
                seen_vars.add(key)
                continue
        
        output_lines.append(line)
    
    # 새 변수 추가
    for key, value in env_vars.items():
        if key not in seen_vars:
            if comments and key in comments:
                output_lines.append(f"# {comments[key]}")
            output_lines.append(f"{key}={value}")
    
    # UTF-8 (BOM 없음)로 저장
    with open(env_file, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(output_lines))
    
    print(f"✅ .env 파일이 UTF-8로 저장되었습니다: {env_file}")

def cmd_set(key: str, value: str):
    """환경 변수 설정"""
    env_vars = read_env_file()
    env_vars[key] = value
    write_env_file(env_vars)
    print(f"✅ {key} = {value}")

def cmd_get(key: str):
    """환경 변수 조회"""
    env_vars = read_env_file()
    if key in env_vars:
        print(f"{key}={env_vars[key]}")
    else:
        print(f"❌ {key} not found")
        sys.exit(1)

def cmd_list():
    """모든 환경 변수 목록"""
    env_vars = read_env_file()
    for key, value in sorted(env_vars.items()):
        if 'TOKEN' in key or 'KEY' in key or 'SECRET' in key:
            display_value = f"{value[:10]}...{value[-10:]}" if len(value) > 20 else "***"
        else:
            display_value = value
        print(f"{key}={display_value}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'set':
        if len(sys.argv) < 4:
            print("Usage: python scripts/edit_env.py set KEY VALUE")
            sys.exit(1)
        cmd_set(sys.argv[2], sys.argv[3])
    elif command == 'get':
        if len(sys.argv) < 3:
            print("Usage: python scripts/edit_env.py get KEY")
            sys.exit(1)
        cmd_get(sys.argv[2])
    elif command == 'list':
        cmd_list()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()

