from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OpportunityOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    category: Optional[str]
    source: Optional[str]
    deadline: Optional[datetime]
    url: Optional[str]
    eligibility_criteria: Optional[str]
    country: Optional[str]


    class Config:
        from_attributes = True

class OpportunityCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    source: Optional[str] = None
    deadline: Optional[datetime] = None
    url: Optional[str] = None
    eligibility_criteria: Optional[str] = None
    country: Optional[str] = None
