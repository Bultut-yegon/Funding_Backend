from datetime import datetime, timedelta
from app.models.user_session import UserSession
import asyncio

from apscheduler.schedulers.background import BackgroundScheduler
from app.db.database import SessionLocal
from app.services.scraper import run_all_scrapers
from app.services.notification_service import notify_users_of_new_opportunities

scheduler = BackgroundScheduler()

def scrape_job():
    db = SessionLocal()
    try:
        new_count = run_all_scrapers(db)
        if new_count > 0:
            asyncio.run(notify_users_of_new_opportunities(db))
    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(session_cleanup_job, "interval", hours=24, id="session_cleanup_job")
    scheduler.start()
    print("Scheduler started — scraping every 6 hours, session cleanup daily.")

  
    
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