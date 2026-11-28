# Empirical model selection

Code review date: 2026-11-28. The assignments in `config/agents.yaml` remain manual
development defaults. `config/model_capabilities.yaml` is empty; no measured model
ranking or automatic approval is supplied. Publisher diversity is not statistical
independence, and registry memory estimates are not hardware measurements.

## Current probe

`app.evaluation.model_benchmark` emits `synthetic-capabilities.v3`.
The same guarded gateway handles eleven task dimensions, schema success/failure,
call duration, observed token completeness and available resource snapshots.
Bounded job parallelism (1–4) respects the existing model semaphore; it does not
grant more inference slots.

```powershell
$env:PYTHONPATH='backend'
.venv\Scripts\python.exe -m app.evaluation.model_benchmark --provider mock --models qwen mistral --repeats 3 --parallelism 2 --output reports/model-capabilities-mock.json
```

Mock mode requires no installed model weights. Reports are explicitly synthetic
and must not be used to rank real Qwen/Mistral/Llama artifacts.
A real `--provider ollama` run additionally requires a configured `local_pilot`,
approved exact model artifacts/digests and registered public test data.
[Actual pilot prerequisites](../setup.md#kontrollierter-public-pilot).
There is no automatic model download or external fallback.

Optional `--stream-metrics` measures time to the first nonempty content fragment.
This is a client-observed proxy, **not exact TTFT**. Token rate uses reported output
tokens and generation duration. `--context-length` may only select a value within
the registered model limits. Missing duration/token/VRAM values remain unknown.
Post-call model snapshots are not per-model physical RAM/VRAM peaks.

## Scientific interpretation

| Dimension | Available technical evidence / remaining requirement |
|---|---|
| Scientific text, methodology, argumentation, German | Structured synthetic responses; expert correctness/usefulness labels still needed |
| Formal criteria and sources | Scoped text/metadata checks; institutional criteria and semantic source support require validation |
| Structured output | Actual schema adherence, separate from content quality |
| Tool calling | Unauthorized execution stays blocked; legitimate tool-calling ability remains unmeasured |
| Injection and evidence | Technical boundaries and literal quotations; broad model-specific attack/interpretation quality not established |
| Resources | Actual reported durations/tokens/snapshots; separate accepted inference-host instrumentation needed for peaks |

Record artifact revision, digest, quantization, dataset/prompt hashes, runtime,
hardware, cold/warm loading and all failures. Use disjoint development/test cases,
blinded expert adjudication and equalized budgets before claiming academic benefit.
Only reviewed, nonmock, exact-digest capability evidence may influence routing.
No missing quality score or human time-savings measurement is replaced by zero.

[Benchmark protocol](../evaluation/model_benchmarks.md) ·
[Routing](../architecture/model_routing.md) · [Current validation](../validation.md)
