"""ThesisHounds backend."""

import os

# Enforce local observability even if inherited host variables enable external tracing.
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["OTEL_SDK_DISABLED"] = "true"
