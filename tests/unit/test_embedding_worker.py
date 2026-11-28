import io
import json
import sys
from types import SimpleNamespace

import pytest
from app.services import embedding_worker


@pytest.mark.parametrize("model_id", ["multilingual-e5-small", "qwen3-embedding-06b", "bge-m3"])
def test_fixed_worker_uses_local_safe_weights_and_model_specific_queries(
    monkeypatch, capsys, model_id
):
    observed = {}

    class Model:
        def __init__(self, root, **kwargs):
            observed.update(kwargs)
            assert root == "SYNTHETIC_LOCAL_PATH"

        def encode(self, texts, **kwargs):
            observed["texts"] = texts
            assert self.max_seq_length == 512
            assert kwargs["batch_size"] == 8 and kwargs["normalize_embeddings"]
            return SimpleNamespace(tolist=lambda: [[1.0], [1.0]])

    monkeypatch.setitem(
        sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=Model)
    )
    monkeypatch.setattr(sys, "addaudithook", lambda hook: observed.update(audit_hook=hook))
    raw = json.dumps(
        {
            "root": "SYNTHETIC_LOCAL_PATH",
            "id": model_id,
            "queries": ["Methodik"],
            "passages": ["Original evidence"],
        }
    ).encode()
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(buffer=io.BytesIO(raw)))
    embedding_worker.main()
    assert json.loads(capsys.readouterr().out)["vectors"] == [[1.0], [1.0]]
    assert observed["device"] == "cpu" and observed["local_files_only"]
    assert not observed["trust_remote_code"] and not observed["token"]
    assert observed["model_kwargs"] == {"use_safetensors": True}
    assert observed["audit_hook"] is embedding_worker.deny_network_and_process
    if model_id == "multilingual-e5-small":
        assert observed["texts"] == ["query: Methodik", "passage: Original evidence"]
    elif model_id == "qwen3-embedding-06b":
        assert observed["texts"][0].startswith("Instruct: ")
        assert observed["texts"][1] == "Original evidence"
    else:
        assert observed["texts"] == ["Methodik", "Original evidence"]


@pytest.mark.parametrize(
    "event",
    ["socket.connect", "socket.getaddrinfo", "subprocess.Popen", "os.system", "os.posix_spawn"],
)
def test_worker_blocks_network_and_child_process_audit_events(event):
    with pytest.raises(PermissionError, match="DENIED"):
        embedding_worker.deny_network_and_process(event, ())
    embedding_worker.deny_network_and_process("open", ())


def test_worker_rejects_unbounded_passage_count_before_loading_runtime(monkeypatch):
    raw = json.dumps({"queries": ["Methodik"], "passages": ["x"] * 257}).encode()
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(buffer=io.BytesIO(raw)))
    with pytest.raises(ValueError, match="LIMIT"):
        embedding_worker.main()
