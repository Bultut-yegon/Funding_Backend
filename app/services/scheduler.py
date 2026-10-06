from datetime import datetime, timedelta
from app.models.user_session import UserSession
import asyncio

from apscheduler.schedulers.background import BackgroundScheduler
from app.db.database import SessionLocal
from app.services.scraper import run_all_scrapers
from app.services.notification_service import notify_users_of_new_opportunities
from app.core.config import settings
from app.models.opportunity import Opportunity

scheduler = BackgroundScheduler()

def scrape_job():
    db = SessionLocal()
    try:
        new_count = run_all_scrapers(db)
        if new_count > 0:
            asyncio.run(notify_users_of_new_opportunities(db))
    finally:
        db.close()

# def start_scheduler():
#     scheduler.add_job(session_cleanup_job, "interval", hours=24, id="session_cleanup_job")
#     scheduler.start()
#     print("Scheduler started — scraping every 6 hours, session cleanup daily.")
    
def start_scheduler():
    scheduler.add_job(scrape_job, "interval", hours=6, id="scrape_job")
    scheduler.add_job(session_cleanup_job, "interval", hours=24, id="session_cleanup_job")
    if settings.ENABLE_EXPIRY_CLEANUP:
        scheduler.add_job(expired_cleanup_job, "interval", hours=24, id="expired_cleanup_job")
    scheduler.start()
    print("Scheduler started.")

  
    
def session_cleanup_job():
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=7)
        deleted = (
            db.query(UserSession)
            .filter(
                (UserSession.revoked_at.isnot(None)) | (UserSession.expires_at < datetime.utcnow()),
                UserSession.expires_at < cutoff,
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        if deleted:
            print(f"Session cleanup: removed {deleted} expired/revoked sessions.")
    finally:
        db.close()
        


def expired_cleanup_job():
    db = SessionLocal()
    try:
        deleted = (
            db.query(Opportunity)
            .filter(Opportunity.deadline.isnot(None), Opportunity.deadline < datetime.utcnow())
            .delete(synchronize_session=False)
        )
        db.commit()
        if deleted:
            print(f"Expired cleanup: removed {deleted} opportunities past their deadline.")
    finally:
        db.close()