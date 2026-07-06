from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from groq import Groq
from app.core.config import settings
from app.core.security import get_current_user
from app.models.user import User
from app.models.profile import UserProfile
from app.db.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

class PredictRequest(BaseModel):
    opportunity_title: str
    opportunity_description: str = ""
    opportunity_category: str = ""

@router.post("/")
async def predict_success(
    data: PredictRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(status_code=400, detail="Complete your profile first")

    prompt = f"""You are an expert funding advisor. Analyze how likely this applicant is to succeed.

OPPORTUNITY:
Title: {data.opportunity_title}
Description: {data.opportunity_description}
Category: {data.opportunity_category}

APPLICANT PROFILE:
Education: {profile.education_level}
Interests: {profile.interests}
Industry: {profile.industry}
Country: {profile.country}
Skills: {profile.skills}

Respond in this exact JSON format with no extra text:
{{
  "score": <number 0-100>,
  "verdict": "<Strong Match|Good Match|Possible Match|Weak Match>",
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "gaps": ["<gap 1>", "<gap 2>"],
  "tips": ["<tip 1>", "<tip 2>", "<tip 3>"]
}}"""

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        import json
        text = response.choices[0].message.content
        # Extract JSON from response
        start = text.find("{")
        end = text.rfind("}") + 1
        result = json.loads(text[start:end])
        return result
    except Exception as e:
        print(f"Predictor error: {e}")
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")
