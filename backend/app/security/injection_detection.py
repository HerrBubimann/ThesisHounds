"""Heuristic signals, never a guarantee and never an academic penalty."""

import re
import unicodedata


def detect_injection(text: str) -> list[str]:
    signals = []
    if any(unicodedata.category(char) == "Cf" for char in text):
        signals.append("INVISIBLE_UNICODE")
    normalized = "".join(c for c in text if unicodedata.category(c) != "Cf")
    patterns = {
        "INSTRUCTION_OVERRIDE": r"ignore.{0,40}(instructions|previous)|ignoriere.{0,40}anweisung",
        "GRADE_MANIPULATION": r"(give|assign).{0,30}(grade|score)|vergib.{0,30}(note|punkt)",
        "EXFILTRATION": r"(reveal|print|send).{0,40}(system prompt|secret|password)",
        "TOOL_REQUEST": r"(execute|run).{0,20}(shell|bash|powershell)|tool_call",
        "IDENTITY_MANIPULATION": r"(author|student|name).{0,50}(deserves|better grade)",
    }
    signals.extend(k for k, p in patterns.items() if re.search(p, normalized, re.I | re.S))
    return signals
