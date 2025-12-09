"""
SQLite DB 뷰어 스크립트
moby.db 파일의 내용을 보기 좋게 출력합니다.
"""

import sqlite3
import json
from datetime import datetime
from typing import Any, Dict, List

def format_datetime(dt_str: str) -> str:
    """날짜 시간 포맷팅"""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return dt_str

def print_table_info(conn: sqlite3.Connection, table_name: str):
    """테이블 정보 출력"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    print(f"\n{'='*80}")
    print(f"테이블: {table_name}")
    print(f"{'='*80}")
    print(f"{'컬럼명':<20} {'타입':<15} {'NULL':<8} {'기본값':<15}")
    print("-" * 80)
    for col in columns:
        print(f"{col[1]:<20} {col[2]:<15} {'YES' if col[3] == 0 else 'NO':<8} {str(col[4]) if col[4] else 'None':<15}")

def print_alerts(conn: sqlite3.Connection, limit: int = 10):
    """알림 데이터 출력"""
    cursor = conn.cursor()
    
    # 전체 개수
    cursor.execute("SELECT COUNT(*) FROM alerts")
    total = cursor.fetchone()[0]
    
    # 레벨별 통계
    cursor.execute("SELECT level, COUNT(*) FROM alerts GROUP BY level")
    stats = cursor.fetchall()
    
    print(f"\n{'='*80}")
    print(f"알림 데이터 (총 {total}개)")
    print(f"{'='*80}")
    print("\n레벨별 통계:")
    for level, count in stats:
        print(f"  {level}: {count}개")
    
    # 최신 알림 조회
    cursor.execute("""
        SELECT 
            id, alert_id, level, message, sensor_id, source, ts, created_at, details
        FROM alerts 
        ORDER BY created_at DESC 
        LIMIT ?
    """, (limit,))
    
    alerts = cursor.fetchall()
    
    print(f"\n최신 알림 {len(alerts)}개:")
    print("-" * 80)
    
    for i, alert in enumerate(alerts, 1):
        alert_id, alert_id_str, level, message, sensor_id, source, ts, created_at, details_json = alert
        
        # details 파싱
        details = {}
        if details_json:
            try:
                details = json.loads(details_json)
            except:
                details = {"raw": details_json[:100]}
        
        # severity 추출
        severity = details.get("severity", "unknown")
        meta = details.get("meta", {})
        grafana_alert = meta.get("grafana_alert", {})
        grafana_status = grafana_alert.get("status", "unknown")
        grafana_labels = grafana_alert.get("labels", {})
        grafana_severity = grafana_labels.get("severity", "unknown")
        
        print(f"\n[{i}] ID: {alert_id_str}")
        print(f"    레벨: {level} | 심각도: {severity} | Grafana 상태: {grafana_status}")
        print(f"    센서: {sensor_id} | 소스: {source}")
        print(f"    메시지: {message if message else '(메시지 없음)'}")
        print(f"    생성 시간: {format_datetime(created_at)}")
        print(f"    타임스탬프: {format_datetime(ts)}")
        
        if grafana_labels:
            alertname = grafana_labels.get("alertname", "")
            host = grafana_labels.get("host", grafana_labels.get("instance", ""))
            sensor = grafana_labels.get("sensor", "")
            print(f"    Grafana 정보:")
            print(f"      - Alert Name: {alertname}")
            print(f"      - Host: {host}")
            print(f"      - Sensor: {sensor}")
            print(f"      - Severity: {grafana_severity}")

def print_all_tables(conn: sqlite3.Connection):
    """모든 테이블 목록 출력"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\n{'='*80}")
    print("데이터베이스 테이블 목록")
    print(f"{'='*80}")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  - {table}: {count}개 레코드")

def main():
    db_path = "moby.db"
    
    try:
        conn = sqlite3.connect(db_path)
        
        print("=" * 80)
        print("MOBY Platform SQLite Database Viewer")
        print("=" * 80)
        
        # 테이블 목록
        print_all_tables(conn)
        
        # alerts 테이블 정보
        print_table_info(conn, "alerts")
        
        # 알림 데이터
        print_alerts(conn, limit=10)
        
        conn.close()
        
        print(f"\n{'='*80}")
        print("완료")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

