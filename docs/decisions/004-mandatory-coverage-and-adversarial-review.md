# ADR 004: Mandatory criterion coverage, bounded supplements and adversarial review

Status: accepted for synthetic engineering MVP, 2026-11-26. OFF-2/3/4.

Problem: a planner can overlook required criteria, and a confirming second model
can repeat unjustified criticism. Additional agents are not inherently more reliable.

Decision: retain a server-owned mandatory criterion loop and structural coverage
check. Create topic supplements only through the existing guarded Factory/Registry
from a small fixed template set. Keep supplements separate. In E, another model
actively attempts to refute each finding; at most two independent-manufacturer
attempts share the existing budgets. Recheck literal evidence after challenges.

Consequences: original findings and dissent remain visible. MODEL_SUPPORTED is a
model judgment, not proof; a later supporter never erases an earlier challenge.
Proposed corrections require human review. More calls cost resources and can still
produce correlated errors. Comparative benefit remains an empirical research question.
