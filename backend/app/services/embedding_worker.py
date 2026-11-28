"""Fixed CPU embedding worker. No arbitrary code, hosted inference or artifact download."""

import json
import sys


def deny_network_and_process(event, args):
    if event.startswith("socket.") or event in {"subprocess.Popen", "os.system", "os.posix_spawn"}:
        raise PermissionError("EMBEDDING_WORKER_NETWORK_OR_PROCESS_DENIED")


def main():
    payload = json.loads(sys.stdin.buffer.read(2_000_001))
    if len(payload.get("queries", [])) > 20 or len(payload.get("passages", [])) > 256:
        raise ValueError("EMBEDDING_INPUT_LIMIT")
    sys.addaudithook(deny_network_and_process)
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(
        payload["root"],
        device="cpu",
        local_files_only=True,
        trust_remote_code=False,
        token=False,
        model_kwargs={"use_safetensors": True},
    )
    model.max_seq_length = 512  # Same bounded passage budget for every comparison model.
    queries, passages = payload["queries"], payload["passages"]
    if payload["id"] == "multilingual-e5-small":
        queries = ["query: " + q for q in queries]
        passages = ["passage: " + p for p in passages]
    elif payload["id"] == "qwen3-embedding-06b":
        queries = [
            "Instruct: Retrieve original scientific evidence for the query.\nQuery: " + q
            for q in queries
        ]
    elif payload["id"] != "bge-m3":
        raise ValueError("EMBEDDING_MODEL_DENIED")
    vectors = model.encode(
        [*queries, *passages], batch_size=8, normalize_embeddings=True, show_progress_bar=False
    ).tolist()
    print(json.dumps({"vectors": vectors}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print('{"status":"LOCAL_EMBEDDING_WORKER_REJECTED"}')
        raise SystemExit(1) from None
