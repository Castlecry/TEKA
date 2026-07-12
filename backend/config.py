"""RAG系统配置"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# PostgreSQL
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "rag_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "MyPassword123!")

# OpenSearch
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "https://localhost:9200")
OPENSEARCH_USER = os.getenv("OPENSEARCH_USER", "admin")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD", "MyPassword123!")
OPENSEARCH_INDEX_PREFIX = os.getenv("OPENSEARCH_INDEX_PREFIX", "rag_docs")
OPENSEARCH_USE_SSL = OPENSEARCH_HOST.startswith("https://")

# Ollama (仅用于嵌入模型)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text:v1.5")

# DeepSeek API (用于 LLM 推理)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

# SearXNG
SEARXNG_HOST = os.getenv("SEARXNG_HOST", "http://localhost:18080")
SEARXNG_SECRET = os.getenv("SEARXNG_SECRET", "your-random-secret-key-change-this")

# MinerU API
MINERU_HOST = os.getenv("MINERU_HOST", "http://127.0.0.1:8000")

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# 知识库文件夹
KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "knowledge_base")

# 文本切片
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

# 检索
TOP_K = int(os.getenv("TOP_K", "5"))
WEB_SEARCH_COUNT = int(os.getenv("WEB_SEARCH_COUNT", "3"))

# 对话历史
HISTORY_TURNS = int(os.getenv("HISTORY_TURNS", "10"))

# LLM 推理超时（秒）
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "600"))

# 支持的文件格式（MinerU 可处理）
SUPPORTED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx",
    ".xls", ".xlsx", ".md", ".txt", ".html", ".htm",
    ".epub", ".mobi", ".jpg", ".jpeg", ".png",
}
