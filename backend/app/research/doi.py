"""One conservative DOI identity function; it performs no lookup or network request."""

import re
from urllib.parse import unquote, urlsplit

DOI = re.compile(r"\b10\.\d{4,9}(?:/|%2f)[-._;()/:A-Z0-9%]+", re.I)


def normalize_doi(value: object) -> str:
    """Preserve ambiguous suffix punctuation: a DOI may legitimately end in it.

    Only explicit enclosing angle brackets are presentation syntax. URL query and
    fragment delimiters are parsed before percent decoding, so encoded suffix
    characters survive. Internal whitespace is rejected rather than silently joined.
    """
    if not isinstance(value, str):
        return ""
    text = value.strip()
    if text.startswith("<") and text.endswith(">"):
        text = text[1:-1].strip()
    if text.casefold().startswith("doi:"):
        text = text[4:].strip()
    encoded = bool(re.match(r"^10\.\d{4,9}%2f", text, re.I))
    if text.casefold().startswith(("http://", "https://")):
        try:
            url = urlsplit(text)
            if url.hostname not in {"doi.org", "dx.doi.org"} or url.username or url.password:
                return ""
            text = url.path.removeprefix("/")
            encoded = True
        except ValueError:
            return ""
    try:
        text = (unquote(text, errors="strict") if encoded else text).casefold()
    except UnicodeError:
        return ""
    if re.search(r"[\s\x00-\x1f\x7f]", text) or not re.fullmatch(r"10\.\d{4,9}/.+", text):
        return ""
    return text
