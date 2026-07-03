# import numpy as np
# from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity
# from typing import List
# from app.models.opportunity import Opportunity
# from app.models.profile import UserProfile

# model = SentenceTransformer("all-MiniLM-L6-v2")

# def build_user_text(profile: UserProfile) -> str:
#     parts = []
#     if profile.interests:
#         parts.append(f"Interests: {profile.interests}")
#     if profile.industry:
#         parts.append(f"Industry: {profile.industry}")
#     if profile.skills:
#         parts.append(f"Skills: {profile.skills}")
#     if profile.education_level:
#         parts.append(f"Education: {profile.education_level}")
#     if profile.country:
#         parts.append(f"Country: {profile.country}")
#     return ". ".join(parts) if parts else "general funding opportunities"

# def build_opportunity_text(opp: Opportunity) -> str:
#     parts = []
#     if opp.title:
#         parts.append(opp.title)
#     if opp.description:
#         parts.append(opp.description)
#     if opp.category:
#         parts.append(f"Category: {opp.category}")
#     return ". ".join(parts)

# def get_recommendations(
#     profile: UserProfile,
#     opportunities: List[Opportunity],
#     top_k: int = 10,
# ) -> List[dict]:
#     if not opportunities:
#         return []

#     user_text = build_user_text(profile)
#     opp_texts = [build_opportunity_text(opp) for opp in opportunities]

#     user_embedding = model.encode([user_text])
#     opp_embeddings = model.encode(opp_texts)

#     scores = cosine_similarity(user_embedding, opp_embeddings)[0]

#     ranked = sorted(
#         zip(opportunities, scores),
#         key=lambda x: x[1],
#         reverse=True,
#     )

#     return [
#         {
#             "opportunity": opp,
#             "score": float(score),
#         }
#         for opp, score in ranked[:top_k]
#     ]

# import numpy as np
# from sklearn.metrics.pairwise import cosine_similarity
# from typing import List
# from app.models.opportunity import Opportunity
# from app.models.profile import UserProfile

# _model = None

# def get_model():
#     global _model
#     if _model is None:
#         from sentence_transformers import SentenceTransformer
#         _model = SentenceTransformer("all-MiniLM-L6-v2")
#     return _model

# def build_user_text(profile: UserProfile) -> str:
#     parts = []
#     if profile.interests:
#         parts.append(f"Interests: {profile.interests}")
#     if profile.industry:
#         parts.append(f"Industry: {profile.industry}")
#     if profile.skills:
#         parts.append(f"Skills: {profile.skills}")
#     if profile.education_level:
#         parts.append(f"Education: {profile.education_level}")
#     if profile.country:
#         parts.append(f"Country: {profile.country}")
#     return ". ".join(parts) if parts else "general funding opportunities"

# def build_opportunity_text(opp: Opportunity) -> str:
#     parts = []
#     if opp.title:
#         parts.append(opp.title)
#     if opp.description:
#         parts.append(opp.description)
#     if opp.category:
#         parts.append(f"Category: {opp.category}")
#     return ". ".join(parts)

# def get_recommendations(
#     profile: UserProfile,
#     opportunities: List[Opportunity],
#     top_k: int = 10,
# ) -> List[dict]:
#     if not opportunities:
#         return []

#     model = get_model()
#     user_text = build_user_text(profile)
#     opp_texts = [build_opportunity_text(opp) for opp in opportunities]

#     user_embedding = model.encode([user_text])
#     opp_embeddings = model.encode(opp_texts)

#     scores = cosine_similarity(user_embedding, opp_embeddings)[0]

#     ranked = sorted(
#         zip(opportunities, scores),
#         key=lambda x: x[1],
#         reverse=True,
#     )

#     return [
#         {"opportunity": opp, "score": float(score)}
#         for opp, score in ranked[:top_k]
#     ]



import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List
from app.models.opportunity import Opportunity
from app.models.profile import UserProfile

def build_user_text(profile: UserProfile) -> str:
    parts = []
    if profile.interests:
        parts.append(f"Interests: {profile.interests}")
    if profile.industry:
        parts.append(f"Industry: {profile.industry}")
    if profile.skills:
        parts.append(f"Skills: {profile.skills}")
    if profile.education_level:
        parts.append(f"Education: {profile.education_level}")
    if profile.country:
        parts.append(f"Country: {profile.country}")
    return ". ".join(parts) if parts else "general funding opportunities"

def build_opportunity_text(opp: Opportunity) -> str:
    parts = []
    if opp.title:
        parts.append(opp.title)
    if opp.description:
        parts.append(opp.description)
    if opp.category:
        parts.append(f"Category: {opp.category}")
    return ". ".join(parts)

def get_recommendations(
    profile: UserProfile,
    opportunities: List[Opportunity],
    top_k: int = 10,
) -> List[dict]:
    if not opportunities:
        return []

    user_text = build_user_text(profile)
    opp_texts = [build_opportunity_text(opp) for opp in opportunities]

    corpus = [user_text] + opp_texts
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(corpus)

    user_vector = tfidf_matrix[0]
    opp_vectors = tfidf_matrix[1:]

    scores = cosine_similarity(user_vector, opp_vectors)[0]

    ranked = sorted(
        zip(opportunities, scores),
        key=lambda x: x[1],
        reverse=True,
    )

    return [
        {"opportunity": opp, "score": float(score)}
        for opp, score in ranked[:top_k]
    ]