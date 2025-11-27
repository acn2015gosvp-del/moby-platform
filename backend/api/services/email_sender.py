"""
이메일 발송 모듈

SMTP를 사용하여 HTML 이메일을 발송하는 기능을 제공합니다.
UTF-8 인코딩을 보장하여 한글이 깨지지 않도록 처리합니다.
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from pathlib import Path

from backend.api.services.schemas.models.core.config import settings
from backend.api.services.schemas.models.core.logger import get_logger

logger = get_logger(__name__)


class EmailSender:
    """이메일 발송 클래스"""
    
    def __init__(self):
        """
        SMTP 설정을 환경변수에서 로드합니다.
        
        필수 환경변수:
        - SMTP_HOST: SMTP 서버 호스트 (예: smtp.gmail.com)
        - SMTP_PORT: SMTP 서버 포트 (예: 587)
        - SMTP_USER: SMTP 사용자명 (이메일 주소)
        - SMTP_PASSWORD: SMTP 비밀번호 또는 앱 비밀번호
        - SMTP_FROM: 발신자 이메일 주소 (기본값: SMTP_USER)
        """
        # 환경변수에서 SMTP 설정 로드 (os.getenv 사용, CURSOR.md 규칙 준수)
        self.smtp_host = os.getenv('SMTP_HOST', '')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.smtp_from = os.getenv('SMTP_FROM', self.smtp_user)
        self.use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        
        # 설정 검증
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            logger.warning(
                "SMTP 설정이 완전하지 않습니다. "
                "SMTP_HOST, SMTP_USER, SMTP_PASSWORD 환경변수를 설정하세요."
            )
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None
    ) -> bool:
        """
        HTML 이메일을 발송합니다.
        
        Args:
            to_emails: 수신자 이메일 주소 리스트
            subject: 이메일 제목 (한글 지원)
            html_body: HTML 본문
            text_body: 텍스트 본문 (선택, 없으면 HTML에서 자동 변환)
            cc_emails: 참조 수신자 이메일 주소 리스트 (선택)
            bcc_emails: 숨은 참조 수신자 이메일 주소 리스트 (선택)
            
        Returns:
            발송 성공 여부 (bool)
        """
        # SMTP 설정 검증
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            logger.error(
                "이메일 발송 실패: SMTP 설정이 완전하지 않습니다. "
                "SMTP_HOST, SMTP_USER, SMTP_PASSWORD 환경변수를 확인하세요."
            )
            return False
        
        try:
            # 메시지 생성
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_from
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # 수신자 목록 구성
            recipients = to_emails.copy()
            if cc_emails:
                recipients.extend(cc_emails)
            if bcc_emails:
                recipients.extend(bcc_emails)
            
            # 텍스트 본문 추가 (없으면 HTML에서 추출한 간단한 텍스트 사용)
            if text_body:
                text_part = MIMEText(text_body, 'plain', 'utf-8')
                msg.attach(text_part)
            else:
                # HTML에서 간단한 텍스트 추출 (기본 처리)
                import re
                simple_text = re.sub(r'<[^>]+>', '', html_body)
                simple_text = simple_text.strip()[:500]  # 최대 500자
                text_part = MIMEText(simple_text, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # HTML 본문 추가 (UTF-8 인코딩 명시, CURSOR.md 규칙 준수)
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # SMTP 서버 연결 및 발송
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                if self.use_tls:
                    server.starttls()
                
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg, from_addr=self.smtp_from, to_addrs=recipients)
            
            logger.info(
                f"✅ 이메일 발송 성공: '{subject}' → {', '.join(to_emails)}"
            )
            return True
            
        except smtplib.SMTPException as e:
            logger.error(
                f"❌ 이메일 발송 실패 (SMTP 오류): {e}",
                exc_info=True
            )
            return False
        except Exception as e:
            logger.error(
                f"❌ 이메일 발송 실패 (예상치 못한 오류): {e}",
                exc_info=True
            )
            return False
    
    def send_report_email(
        self,
        to_emails: List[str],
        report_html: str,
        report_date: str,
        device_name: Optional[str] = None
    ) -> bool:
        """
        일일 보고서 이메일을 발송합니다.
        
        Args:
            to_emails: 수신자 이메일 주소 리스트
            report_html: 보고서 HTML 내용
            report_date: 보고서 날짜 (예: "2025-01-15")
            device_name: 디바이스/설비명 (선택)
            
        Returns:
            발송 성공 여부 (bool)
        """
        # 제목 생성 (한글 지원)
        subject = f"MOBY 일일 이상징후 보고서 - {report_date}"
        if device_name:
            subject = f"MOBY 일일 이상징후 보고서 - {device_name} ({report_date})"
        
        # HTML 본문 구성
        html_body = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Malgun Gothic', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .report-date {{
            color: #7f8c8d;
            font-size: 14px;
            margin-bottom: 20px;
        }}
        .report-content {{
            margin-top: 30px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
            font-size: 12px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 MOBY 일일 이상징후 보고서</h1>
        <div class="report-date">
            보고 날짜: {report_date}
            {f'<br>설비명: {device_name}' if device_name else ''}
        </div>
        <div class="report-content">
            {report_html}
        </div>
        <div class="footer">
            <p>이 보고서는 MOBY Platform에서 자동 생성되었습니다.</p>
            <p>문의사항이 있으시면 시스템 관리자에게 연락해주세요.</p>
        </div>
    </div>
</body>
</html>
"""
        
        # 텍스트 본문 생성 (간단한 버전)
        text_body = f"""
MOBY 일일 이상징후 보고서

보고 날짜: {report_date}
{('설비명: ' + device_name + '\n') if device_name else ''}

보고서 내용은 HTML 형식으로 제공됩니다.
이메일 클라이언트에서 HTML 형식을 지원하지 않는 경우, 
웹 브라우저로 확인해주세요.
"""
        
        return self.send_email(
            to_emails=to_emails,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )


# 전역 이메일 발송기 인스턴스
_email_sender: Optional[EmailSender] = None


def get_email_sender() -> EmailSender:
    """
    이메일 발송기 인스턴스를 싱글톤 패턴으로 반환합니다.
    
    Returns:
        EmailSender: 이메일 발송기 인스턴스
    """
    global _email_sender
    if _email_sender is None:
        _email_sender = EmailSender()
    return _email_sender

