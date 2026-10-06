"""
One-off backfill: re-classifies every existing opportunity and extracts
eligibility + deadline using the same enrichment used for new scrapes.
Run manually: python backfill_enrichment.py
"""
import time
from app.db.database import SessionLocal
from app.models.opportunity import Opportunity
from app.ml.enrichment import enrich_opportunity


def run():
    db = SessionLocal()
    try:
        opportunities = db.query(Opportunity).all()
        print(f"Found {len(opportunities)} opportunities to reprocess.")

        for i, opp in enumerate(opportunities, start=1):
            result = enrich_opportunity(opp.title, opp.description or "")
            opp.category = result["category"]
            opp.eligibility_criteria = result["eligibility"]
            if result["deadline"]:
                opp.deadline = result["deadline"]
            db.commit()
            print(f"[{i}/{len(opportunities)}] {opp.title[:60]} -> {opp.category}")
            time.sleep(0.5)  # stay comfortably under Groq rate limits

        print("Backfill complete.")
    finally:
        db.close()


if __name__ == "__main__":
    run()