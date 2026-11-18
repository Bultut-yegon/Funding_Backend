"""
Remove opportunities whose deadlines have passed.

    python cleanup_expired.py               # preview only
    python cleanup_expired.py --apply       # delete expired, keep bookmarked
    DATABASE_URL="$NEON_URL" python cleanup_expired.py --apply
"""

import sys

from app.db.database import SessionLocal
from app.models.opportunity import Opportunity
from app.services.cleanup import find_expired, delete_expired_opportunities


def run(apply: bool, include_bookmarked: bool) -> None:
    db = SessionLocal()
    try:
        total = db.query(Opportunity).count()
        no_deadline = db.query(Opportunity).filter(Opportunity.deadline.is_(None)).count()
        deletable, kept = find_expired(db, include_bookmarked)

        print(f"Total opportunities: {total} (no deadline recorded: {no_deadline})")
        print(f"Expired and deletable: {len(deletable)}")
        for opportunity in sorted(deletable, key=lambda item: item.deadline):
            print(f"  [{opportunity.id}] {opportunity.deadline:%Y-%m-%d}  {opportunity.title[:70]}")

        if kept:
            print(f"Expired but bookmarked by a user (kept): {len(kept)}")
            for opportunity in kept:
                print(f"  [{opportunity.id}] {opportunity.deadline:%Y-%m-%d}  {opportunity.title[:70]}")

        print(f"Would remain after cleanup: {total - len(deletable)}")

        if not apply:
            print("\nDry run only. Re-run with --apply to delete.")
            return

        result = delete_expired_opportunities(db, include_bookmarked)
        print(f"\nDeleted {result['deleted']} opportunities.")
    finally:
        db.close()


if __name__ == "__main__":
    run("--apply" in sys.argv, "--include-bookmarked" in sys.argv)
