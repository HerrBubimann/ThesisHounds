FROM python:3.12.16-slim-bookworm

# Apply available Debian security fixes before installing application dependencies.
# The base image includes PAM packages affected by CVE-2025-6020 before deb12u3.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade --yes --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOME=/home/app \
    CONFIG_DIR=/app/config \
    DOCUMENT_STORE_DIR=/tmp/documents \
    LANGSMITH_TRACING=false \
    LANGCHAIN_TRACING_V2=false \
    OTEL_SDK_DISABLED=true

WORKDIR /app
COPY backend/requirements.lock /app/requirements.lock
RUN pip install --no-cache-dir --require-hashes -r requirements.lock \
    && python -m pip uninstall --yes pip \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home app
COPY --chown=10001:10001 backend/app /app/app
COPY --chown=10001:10001 config /app/config
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
