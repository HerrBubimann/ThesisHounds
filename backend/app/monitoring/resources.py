import time

import psutil


def sample_resources() -> dict:
    memory = psutil.virtual_memory()
    return {
        "timestamp": time.time(),
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_total_bytes": memory.total,
        "ram_available_bytes": memory.available,
        "backend_rss_bytes": psutil.Process().memory_info().rss,
        "scope": "OS-visible system and backend process; not per-Ollama CPU/RAM",
    }


def completion_metrics(response):
    return {
        "provider_total_seconds": response.total_duration_seconds,
        "model_load_seconds": response.load_duration_seconds,
        "generation_seconds": response.generation_duration_seconds,
        "prompt_eval_seconds": response.prompt_duration_seconds,
        "output_tokens": response.output_tokens,
        "input_tokens": response.input_tokens,
        "tokens_per_second": response.output_tokens / response.generation_duration_seconds
        if response.output_tokens is not None and response.generation_duration_seconds
        else None,
        "first_content_chunk_seconds": response.first_content_seconds,
        "ttft_seconds": None,
        "first_content_scope": "CLIENT_FIRST_NONEMPTY_CONTENT_CHUNK_NOT_EXACT_TOKEN_BOUNDARY",
        "timing_source": "PROVIDER_REPORTED_DURATIONS_AND_OPTIONAL_CLIENT_STREAM_OBSERVATION",
    }


def loaded_vram_bytes(models):
    values = [m.get("vram_bytes") for m in models]
    return sum(values) if all(type(v) is int and v >= 0 for v in values) else None
