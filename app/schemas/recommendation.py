from pydantic import BaseModel
from app.schemas.opportunity import OpportunityOut

class RecommendationOut(BaseModel):
    opportunity: OpportunityOut
    score: float

    class Config:
        from_attributes = True
