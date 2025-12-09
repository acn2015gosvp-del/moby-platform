"""
기존 텍스트 보고서를 PDF로 변환 테스트
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.api.services.pdf_generator import markdown_to_pdf

# 이전에 생성된 보고서 읽기
report_file = Path("reports/report_20251208_103916.txt")

if report_file.exists():
    print("=" * 60)
    print("텍스트 보고서를 PDF로 변환 테스트")
    print("=" * 60)
    print()
    
    # 텍스트 파일 읽기 (마크다운 부분만 추출)
    with open(report_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 마크다운 부분 찾기 (첫 번째 # 부터)
    markdown_start = content.find("#")
    if markdown_start > 0:
        markdown_text = content[markdown_start:]
    else:
        markdown_text = content
    
    # PDF로 변환
    output_pdf = report_file.with_suffix('.pdf')
    
    metadata = {
        "보고 기간": "2025-12-01 ~ 2025-12-08",
        "설비 ID": "44d5516Z",
        "생성 시각": "2025-12-08 10:39:16 UTC"
    }
    
    print(f"📄 원본 파일: {report_file}")
    print(f"📄 변환 대상: {output_pdf}")
    print()
    print("🔄 PDF 변환 중...")
    
    success = markdown_to_pdf(
        markdown_text=markdown_text,
        output_path=output_pdf,
        title="MOBY 설비 상태 보고서",
        metadata=metadata
    )
    
    if success:
        print(f"✅ PDF 변환 성공!")
        print(f"   파일: {output_pdf}")
        print(f"   크기: {output_pdf.stat().st_size / 1024:.2f} KB")
    else:
        print("❌ PDF 변환 실패")
else:
    print(f"❌ 보고서 파일을 찾을 수 없습니다: {report_file}")

