# from apscheduler.schedulers.background import BackgroundScheduler
# from app.db.database import SessionLocal
# from app.services.scraper import run_all_scrapers

# scheduler = BackgroundScheduler()

# def scrape_job():
#     db = SessionLocal()
#     try:
#         run_all_scrapers(db)
#     finally:
#         db.close()

# def start_scheduler():
#     scheduler.add_job(scrape_job, "interval", hours=6, id="scrape_job")
#     scheduler.start()
#     print("Scheduler started — scraping every 6 hours.")


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
    scheduler.add_job(scrape_job, "interval", hours=6, id="scrape_job")
    scheduler.start()
    print("Scheduler started — scraping every 6 hours.")