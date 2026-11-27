"""Local text/metadata/OCR scan. Never quotes or logs matching confidential text."""

import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date

from app.security.classification import Classification

TERMS = (
    "sperrvermerk",
    "vertraulich",
    "streng vertraulich",
    "nur für den internen gebrauch",
    "nicht zur veröffentlichung bestimmt",
    "confidential",
    "strictly confidential",
    "restricted",
    "internal use only",
    "non-disclosure agreement",
    "geschäftsgeheimnis",
    "betriebsgeheimnis",
)


@dataclass(frozen=True, repr=False)
class NoticeDetails:
    # Explicit labelled candidates only. These values are protected, never log fields.
    company: str | None = field(default=None, repr=False)
    stated_until: date | None = None
    stated_duration: str | None = None
    audience: str | None = field(default=None, repr=False)
    approval_reference: bool = False
    legal_validity: str = "REQUIRES_AUTHORIZED_REVIEW"


@dataclass(frozen=True)
class Detection:
    detected: bool
    indicators: tuple[str, ...]
    classification: Classification = Classification.RESTRICTED
    # This is a detection result, never legal authorization or expiry-based release.
    requires_authorized_review: bool = True
    details: NoticeDetails = field(default_factory=NoticeDetails, repr=False)


def explicit_details(text: str) -> NoticeDetails:
    def labelled(pattern):
        match = re.search(r"(?im)^\s*(?:" + pattern + r")\s*:\s*([^\n]{1,200})$", text)
        return match.group(1).strip() if match else None

    company = labelled(r"Unternehmen|Firma|Company")
    audience = labelled(r"Zugriffsberechtigt|Berechtigter Personenkreis|Authorized audience")
    duration = labelled(r"Sperrfrist|Geheimhaltungsdauer|Confidentiality period")
    until = labelled(r"Gesperrt bis|Vertraulich bis|Confidential until")
    parsed = None
    if until and re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", until):
        try:
            day, month, year = map(int, until.split("."))
            parsed = date(year, month, day)
        except ValueError:
            pass
    duration = (
        duration
        if duration and re.fullmatch(r"\d{1,3}\s+(?:Jahre?|Monate?|years?|months?)", duration, re.I)
        else None
    )
    return NoticeDetails(
        company,
        parsed,
        duration,
        audience,
        bool(re.search(r"Genehmigung|Zustimmung|approval|permission", text, re.I)),
    )


def detect_sperrvermerk(
    pages: Mapping[int, str] | None = None,
    *,
    metadata: Mapping[str, str] | None = None,
    ocr: Iterable[str] = (),
) -> Detection:
    parts = [*(pages or {}).values(), *(metadata or {}).values(), *ocr]
    original = unicodedata.normalize("NFKC", "\n".join(parts))
    original = "".join(c for c in original if unicodedata.category(c) != "Cf")
    original = re.sub(r"(?<=\w)[-\u00ad]\s*\n\s*(?=\w)", "", original)
    normalized = re.sub(r"\s+", " ", original.casefold())
    matches = tuple(term for term in TERMS if term in normalized)
    return Detection(
        bool(matches), matches, details=explicit_details(original) if matches else NoticeDetails()
    )
