"""Local text structure with exact source spans. No PDF/OCR/layout inference or I/O."""

import re
from dataclasses import asdict, dataclass

HEADINGS = re.compile(
    r"^(?:(?P<number>\d+(?:\.\d+)*)\s+)?(?P<title>"
    r"Einleitung|Forschungsfrage|Methodik|Methode|Ergebnisse|Diskussion|Fazit|"
    r"Zusammenfassung|Literaturverzeichnis|Literatur|References|Conclusion|Introduction)\b[:.]?",
    re.I,
)


@dataclass(frozen=True)
class TextBlock:
    id: str
    page: int
    start: int
    end: int
    text: str
    chapter: str | None
    kind: str = "PARAGRAPH"
    reliable: bool = True


@dataclass(frozen=True)
class DocumentStructure:
    analysis_id: str
    classification: str
    blocks: tuple[TextBlock, ...]
    sections: tuple[dict, ...]
    warnings: tuple[str, ...]
    quotations: tuple[dict, ...] = ()

    def locate(self, page: int | None, quote: str):
        return next((b for b in self.blocks if b.page == page and quote and quote in b.text), None)

    def related(self, first: str, second: str) -> dict:
        def selected(title):
            return [
                asdict(b)
                for b in self.blocks
                if b.chapter and title.casefold() in b.chapter.casefold()
            ]

        return {
            "first": selected(first),
            "second": selected(second),
            "semantic_relation_verified": False,
        }


def structure_document(document) -> DocumentStructure:
    blocks, sections, chapter = [], [], None
    warnings = ["TEXT_ONLY: tables, figures, formulas and code have no verified visual extraction"]
    for page, text in sorted(document.pages.items()):
        for index, match in enumerate(re.finditer(r"[^\n]+(?:\n(?!\s*\n)[^\n]+)*", text)):
            value = match.group()
            heading = HEADINGS.match(value)
            numbered = re.match(r"^(\d+(?:\.\d+)*)\s+([^\n]{1,100})(?:\n|$)", value)
            if heading or numbered:
                chapter = heading.group("title") if heading else numbered.group(2)
                number = heading.group("number") if heading else numbered.group(1)
                sections.append(
                    {
                        "title": chapter,
                        "level": (number or "").count(".") + 1,
                        "page": page,
                        "start": match.start(),
                    }
                )
            kind, reliable = "PARAGRAPH", True
            if re.match(r"\s*(Tabelle|Table)\s+\d", value, re.I):
                kind, reliable = "TABLE", False
            elif re.match(r"\s*(Abbildung|Figure|Abb\.)\s*\d", value, re.I):
                kind, reliable = "FIGURE", False
            elif "```" in value:
                kind, reliable = "CODE", False
            elif "$" in value or "\\begin{equation}" in value:
                kind, reliable = "FORMULA", False
            elif chapter and chapter.casefold() in {
                "literaturverzeichnis",
                "literatur",
                "references",
            }:
                kind = "BIBLIOGRAPHY"
            blocks.append(
                TextBlock(
                    f"p{page}-b{index}",
                    page,
                    match.start(),
                    match.end(),
                    value,
                    chapter,
                    kind,
                    reliable,
                )
            )
    quotations = tuple(
        {
            "page": page,
            "start": match.start(),
            "end": match.end(),
            "text": match.group(),
            "bibliographic_support_verified": False,
        }
        for page, text in sorted(document.pages.items())
        for match in re.finditer(r'„[^“\n]{1,2000}“|“[^”\n]{1,2000}”|"[^"\n]{1,2000}"', text)
    )
    return DocumentStructure(
        document.analysis_id,
        document.classification,
        tuple(blocks),
        tuple(sections),
        tuple(warnings),
        quotations,
    )
