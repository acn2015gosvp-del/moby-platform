"""
스케줄러 모듈

매일 18:00에 일일 보고서를 생성하고 이메일로 발송하는 작업을 관리합니다.
"""

import logging
import threading
from datetime import datetime, time
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.api.services.schemas.models.core.logger import get_logger
from backend.api.services.database import SessionLocal
from backend.api.services.report_generator import generate_daily_alert_report_html
from backend.api.services.email_sender import get_email_sender
import os

logger = get_logger(__name__)

# 전역 스케줄러 인스턴스
_scheduler: Optional[BackgroundScheduler] = None


def send_daily_report():
    """
    매일 18:00에 실행되는 일일 보고서 생성 및 이메일 발송 작업
    """
    db = SessionLocal()
    try:
        logger.info("📧 일일 보고서 생성 및 이메일 발송 작업 시작...")
        
        # 오늘 날짜
        today = datetime.now().date()
        
        # 일일 보고서 HTML 생성
        try:
            report_html = generate_daily_alert_report_html(db, today)
            logger.info("✅ 일일 보고서 HTML 생성 완료")
        except Exception as e:
            logger.error(
                f"❌ 일일 보고서 생성 실패: {e}",
                exc_info=True
            )
            return
        
        # 이메일 발송 설정 확인
        email_sender = get_email_sender()
        
        # 수신자 이메일 목록 (환경변수에서 로드)
        recipient_emails_str = os.getenv('REPORT_RECIPIENT_EMAILS', '')
        if not recipient_emails_str:
            logger.warning(
                "REPORT_RECIPIENT_EMAILS 환경변수가 설정되지 않았습니다. "
                "이메일을 발송하지 않습니다."
            )
            return
        
        recipient_emails = [
            email.strip() for email in recipient_emails_str.split(',')
            if email.strip()
        ]
        
        if not recipient_emails:
            logger.warning("수신자 이메일이 없습니다. 이메일을 발송하지 않습니다.")
            return
        
        # 이메일 발송
        try:
            success = email_sender.send_report_email(
                to_emails=recipient_emails,
                report_html=report_html,
                report_date=today.strftime('%Y-%m-%d')
            )
            
            if success:
                logger.info(
                    f"✅ 일일 보고서 이메일 발송 완료: {', '.join(recipient_emails)}"
                )
            else:
                logger.error("❌ 일일 보고서 이메일 발송 실패")
                
        except Exception as e:
            logger.error(
                f"❌ 일일 보고서 이메일 발송 중 오류 발생: {e}",
                exc_info=True
            )
            
    except Exception as e:
        logger.error(
            f"❌ 일일 보고서 작업 중 예상치 못한 오류 발생: {e}",
            exc_info=True
        )
    finally:
        db.close()


def init_scheduler():
    """
    스케줄러를 초기화하고 일일 보고서 작업을 등록합니다.
    """
    global _scheduler
    
    try:
        if _scheduler is not None and _scheduler.running:
            logger.warning("스케줄러가 이미 실행 중입니다.")
            return
        
        # 백그라운드 스케줄러 생성
        _scheduler = BackgroundScheduler()
        
        # 매일 18:00에 실행되는 작업 등록
        _scheduler.add_job(
            func=send_daily_report,
            trigger=CronTrigger(hour=18, minute=0),  # 매일 18:00
            id='daily_report_job',
            name='일일 보고서 생성 및 이메일 발송',
            replace_existing=True
        )
        
        # 스케줄러 시작
        _scheduler.start()
        
        logger.info("✅ 스케줄러 초기화 완료: 매일 18:00에 일일 보고서 생성 및 이메일 발송")
        
    except Exception as e:
        logger.error(
            f"❌ 스케줄러 초기화 실패: {e}",
            exc_info=True
        )


def shutdown_scheduler():
    """
    스케줄러를 종료합니다.
    """
    global _scheduler
    
    try:
        if _scheduler is not None and _scheduler.running:
            _scheduler.shutdown()
            logger.info("✅ 스케줄러 종료 완료")
    except Exception as e:
        logger.error(
            f"❌ 스케줄러 종료 중 오류 발생: {e}",
            exc_info=True
        )


def get_scheduler() -> Optional[BackgroundScheduler]:
    """
    스케줄러 인스턴스를 반환합니다.
    
    Returns:
        BackgroundScheduler 인스턴스 또는 None
    """
    return _scheduler

