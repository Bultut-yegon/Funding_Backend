from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    status = Column(String, default="Saved")
    notes = Column(String, nullable=True)
    applied_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    opportunity = relationship("Opportunity")