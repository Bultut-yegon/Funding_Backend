from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Optional
from app.models.opportunity import Opportunity
from app.models.profile import UserProfile
from app.services.profile_normalization import normalize_value, normalized_terms

MIN_RELEVANCE_SCORE = 0.10
FIELD_WEIGHTS = {
    "interests": 0.30,
    "skills": 0.30,
    "industry": 0.25,
    "education_level": 0.10,
    "country": 0.05,
}
GLOBAL_COUNTRIES = {"global", "worldwide", "international", "any country", "all countries"}
REGION_MEMBERSHIP = {
    "kenya": {"africa", "east africa", "sub-saharan africa"},
    "nigeria": {"africa", "west africa", "sub-saharan africa"},
    "ghana": {"africa", "west africa", "sub-saharan africa"},
}


def _text_score(user_value: Optional[str], opportunity_text: str) -> float:
    value = normalize_value(user_value)
    opportunity_text = (opportunity_text or "").lower()
    if not value:
        return 0.0

    terms = [term.strip().lower() for term in value.split(",") if term.strip()]
    matched_terms = sum(
        1 for term in terms
        if term and (term in opportunity_text)
    )
    direct_coverage = matched_terms / len(terms) if terms else 0.0

    vectorizer = TfidfVectorizer(stop_words="english", lowercase=True)
    try:
        matrix = vectorizer.fit_transform([value, opportunity_text])
        cosine = float(cosine_similarity(matrix[0], matrix[1])[0][0])
    except ValueError:
        cosine = 0.0

    return max(direct_coverage, cosine)


def _country_is_eligible(profile_country: Optional[str], opportunity_country: Optional[str]) -> bool:
    profile_terms = normalized_terms(profile_country, field="country")
    opportunity_terms = normalized_terms(opportunity_country, field="country")
    if not profile_terms:
        return True
    if opportunity_country is None:
        return True

    opportunity_text = normalize_value(opportunity_country, field="country").lower()
    if not opportunity_text:
        return True
    if opportunity_terms & GLOBAL_COUNTRIES or any(term in opportunity_text for term in GLOBAL_COUNTRIES):
        return True

    for country in profile_terms:
        if country in opportunity_text:
            return True
        if any(region in opportunity_text for region in REGION_MEMBERSHIP.get(country, set())):
            return True
        if country in opportunity_terms:
            return True
        if opportunity_terms & REGION_MEMBERSHIP.get(country, set()):
            return True
    return False

def build_user_text(profile: UserProfile) -> str:
    parts = []
    for field, label in (
        ("interests", "Interests"), ("industry", "Industry"),
        ("skills", "Skills"), ("education_level", "Education"), ("country", "Country"),
    ):
        value = normalize_value(getattr(profile, field), field=field)
        if value:
            parts.append(f"{label}: {value}")
    return ". ".join(parts) if parts else "general funding opportunities"

def build_opportunity_text(opp: Opportunity) -> str:
    parts = []
    if opp.title:
        parts.append(opp.title)
    if opp.description:
        parts.append(opp.description)
    if opp.category:
        parts.append(f"Category: {opp.category}")
    if opp.eligibility_criteria:
        parts.append(opp.eligibility_criteria)
    if opp.country:
        parts.append(f"Country: {opp.country}")
    return ". ".join(parts)

def get_recommendations(
    profile: UserProfile,
    opportunities: List[Opportunity],
    top_k: int = 10,
) -> List[dict]:
    if not any(normalize_value(getattr(profile, field), field=field)
               for field in FIELD_WEIGHTS):
        return []

    if not opportunities:
        return []

    opp_texts = [build_opportunity_text(opp) for opp in opportunities]
    ranked = []
    for opp, opp_text in zip(opportunities, opp_texts):
        if not _country_is_eligible(profile.country, opp.country):
            continue
        score = sum(
            weight * _text_score(getattr(profile, field), opp_text)
            for field, weight in FIELD_WEIGHTS.items()
        )
        if score >= MIN_RELEVANCE_SCORE:
            ranked.append((opp, score))
    ranked.sort(key=lambda item: item[1], reverse=True)

    return [
        {"opportunity": opp, "score": float(score)}
        for opp, score in ranked[:top_k]
    ]