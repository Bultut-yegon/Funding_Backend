from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from app.db.database import get_db
from app.core.security import get_current_user, get_admin_user
from app.models.user import User
from app.models.analytics import AnalyticsEvent

router = APIRouter()

class EventCreate(BaseModel):
    event_type: str
    opportunity_id: Optional[int] = None

@router.post("/track")
def track_event(
    data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = AnalyticsEvent(
        user_id=current_user.id,
        event_type=data.event_type,
        opportunity_id=data.opportunity_id,
    )
    db.add(event)
    db.commit()
    return {"message": "Event tracked"}

@router.get("/me")
def my_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    views = db.query(AnalyticsEvent).filter(
        AnalyticsEvent.user_id == current_user.id,
        AnalyticsEvent.event_type == "view",
    ).count()

    bookmarks = db.query(AnalyticsEvent).filter(
        AnalyticsEvent.user_id == current_user.id,
        AnalyticsEvent.event_type == "bookmark",
    ).count()

    apply_clicks = db.query(AnalyticsEvent).filter(
        AnalyticsEvent.user_id == current_user.id,
        AnalyticsEvent.event_type == "apply_click",
    ).count()

    return {
        "total_views": views,
        "total_bookmarks": bookmarks,
        "total_apply_clicks": apply_clicks,
    }

@router.get("/admin/overview")
def admin_analytics(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    total_events = db.query(AnalyticsEvent).count()
    views = db.query(AnalyticsEvent).filter(AnalyticsEvent.event_type == "view").count()
    bookmarks = db.query(AnalyticsEvent).filter(AnalyticsEvent.event_type == "bookmark").count()
    apply_clicks = db.query(AnalyticsEvent).filter(AnalyticsEvent.event_type == "apply_click").count()

    return {
        "total_events": total_events,
        "total_views": views,
        "total_bookmarks": bookmarks,
        "total_apply_clicks": apply_clicks,
    }
