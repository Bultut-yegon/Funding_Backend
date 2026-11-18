"""Application service for generating personalized opportunity recommendations."""

from typing import List

from app.ml.recommender import get_recommendations as _match_recommendations
from app.models.opportunity import Opportunity
from app.models.profile import UserProfile


def get_recommendations(
    profile: UserProfile,
    opportunities: List[Opportunity],
    top_k: int = 10,
) -> List[dict]:
    """Return ranked, eligible recommendations for a user's profile."""
    return _match_recommendations(profile, opportunities, top_k=top_k)