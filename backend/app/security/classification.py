"""Server-owned labels. Unknown, absent and malformed labels are RESTRICTED."""

from enum import StrEnum


class Classification(StrEnum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


def classify(value: object = None) -> Classification:
    try:
        return Classification(value)
    except (ValueError, TypeError):
        return Classification.RESTRICTED


def combine(*values: object) -> Classification:
    order = list(Classification)
    return max((classify(v) for v in values), key=order.index, default=Classification.RESTRICTED)
