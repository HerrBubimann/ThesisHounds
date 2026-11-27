FROM ollama/ollama:0.40.18

# Pre-owned directory initializes a NEW named volume for an unprivileged runtime user.
ENV HOME=/home/ollama \
    OLLAMA_MODELS=/home/ollama/.ollama/models
RUN mkdir -p /home/ollama/.ollama/models \
    && chown -R 10001:10001 /home/ollama
USER 10001:10001
