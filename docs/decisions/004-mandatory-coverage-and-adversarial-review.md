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

## Implementation follow-up, 2026-11-28

The fixed-template restriction above is the historical baseline. Current D/E assessment
planning defaults to a bounded semantic proposal with APPLIED-method original evidence;
regex templates remain an explicit comparison baseline. Existing rights, mandatory
coverage and budgets still constrain every specialist. No scientific benefit is inferred
from the additional agents. [Current contract](../architecture/semantic_adaptive_planning.md).
