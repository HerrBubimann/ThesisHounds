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
