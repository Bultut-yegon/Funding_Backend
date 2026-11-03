import json
from datetime import datetime
from groq import Groq
from app.core.config import settings

VALID_CATEGORIES = [
    "Scholarships",
    "Research Grants",
    "Startup Funding",
    "NGO Funding",
    "Government Tenders",
    "General",
]


def enrich_opportunity(title: str, description: str) -> dict:
    """
    Classifies an opportunity and extracts eligibility + deadline using Groq,
    reading the actual meaning of the text instead of counting keywords.
    Falls back to safe defaults if the AI call fails for any reason.
    """
    fallback = {"category": "General", "eligibility": None, "deadline": None, "country": None, "failed": True}

    if not settings.GROQ_API_KEY:
        return fallback

    prompt = f"""You are analyzing a funding opportunity listing (scholarship, grant, tender, or fellowship).

TITLE: {title}
DESCRIPTION: {description}

Respond in this exact JSON format with no extra text:
{{
  "category": "<one of: Scholarships, Research Grants, Startup Funding, NGO Funding, Government Tenders, General>",
  "eligibility": "<a short 1-3 sentence plain-English summary of who can apply and what is required, based only on what the description states. If no eligibility information is present, use null>",
  "deadline": "<the application deadline as YYYY-MM-DD if a specific date is stated in the text, otherwise null>"
  "country": "<the specific country this opportunity is for, e.g. 'Kenya', if one is clearly stated or strongly implied. If open to a region, use that region, e.g. 'East Africa' or 'Sub-Saharan Africa'. If open worldwide with no restriction, use 'Global'. If not stated or genuinely unclear, use null>"
}}"""

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            response_format={"type": "json_object"},
        )
        choice = response.choices[0]
        text = choice.message.content or ""
        if not text.strip():
            print("Enrichment error: empty response (finish_reason={choice.finish_reason}) for: {title[:60]}")
            return fallback
        start = text.find("{")
        end = text.rfind("}") + 1
        result = json.loads(text[start:end])

        category = result.get("category")
        if category not in VALID_CATEGORIES:
            category = "General"

        deadline = None
        raw_deadline = result.get("deadline")
        if raw_deadline:
            try:
                deadline = datetime.strptime(raw_deadline, "%Y-%m-%d")
            except (ValueError, TypeError):
                deadline = None

        return {
            "category": category,
            "eligibility": result.get("eligibility") or None,
            "deadline": deadline,
            "country": result.get("country") or None,
            "failed": False,
        }
    except Exception as e:
        print(f"Enrichment error: {e}")
        return fallback