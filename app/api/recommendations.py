#from fastapi import APIRouter

#router = APIRouter()

#@router.get("/")
#def get_recommendations():
    #return {"message": "Recommendations endpoint - coming soon"}


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.opportunity import Opportunity
from app.models.profile import UserProfile
from app.ml.recommender import get_recommendations
from app.schemas.recommendation import RecommendationOut

router = APIRouter()

@router.get("/", response_model=List[RecommendationOut])
def recommend(
    top_k: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Please complete your profile first")

    opportunities = db.query(Opportunity).all()
    if not opportunities:
        raise HTTPException(status_code=404, detail="No opportunities available yet")

    results = get_recommendations(profile, opportunities, top_k=top_k)
    return results
