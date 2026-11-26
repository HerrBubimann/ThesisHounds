# ADR 002: Explicit university inference, closed public research and scoring

Date: 2026-11-26. Status: accepted for MVP; university deployment requires IT approval.

Decision: retain local HTTP defaults. University HTTPS endpoints need an exact
operator-managed host allowlist, normal certificate validation, optional custom CA
and optional bearer authentication. Credentials remain server-side. Redirects and
environment proxy inheritance stay disabled. A separate Compose stack joins an
externally administered university network; IT must enforce endpoint-only egress,
VPN routing and restricted ingress. The hostname allowlist cannot prove network
ownership or prevent DNS rebinding by itself.

No cloud provider or automatic fallback is implemented. Azure is an option to assess
later (residency, tenant controls, contracts, logging, egress, identity and costs), not
an approved operating mode. Configure Ollama itself with cloud disabled; rejecting
cloud tag names alone cannot detect a malicious server or misleading model alias.

HF metadata is optional for existing registry entries. New HF entries cannot be
enabled until provenance, artifact hash, pinned revision, license, technical
compatibility and security review are documented. These operator attestations are
not cryptographic proof; artifact bytes must be checked separately before import.
No remote model code, download endpoint or conversion executor is added.

Public research is fail-closed, including for queries labeled PUBLIC by callers.
No production provider client exists. Enabling public research or AI scoring via
environment fails startup instead of silently bypassing unavailable controls.
`research.yaml` describes the future contract and grants no permission. Internal
research is currently limited to the current synthetic document supplied to review;
the internal-research flag reserves an extension and creates no cross-document index.

After privacy approval, build RES-1 as a separate service without document-store
mounts or credentials, with structured provider allowlists, reviewed query objects,
rate/size/time limits, sanitized audits and adversarial tests. Heuristic PII removal
does not establish that queries are safe. No research capability is needed for core
local assessment. Scoring awaits official catalogs/scales; no target-grade optimizer
is introduced before defensible qualitative constraints have been agreed.
