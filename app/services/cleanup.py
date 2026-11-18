from datetime import datetime

from sqlalchemy.orm import Session

from app.models.analytics import AnalyticsEvent
from app.models.bookmark import Bookmark
from app.models.opportunity import Opportunity
from app.models.recommendation import Recommendation
from app.services.deadlines import start_of_today


def find_expired(db: Session, include_bookmarked: bool = False):
    """Return expired opportunities split into deletable and bookmarked rows."""
    expired = (
        db.query(Opportunity)
        .filter(
            Opportunity.deadline.isnot(None),
            Opportunity.deadline < start_of_today(),
        )
        .all()
    )

    if include_bookmarked:
        return expired, []

    bookmarked_ids = {
        row[0]
        for row in db.query(Bookmark.opportunity_id).distinct().all()
    }
    deletable = [opportunity for opportunity in expired if opportunity.id not in bookmarked_ids]
    kept = [opportunity for opportunity in expired if opportunity.id in bookmarked_ids]
    return deletable, kept


def delete_expired_opportunities(db: Session, include_bookmarked: bool = False) -> dict:
    deletable, kept = find_expired(db, include_bookmarked)
    ids = [opportunity.id for opportunity in deletable]

    if not ids:
        return {"deleted": 0, "kept_bookmarked": len(kept)}

    if include_bookmarked:
        (
            db.query(Bookmark)
            .filter(Bookmark.opportunity_id.in_(ids))
            .delete(synchronize_session=False)
        )

    (
        db.query(Recommendation)
        .filter(Recommendation.opportunity_id.in_(ids))
        .delete(synchronize_session=False)
    )

    (
        db.query(AnalyticsEvent)
        .filter(AnalyticsEvent.opportunity_id.in_(ids))
        .update({AnalyticsEvent.opportunity_id: None}, synchronize_session=False)
    )

    (
        db.query(Opportunity)
        .filter(Opportunity.id.in_(ids))
        .delete(synchronize_session=False)
    )

    db.commit()
    return {"deleted": len(ids), "kept_bookmarked": len(kept)}
