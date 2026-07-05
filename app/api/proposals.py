from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from groq import Groq
from app.core.config import settings
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()

class ProposalRequest(BaseModel):
    opportunity_title: str
    opportunity_description: str = ""
    user_background: str

@router.post("/")
async def generate_proposal(
    data: ProposalRequest,
    current_user: User = Depends(get_current_user),
):
    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")

    prompt = f"""You are an expert grant and scholarship proposal writer.

Write a compelling application proposal for the following opportunity:

Opportunity: {data.opportunity_title}
Description: {data.opportunity_description}

Applicant background:
{data.user_background}

Write a professional, persuasive proposal of about 400 words that:
1. Opens with a strong hook
2. Clearly states why the applicant is a perfect fit
3. Explains the impact of receiving this funding
4. Closes with a confident call to action

Write only the proposal text, no headings or labels."""

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
        )
        proposal = response.choices[0].message.content
        return {"proposal": proposal}
    except Exception as e:
        print(f"Groq error: {e}")
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")