# Empirical model selection

Date: 2026-11-26. Current assignments in `agents.yaml` are development defaults, not
validated specialization. Existing registry estimates are not measurements. Candidate
families include Qwen/Alibaba, Mistral/Mistral AI, Llama/Meta and Gemma/Google; exact
revision, quantization, runtime compatibility, license and hardware fit must be
approved individually. Different publishers do not imply statistical independence.

The runnable initial probe uses the existing gateway and identical server-owned
synthetic cases. It measures JSON schema validity, observed tokens (with an explicit
completeness flag), elapsed call time and a backend resource snapshot. It records
model configuration and test-case hash. Human quality, tool-calling and VRAM peak
metrics are null, not zero. It makes no automatic task assignment or model ranking.

```powershell
$env:PYTHONPATH = 'backend'
$env:CONFIG_DIR = 'config'
$env:OLLAMA_BASE_URL = 'http://localhost:11434'
.\.venv\Scripts\python.exe -m app.evaluation.model_benchmark --models qwen mistral --repeats 3
```

Model tags must already be installed. No model download or external inference occurs.
Capture JSON in an ignored `reports/` file if needed. CI uses a synthetic mock provider;
passing those tests only validates plumbing, never real model capabilities. Record
installed model digest, Ollama version, OS, CPU/GPU, RAM/VRAM, cold/warm loading,
configuration and prompts alongside real benchmark runs before comparing results.

| Capability | Initial probe / required extension |
|---|---|
| German scientific analysis, methodology, contradictions | Synthetic prompts present; expert quality annotations pending |
| Evidence and complex criteria | Exact quote validation in assessment flow; expand blinded reference cases |
| Sources | Unknown-source case; no real provider or content verification |
| Structured JSON | Actual schema validation; track errors separately from content quality |
| Tool calling | Intentionally unmeasured; MVP has no model tool execution |
| Injection robustness | Instruction-attack prompt present; adversarial success needs human scoring and broad corpus |
| Error rate / latency / tokens | Recorded per call; aggregate by model and repeated case, account for failures |
| RAM / VRAM | Backend snapshot only; separate time-sampled inference-host telemetry needed |

Expand cases for grammatical variation, long German documents, missing evidence,
conflicting numbers, invented citations, indirect injection and identity counterfactuals.
Use disjoint development/test sets and expert adjudication; do not optimize on final
test cases. Compare one model, homogeneous agents, heterogeneous agents, cross-model
verification and eventually approved research under equal input/output budgets.
Repeat/rotate ordering and report quality-resource tradeoffs, confidence intervals,
failure counts and unavailable metrics. Sources S1/S2/S6–S8 motivate this caution;
none supplies model-specific performance results for ThesisHounds.
