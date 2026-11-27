import pytest
from app.config import Settings
from pydantic import ValidationError


@pytest.mark.parametrize(
    "url",
    [
        "https://api.example.com",
        "http://external:11434",
        "http://ollama/api",
        "http://user:pass@ollama:11434",
        "http://ollama?query=x",
    ],
)
def test_reject_external_or_credentialed_llm_url(url) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, ollama_base_url=url)


@pytest.mark.parametrize("model", ["model:cloud", "model-cloud", "https://external/model", "   "])
def test_reject_remote_model(model) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, llm_model=model)


@pytest.mark.parametrize("field", ["llm_connect_timeout", "llm_status_timeout", "llm_chat_timeout"])
def test_reject_nonpositive_timeouts(field) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{field: 0})
