"""Mosbach-first resolution. Priority never silently disposes of a conflicting rule."""

import hashlib
import json
from datetime import date
from pathlib import Path

import yaml

from app.knowledge.schemas import Hierarchy, InstitutionalProfile, SourceDocument
from app.security.classification import classify, combine


def fingerprint(model) -> str:
    return hashlib.sha256(
        json.dumps(model.model_dump(mode="json"), sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


class InstitutionalRegistry:
    def __init__(self, sources, profiles, approvals=()):
        self.sources = {s.id: s.model_copy(deep=True) for s in sources}
        self.profiles = {p.id: p.model_copy(deep=True) for p in profiles}
        self.approvals = {a.subject_id: a.model_copy(deep=True) for a in approvals}
        if len(self.sources) != len(sources) or len(self.profiles) != len(profiles):
            raise ValueError("DUPLICATE_KNOWLEDGE_ID")
        if len(self.approvals) != len(approvals):
            raise ValueError("DUPLICATE_APPROVAL")

    @classmethod
    def load(cls, root: Path):
        sources_path = root / "data_science_ai" / "sources.yaml"
        if not sources_path.exists():
            return cls([], [])
        sources = [
            SourceDocument.model_validate(s)
            for s in yaml.safe_load(sources_path.read_text("utf-8"))["sources"]
        ]
        profiles = [
            InstitutionalProfile.model_validate(yaml.safe_load(path.read_text("utf-8")))
            for path in sorted(root.glob("*/profiles/*.yaml"))
        ]
        # Shipping config cannot grant approval. Operator-reviewed approvals are separate,
        # and no production approval store is connected in this DEVELOPMENT release.
        return cls(sources, profiles)

    def approved(self, subject) -> bool:
        approval = self.approvals.get(subject.id)
        return bool(
            subject.release == "APPROVED"
            and approval
            and approval.content_sha256 == fingerprint(subject)
            and (
                not isinstance(subject, SourceDocument)
                or (
                    subject.sha256
                    and subject.retrieved_at
                    and subject.valid_from
                    and (subject.classification != "PUBLIC" or approval.public_provenance_confirmed)
                )
            )
        )

    def resolve(self, program, cohort, work_type, *, as_of=None, clearance="PUBLIC") -> dict:
        as_of = as_of or date.today()
        # Private institutional stores have no admitted identity/storage adapter yet.
        # An unknown permission label must never become RESTRICTED clearance.
        level = classify(clearance)
        if level != "PUBLIC":
            return {
                "status": "MANUAL_REVIEW_REQUIRED",
                "reason": "PRIVATE_LIBRARY_NOT_RELEASED",
                "profile": None,
                "rules": [],
                "sources": [],
                "conflicts": [],
            }
        profiles = [
            p
            for p in self.profiles.values()
            if (p.program, p.cohort, p.work_type) == (program, cohort, work_type)
        ]
        # Never pick a "latest" version implicitly; two versions require explicit reconciliation.
        profiles = [
            p
            for p in profiles
            if all(
                r.source_id in self.sources
                and combine(self.sources[r.source_id].classification, level) == level
                for r in p.rules
            )
        ]
        if len(profiles) != 1:
            return {
                "status": "MANUAL_REVIEW_REQUIRED",
                "reason": "MISSING_OR_AMBIGUOUS_PROFILE",
                "profile": None,
                "rules": [],
                "sources": [],
                "conflicts": [],
            }
        profile = profiles[0]
        rows, used, conflicts, groups = [], {}, [], {}
        for rule in profile.rules:
            source = self.sources[rule.source_id]
            applicable = (
                source.campus in {"Mosbach", "DHBW"}
                and source.hierarchy != Hierarchy.OTHER_CAMPUS
                and (program in source.programs or "all" in source.programs)
                and (cohort in source.cohorts or not source.cohorts)
                and work_type in source.work_types
                and source.valid_from is not None
                and source.valid_from <= as_of
                and (source.valid_until is None or as_of <= source.valid_until)
            )
            delegated = source.delegated_by is None or (
                source.delegated_by in self.sources
                and self.approved(self.sources[source.delegated_by])
                and program in self.sources[source.delegated_by].programs
                and cohort in self.sources[source.delegated_by].cohorts
                and work_type in self.sources[source.delegated_by].work_types
            )
            active = (
                applicable
                and delegated
                and self.approved(source)
                and self.approved(profile)
                and rule.release == "APPROVED"
                and source.binding == "BINDING"
            )
            rows.append(
                {
                    **rule.model_dump(mode="json"),
                    "active": bool(active),
                    "hierarchy": int(source.hierarchy),
                    "status": "ACTIVE" if active else "MANUAL_REVIEW_REQUIRED",
                }
            )
            used[source.id] = source.model_dump(mode="json")
            if rule.conflict_key:
                groups.setdefault(rule.conflict_key, []).append(rule)
        for key, group in groups.items():
            if len({r.conflict_value for r in group}) > 1:
                approval = self.approvals.get(profile.id)
                selected = approval.resolved_conflicts.get(key) if approval else None
                legal = {
                    r.id
                    for r in group
                    if self.sources[r.source_id].hierarchy == Hierarchy.EXAMINATION_LAW
                }
                valid_selection = (
                    self.approved(profile)
                    and selected in {r.id for r in group}
                    and (not legal or selected in legal)
                )
                conflicts.append(
                    {
                        "key": key,
                        "rule_ids": [r.id for r in group],
                        "status": "HUMAN_RESOLVED" if valid_selection else "OPEN",
                        "selected_rule": selected if valid_selection else None,
                    }
                )
                for row in rows:
                    if row["id"] in {r.id for r in group}:
                        row["active"] = bool(
                            row["active"] and valid_selection and row["id"] == selected
                        )
                        row["status"] = "ACTIVE" if row["active"] else "MANUAL_REVIEW_REQUIRED"
        rows.sort(key=lambda row: (row["hierarchy"], row["id"]))
        return {
            "status": "ACTIVE"
            if any(r["active"] for r in rows) and not any(c["status"] == "OPEN" for c in conflicts)
            else "MANUAL_REVIEW_REQUIRED",
            "profile": profile.model_dump(mode="json"),
            "rules": rows,
            "sources": list(used.values()),
            "conflicts": conflicts,
            "classification": combine(
                *(s.classification for s in [self.sources[k] for k in used])
            ).value,
        }
