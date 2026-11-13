import feedparser
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.opportunity import Opportunity
from app.ml.enrichment import enrich_opportunity

#1. Opportunity Desk RSS 

FEEDS = [
    "https://opportunitydesk.org/feed/",
    "https://www.scholars4dev.com/feed/",
    "https://www.afterschoolafrica.com/feed/",
]


def _description(value: str, limit: int = 12000) -> str:
    """Convert feed/API HTML to enough plain text for requirements extraction."""
    return BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True)[:limit]


def _add_opportunity(db: Session, *, title: str, description: str, url: str, source: str) -> bool:
    if not title or not url or db.query(Opportunity).filter(Opportunity.url == url).first():
        return False

    enrichment = enrich_opportunity(title, description)
    if enrichment["failed"]:
        print(f"Enrichment unavailable; storing un-enriched opportunity: {title[:80]}")

    db.add(Opportunity(
        title=title,
        description=description,
        category=enrichment["category"],
        source=source,
        url=url,
        deadline=enrichment["deadline"],
        eligibility_criteria=enrichment["eligibility"],
        country=enrichment["country"],
    ))
    return True


def scrape_rss_feeds(db: Session):
    added = 0
    for feed_url in FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                description = _description(entry.get("summary", ""))
                url = entry.get("link", "")
                source = feed.feed.get("title", feed_url)

                added += _add_opportunity(
                    db, title=title, description=description, url=url, source=source
                )

            db.commit()
        except Exception as e:
            db.rollback()
            print(f"RSS feed error ({feed_url}): {e}")

    return added


#2. ReliefWeb API (UN-backed, free, no key needed)

def scrape_reliefweb(db: Session):
    added = 0
    url = "https://api.reliefweb.int/v1/jobs"
    params = {
        "appname": "fundinghub",
        "limit": 50,
        "fields[include][]": ["title", "body", "url", "date"],
    }

    try:
        response = httpx.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        for item in data.get("data", []):
            fields = item.get("fields", {})
            title = fields.get("title", "").strip()
            description = _description(fields.get("body", ""))
            opp_url = fields.get("url", "")

            added += _add_opportunity(
                db,
                title=title,
                description=description,
                url=opp_url,
                source="ReliefWeb / UN",
            )

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"ReliefWeb API error: {e}")

    return added


# ── 3. Grants.gov RSS (US federal grants, open API) ─────────────────────────

def scrape_grants_gov(db: Session):
    added = 0
    url = "https://www.grants.gov/rss/GG_NewOpp.xml"

    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.get("title", "").strip()
            description = _description(entry.get("summary", ""))
            opp_url = entry.get("link", "")

            added += _add_opportunity(
                db,
                title=title,
                description=description,
                url=opp_url,
                source="Grants.gov",
            )

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Grants.gov error: {e}")

    return added


#  Master runner

def run_all_scrapers(db: Session):
    print("Starting scrapers...")
    total = 0
    total += scrape_rss_feeds(db)
    print(f"  RSS feeds: done")
    total += scrape_reliefweb(db)
    print(f"  ReliefWeb: done")
    total += scrape_grants_gov(db)
    print(f"  Grants.gov: done")
    print(f"Scraping complete. Added {total} new opportunities.")
    return total
