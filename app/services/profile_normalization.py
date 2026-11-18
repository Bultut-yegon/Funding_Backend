import re
from typing import Optional


NULL_LITERALS = {"", "null", "none", "undefined", "n/a", "na"}

COUNTRY_ALIASES = {
    "kenyan": "kenya",
    "nigerian": "nigeria",
    "ghanaian": "ghana",
    "usa": "united states",
    "us": "united states",
    "uk": "united kingdom",
}

EDUCATION_ALIASES = {
    "class 8": "primary",
    "grade 8": "primary",
    "primary school": "primary",
    "elementary": "primary",
    "high school": "secondary",
    "secondary school": "secondary",
    "form 4": "secondary",
    "undergraduate": "bachelor",
    "bachelors": "bachelor",
    "bachelor's": "bachelor",
    "masters": "master",
    "master's": "master",
    "postgraduate": "master",
    "doctorate": "phd",
    "doctoral": "phd",
}


def normalize_value(value, *, field: str = "") -> str:
    """Return a canonical, comma-separated profile value."""
    if value is None:
        return ""

    if isinstance(value, (list, tuple, set)):
        value = ",".join(str(item) for item in value)

    terms = []
    for raw_term in re.split(r"[,;\n]+", str(value)):
        term = re.sub(r"\s+", " ", raw_term.strip().lower())
        if term in NULL_LITERALS:
            continue
        if field == "country":
            term = COUNTRY_ALIASES.get(term, term)
        elif field == "education_level":
            term = EDUCATION_ALIASES.get(term, term)
        if term and term not in terms:
            terms.append(term)
    return ", ".join(terms)


def normalized_terms(value: Optional[str], *, field: str = "") -> set[str]:
    return {
        term
        for term in re.split(r"[,;\n]+", normalize_value(value, field=field))
        if term
    }
