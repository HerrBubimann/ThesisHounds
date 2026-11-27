"""Heuristic signals, never a guarantee and never an academic penalty."""

import re
import unicodedata


def normalize_for_detection(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKC", text) if unicodedata.category(c) != "Cf"
    )


def academic_example(text: str) -> bool:
    # Context is an alternative explanation, never an authorization or an all-clear.
    return bool(
        re.search(
            r"(?:Angriffsbeispiel|Beispiel eines Angriffs|attack example|"
            r"quoted attack|zitierte Angriff|untersuchen.{0,30}Prompt.Injection)",
            text,
            re.I,
        )
    )


def detect_injection(text: str) -> list[str]:
    signals = []
    if any(unicodedata.category(char) == "Cf" for char in text):
        signals.append("INVISIBLE_UNICODE")
    normalized = normalize_for_detection(text)
    patterns = {
        "INSTRUCTION_OVERRIDE": r"ignore.{0,40}(instructions|previous)|ignoriere.{0,40}anweisung",
        "GRADE_MANIPULATION": r"(give|assign).{0,30}(grade|score)|vergib.{0,30}(note|punkt)",
        "EXFILTRATION": r"(reveal|print|send).{0,40}(system prompt|secret|password)",
        "TOOL_REQUEST": r"(execute|run).{0,20}(shell|bash|powershell)|tool_call",
        "IDENTITY_MANIPULATION": r"(author|student|name).{0,50}(deserves|better grade)",
        "EXTERNAL_TRANSFER": r"(send|upload|sende|übertrag).{0,100}"
        r"(api|https?://|openai|anthropic|gemini|cloud)",
        "CLASSIFICATION_DOWNGRADE": r"(classif|klassifiz|declassif).{0,60}"
        r"(public|öffentlich|lower|herab)",
        "ENCODED_EXFILTRATION": r"(base64|hex|kodier|encod).{0,80}(send|upload|sende|api)",
        "CROSS_ANALYSIS_ACCESS": r"(other|fremd|andere).{0,40}(thes[ie]s|arbeit|analyse|document)",
        "ROLE_SPOOFING": r"<\|(?:im_start|system|assistant)\|>|\[INST\]|"
        r"(?:^|\n)\s*(?:SYSTEM|DEVELOPER)\s*:",
        "CRITERION_OVERRIDE": r"(?:ignore|ignoriere|überspringe|ersetze).{0,50}"
        r"(?:criteria|kriterien|rubric|kritikpunkte)",
        "MODEL_SWITCH": r"(?:switch|use|wechsel|verwende).{0,35}"
        r"(?:external model|externes modell|gpt-|claude|openai)",
        "AGENT_CREATION": r"(?:create|spawn|erstelle|erzeuge).{0,35}(?:agent|subagent|spezialist)",
        "ENCODED_PAYLOAD": r"(?:base64|hex)(?:[- ]?(?:decode|dekodier|payload))|"
        r"\\x[0-9a-f]{2}(?:\\x[0-9a-f]{2}){5}",
    }
    signals.extend(k for k, p in patterns.items() if re.search(p, normalized, re.I | re.S))
    return signals


def requires_quarantine(text: str) -> bool:
    signals = set(detect_injection(text)) - {"INVISIBLE_UNICODE", "ENCODED_PAYLOAD"}
    return bool(signals) and not academic_example(text)
