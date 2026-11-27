FROM python:3.12.16-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOME=/home/app \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    PYTHONPATH=/app

WORKDIR /app
COPY frontend/requirements.lock /app/requirements.lock
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --require-hashes -r requirements.lock \
    && python -m pip uninstall --yes pip \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home app
COPY --chown=10001:10001 frontend /app/frontend
COPY --chown=10001:10001 frontend/.streamlit /app/.streamlit
USER 10001:10001
EXPOSE 8501
CMD ["streamlit", "run", "frontend/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
