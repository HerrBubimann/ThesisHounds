# Controlled model provisioning

Security follow-up 2026-11-27: `compose.provision.yaml` is now a standalone project
with a dedicated online network and no processing services. Downloads require
reviewed license/security/model approval, version, weights origin and a complete
`expected_digest`. An in-use model volume is rejected. A separate unprivileged
helper checks `/api/tags` via the provisioner's loopback before success is reported.
No actual download approval is shipped. These guards do not authorize real documents.
The router/provider also reject a changed configured digest before sending content.

The registry now accepts an optional `huggingface` object. Existing Ollama entries
continue to work and are not retroactively claimed to be university-approved.
Candidate entries must be `enabled: false`. Required artifact metadata: repository,
40-character commit revision, license, format (GGUF or safetensors), quantization,
SHA-256 and language list. Context, manufacturer, memory, privacy, roles and provider
remain on the enclosing model. Structured-output, tool-calling and reasoning claims
may be `null` until measured. No Gemma model or additional manufacturer is implicitly
approved; select exact candidates after resources and licenses are known.

1. Model steward selects an exact publisher/repository/revision. Record original
   and derivative model licenses, conversion provenance, tokenizer and model card.
2. Download only reviewed artifacts in a separate provisioning environment. Verify
   SHA-256 against a trusted manifest; scan files and dependencies. Do not unpickle
   arbitrary weights, execute repository scripts or enable `trust_remote_code`.
3. Check architecture/tokenizer/template support against the installed Ollama
   version. A GGUF extension alone does not establish compatibility. Some supported
   architectures can import safetensors; unsupported ones cannot. Conversion via a
   pinned reviewed llama.cpp toolchain is an operator-controlled, isolated step;
   record input/output hashes, quantization and tool versions. The app runs no converters.
4. In a disconnected staging deployment, manually create a reviewed Modelfile using
   a local artifact path, import with `ollama create`, inspect the resulting model
   and test JSON/schema adherence, German analysis, evidence and injection resistance.
   Do not use model-provided system templates without reviewing them.
5. Record results, provenance/license/security reviewers and date. Only then set
   `approval: APPROVED`, `ollama_compatible: true`, all three `*_reviewed` flags,
   `reviewed_by`, `review_date`, and enable the model in operator-controlled YAML.
   The registry rejects enabled HF artifacts with missing approval fields.
6. Verify installed digest and operational limits, deploy through change review;
   retain prior known-good registry/artifact for rollback. Re-review any new revision.

This prepares provisioning; it does not grant a license, download a model or verify
artifact bytes. No Hugging Face credentials or remote model code enter the runtime.

Sources checked 2026-11-26: [Ollama import](https://docs.ollama.com/import),
[Hugging Face security](https://huggingface.co/docs/hub/en/security-pickle).
