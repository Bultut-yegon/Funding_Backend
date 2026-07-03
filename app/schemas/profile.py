from pydantic import BaseModel
from typing import Optional

class ProfileUpdate(BaseModel):
    education_level: Optional[str] = None
    interests: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    skills: Optional[str] = None

class ProfileOut(BaseModel):
    id: int
    user_id: int
    education_level: Optional[str]
    interests: Optional[str]
    industry: Optional[str]
    country: Optional[str]
    skills: Optional[str]

    class Config:
        from_attributes = True
