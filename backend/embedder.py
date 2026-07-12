"""向量嵌入模块：使用 Ollama nomic-embed-text"""

import requests
from config import OLLAMA_HOST, EMBED_MODEL


def embed_text(text: str) -> list[float]:
    """将文本转换为向量（调用 /api/embed 接口）"""
    resp = requests.post(
        f"{OLLAMA_HOST}/api/embed",
        json={"model": EMBED_MODEL, "input": text},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["embeddings"][0]


def embed_batch(texts: list[str]) -> list[list[float]]:
    """批量嵌入"""
    resp = requests.post(
        f"{OLLAMA_HOST}/api/embed",
        json={"model": EMBED_MODEL, "input": texts},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["embeddings"]
