import re
from datetime import datetime


_DEADLINE_RE = re.compile(
    r"Deadline:\s*([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})",
    re.IGNORECASE,
)


def stated_deadline(text: str | None) -> datetime | None:
    """Parse a deadline stated in the first part of an opportunity description."""
    if not text:
        return None

    match = _DEADLINE_RE.search(text[:200])
    if not match:
        return None

    month, day, year = match.groups()
    for fmt in ("%B %d %Y", "%b %d %Y"):
        try:
            return datetime.strptime(f"{month} {day} {year}", fmt)
        except ValueError:
            continue
    return None


def start_of_today() -> datetime:
    return datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)


def is_expired(deadline: datetime | None) -> bool:
    if deadline is None:
        return False
    return deadline < start_of_today()
