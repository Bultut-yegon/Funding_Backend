from pydantic import BaseModel
from pydantic import field_validator
from typing import Optional, Union
from app.services.profile_normalization import normalize_value

class ProfileUpdate(BaseModel):
    education_level: Optional[Union[str, list]] = None
    interests: Optional[Union[str, list]] = None
    industry: Optional[Union[str, list]] = None
    country: Optional[Union[str, list]] = None
    skills: Optional[Union[str, list]] = None

    @field_validator(
        "education_level", "interests", "industry", "country", "skills",
        mode="before",
    )
    @classmethod
    def normalize_profile_field(cls, value, info):
        return normalize_value(value, field=info.field_name)

class ProfileOut(BaseModel):
    id: int
    user_id: int
    education_level: Optional[str]
    interests: Optional[str]
    industry: Optional[str]
    country: Optional[str]
    skills: Optional[str]

    @field_validator(
        "education_level", "interests", "industry", "country", "skills",
        mode="before",
    )
    @classmethod
    def normalize_profile_field(cls, value, info):
        return normalize_value(value, field=info.field_name)

    class Config:
        from_attributes = True
