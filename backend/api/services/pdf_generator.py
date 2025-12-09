"""
PDF 보고서 생성 유틸리티

마크다운 형식의 보고서를 PDF로 변환합니다.
"""

import logging
import re
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    logger.warning("markdown 라이브러리가 설치되지 않았습니다. pip install markdown")

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab 라이브러리가 설치되지 않았습니다. pip install reportlab")


def markdown_to_pdf(
    markdown_text: str,
    output_path: Path,
    title: str = "MOBY 설비 상태 보고서",
    metadata: Optional[dict] = None
) -> bool:
    """
    마크다운 텍스트를 PDF로 변환합니다.
    
    Args:
        markdown_text: 마크다운 형식의 텍스트
        output_path: PDF 파일 저장 경로
        title: 보고서 제목
        metadata: 보고서 메타데이터 (보고 기간, 설비 ID 등)
        
    Returns:
        성공 여부 (bool)
    """
    if not REPORTLAB_AVAILABLE:
        logger.error("reportlab 라이브러리가 필요합니다. pip install reportlab")
        return False
    
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # PDF 문서 생성
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # 스타일 설정
        styles = getSampleStyleSheet()
        
        # 한글 폰트 설정 시도 (없으면 기본 폰트 사용)
        try:
            # Windows 기본 한글 폰트
            pdfmetrics.registerFont(TTFont('NanumGothic', 'C:/Windows/Fonts/malgun.ttf'))
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName='NanumGothic',
                fontSize=18,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=12
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontName='NanumGothic',
                fontSize=14,
                textColor=colors.HexColor('#34495e'),
                spaceAfter=10
            )
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName='NanumGothic',
                fontSize=10,
                leading=14
            )
        except:
            # 폰트 등록 실패 시 기본 폰트 사용
            title_style = styles['Heading1']
            heading_style = styles['Heading2']
            normal_style = styles['Normal']
        
        # 스토리 빌드
        story = []
        
        # 제목
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.5*cm))
        
        # 메타데이터 테이블
        if metadata:
            metadata_data = [[key, value] for key, value in metadata.items()]
            metadata_table = Table(metadata_data, colWidths=[4*cm, 12*cm])
            metadata_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(metadata_table)
            story.append(Spacer(1, 0.5*cm))
        
        # 마크다운 파싱 및 변환
        lines = markdown_text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                story.append(Spacer(1, 0.3*cm))
                i += 1
                continue
            
            # 제목 처리
            if line.startswith('# '):
                story.append(Paragraph(line[2:], title_style))
                story.append(Spacer(1, 0.3*cm))
            elif line.startswith('## '):
                story.append(Paragraph(line[3:], heading_style))
                story.append(Spacer(1, 0.2*cm))
            elif line.startswith('### '):
                story.append(Paragraph(line[4:], styles['Heading3']))
                story.append(Spacer(1, 0.15*cm))
            # 테이블 처리
            elif line.startswith('|'):
                table_data = []
                # 헤더 행
                if i < len(lines) and lines[i].startswith('|'):
                    headers = [cell.strip() for cell in lines[i].split('|')[1:-1]]
                    table_data.append(headers)
                    i += 1
                # 구분선 건너뛰기
                if i < len(lines) and lines[i].startswith('|---'):
                    i += 1
                # 데이터 행
                while i < len(lines) and lines[i].startswith('|'):
                    row = [cell.strip() for cell in lines[i].split('|')[1:-1]]
                    table_data.append(row)
                    i += 1
                
                if table_data:
                    table = Table(table_data, repeatRows=1)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 0.3*cm))
                continue
            # 구분선
            elif line.startswith('---'):
                story.append(Spacer(1, 0.5*cm))
            # 일반 텍스트
            else:
                # 마크다운 강조 제거
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
                story.append(Paragraph(text, normal_style))
            
            i += 1
        
        # PDF 생성
        doc.build(story)
        
        logger.info(f"PDF 보고서 생성 완료: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"PDF 생성 실패: {e}", exc_info=True)
        return False

