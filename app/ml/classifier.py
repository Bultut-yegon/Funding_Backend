from typing import Optional

CATEGORY_KEYWORDS = {
    "Scholarships": ["scholarship", "tuition", "student", "undergraduate", "graduate", "academic", "university", "study"],
    "Research Grants": ["research", "grant", "laboratory", "scientific", "publication", "PhD", "postdoc"],
    "Startup Funding": ["startup", "entrepreneur", "venture", "seed", "pitch", "innovation", "founder"],
    "NGO Funding": ["NGO", "nonprofit", "community", "humanitarian", "civil society", "development"],
    "Government Tenders": ["tender", "procurement", "government", "contract", "RFP", "bid", "public sector"],
}

def classify_opportunity(title: str, description: str = "") -> Optional[str]:
    text = f"{title} {description}".lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        scores[category] = sum(1 for kw in keywords if kw.lower() in text)

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "General"
