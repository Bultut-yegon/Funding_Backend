import feedparser
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.opportunity import Opportunity
from app.ml.classifier import classify_opportunity

# ── 1. Opportunity Desk RSS ──────────────────────────────────────────────────

FEEDS = [
    "https://opportunitydesk.org/feed/",
    "https://www.scholars4dev.com/feed/",
    "https://www.afterschoolafrica.com/feed/",
]

def scrape_rss_feeds(db: Session):
    added = 0
    for feed_url in FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                description = BeautifulSoup(
                    entry.get("summary", ""), "html.parser"
                ).get_text()[:500]
                url = entry.get("link", "")
                source = feed.feed.get("title", feed_url)

                if not title or not url:
                    continue

                existing = db.query(Opportunity).filter(Opportunity.url == url).first()
                if existing:
                    continue

                category = classify_opportunity(title, description)

                opp = Opportunity(
                    title=title,
                    description=description,
                    category=category,
                    source=source,
                    url=url,
                    deadline=None,
                )
                db.add(opp)
                added += 1

            db.commit()
        except Exception as e:
            print(f"RSS feed error ({feed_url}): {e}")

    return added


# ── 2. ReliefWeb API (UN-backed, free, no key needed) ───────────────────────

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
        data = response.json()

        for item in data.get("data", []):
            fields = item.get("fields", {})
            title = fields.get("title", "").strip()
            description = BeautifulSoup(
                fields.get("body", ""), "html.parser"
            ).get_text()[:500]
            opp_url = fields.get("url", "")

            if not title or not opp_url:
                continue

            existing = db.query(Opportunity).filter(Opportunity.url == opp_url).first()
            if existing:
                continue

            category = classify_opportunity(title, description)

            opp = Opportunity(
                title=title,
                description=description,
                category=category,
                source="ReliefWeb / UN",
                url=opp_url,
                deadline=None,
            )
            db.add(opp)
            added += 1

        db.commit()
    except Exception as e:
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
            description = entry.get("summary", "")[:500]
            opp_url = entry.get("link", "")

            if not title or not opp_url:
                continue

            existing = db.query(Opportunity).filter(Opportunity.url == opp_url).first()
            if existing:
                continue

            category = classify_opportunity(title, description)

            opp = Opportunity(
                title=title,
                description=description,
                category=category,
                source="Grants.gov",
                url=opp_url,
                deadline=None,
            )
            db.add(opp)
            added += 1

        db.commit()
    except Exception as e:
        print(f"Grants.gov error: {e}")

    return added


# ── Master runner ─────────────────────────────────────────────────────────────

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
