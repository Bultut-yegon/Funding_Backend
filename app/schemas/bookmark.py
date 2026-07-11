from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.opportunity import OpportunityOut

class BookmarkUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class BookmarkOut(BaseModel):
    id: int
    user_id: int
    opportunity_id: int
    status: str
    notes: Optional[str]
    applied_date: Optional[datetime]
    created_at: Optional[datetime]
    opportunity: Optional[OpportunityOut] = None

    class Config:
        from_attributes = True