"""Checksum-validated ISBN identity, without catalog lookup or network access."""

import re


def normalize_isbn(value: object) -> str:
    """Return canonical ISBN-13; an invalid checksum never becomes an identifier."""
    if not isinstance(value, str):
        return ""
    text = re.sub(r"^ISBN(?:-1[03])?\s*:?\s*", "", value.strip(), flags=re.I)
    text = re.sub(r"[ -]", "", text).upper()
    if re.fullmatch(r"[0-9]{9}[0-9X]", text):
        if sum((10 - i) * (10 if ch == "X" else int(ch)) for i, ch in enumerate(text)) % 11:
            return ""
        text = "978" + text[:9]
        text += str((-sum(int(ch) * (1 if i % 2 == 0 else 3) for i, ch in enumerate(text))) % 10)
    if not re.fullmatch(r"97[89][0-9]{10}", text):
        return ""
    return (
        text
        if sum(int(ch) * (1 if i % 2 == 0 else 3) for i, ch in enumerate(text)) % 10 == 0
        else ""
    )
