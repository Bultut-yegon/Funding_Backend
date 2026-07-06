from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.db.database import Base

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_type = Column(String, nullable=False)  # view, bookmark, apply_click
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
