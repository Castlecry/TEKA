"""app 层配置 — 从根级 config 重新导出，保持兼容"""

import sys
import os

# 将 backend 根目录加入 path，以便导入根级 config
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from config import (  # noqa: E402, F401
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    OPENSEARCH_HOST,
    OPENSEARCH_USER,
    OPENSEARCH_PASSWORD,
    OPENSEARCH_INDEX_PREFIX,
    OPENSEARCH_INDEX,
    OLLAMA_HOST,
    EMBED_MODEL,
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    LLM_MODEL,
    SEARXNG_HOST,
    SEARXNG_SECRET,
    MINERU_HOST,
    REDIS_HOST,
    REDIS_PORT,
    KNOWLEDGE_BASE_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K,
    WEB_SEARCH_COUNT,
    HISTORY_TURNS,
    LLM_TIMEOUT,
    EMBED_DIMENSION,
    SUPPORTED_EXTENSIONS,
)
