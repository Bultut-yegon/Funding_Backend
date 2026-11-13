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


def _has_recommendation_preferences(profile: UserProfile) -> bool:
    """Return whether the user has supplied at least one matching preference."""
    return any(
        value and value.strip()
        for value in (
            profile.interests,
            profile.skills,
            profile.industry,
            profile.education_level,
            profile.country,
        )
    )


@router.get("/", response_model=List[RecommendationOut])
def recommend(
    top_k: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile or not _has_recommendation_preferences(profile):
        raise HTTPException(
            status_code=400,
            detail="Please update your interests page before viewing recommendations",
        )

    opportunities = db.query(Opportunity).all()
    if not opportunities:
        raise HTTPException(status_code=404, detail="No opportunities available yet")

    results = get_recommendations(profile, opportunities, top_k=top_k)
    return results
