"""OpenSearch 向量存储与检索模块"""

import uuid
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.helpers import bulk
from urllib3.exceptions import InsecureRequestWarning
import warnings

from config import (
    OPENSEARCH_HOST, OPENSEARCH_USER, OPENSEARCH_PASSWORD,
    OPENSEARCH_INDEX, TOP_K, EMBED_MODEL, OPENSEARCH_USE_SSL,
)
from embedder import embed_text

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

http_auth = (OPENSEARCH_USER, OPENSEARCH_PASSWORD) if OPENSEARCH_USE_SSL else None
_client = OpenSearch(
    hosts=[OPENSEARCH_HOST],
    http_auth=http_auth,
    use_ssl=OPENSEARCH_USE_SSL,
    verify_certs=False,
    connection_class=RequestsHttpConnection,
)

INDEX_SETTINGS = {
    "settings": {
        "index": {
            "knn": True,
        }
    },
    "mappings": {
        "properties": {
            "content": {"type": "text"},
            "embedding": {
                "type": "knn_vector",
                "dimension": 768,
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "nmslib",
                },
            },
            "source": {"type": "keyword"},
            "chunk_index": {"type": "integer"},
        }
    },
}


def ensure_index():
    """确保索引存在"""
    if not _client.indices.exists(index=OPENSEARCH_INDEX):
        _client.indices.create(index=OPENSEARCH_INDEX, body=INDEX_SETTINGS)
        print(f"[OpenSearch] 创建索引: {OPENSEARCH_INDEX}")
    else:
        print(f"[OpenSearch] 索引已存在: {OPENSEARCH_INDEX}")


def add_documents(chunks: list[str], source: str = "unknown"):
    """将文本切片存入 OpenSearch"""
    ensure_index()
    docs = []
    for i, chunk in enumerate(chunks):
        vec = embed_text(chunk)
        docs.append({
            "_index": OPENSEARCH_INDEX,
            "_id": str(uuid.uuid4()),
            "_source": {
                "content": chunk,
                "embedding": vec,
                "source": source,
                "chunk_index": i,
            },
        })

    success, errors = bulk(_client, docs)
    print(f"[OpenSearch] 写入 {success} 条文档, 错误 {len(errors)}")
    return success


def search(query: str, top_k: int = TOP_K) -> list[dict]:
    """向量检索"""
    ensure_index()
    vec = embed_text(query)

    body = {
        "size": top_k,
        "query": {
            "knn": {
                "embedding": {
                    "vector": vec,
                    "k": top_k,
                }
            }
        },
    }

    resp = _client.search(index=OPENSEARCH_INDEX, body=body)
    results = []
    for hit in resp["hits"]["hits"]:
        results.append({
            "content": hit["_source"]["content"],
            "source": hit["_source"].get("source", ""),
            "score": hit["_score"],
        })
    return results


def clear_index():
    """清空索引"""
    if _client.indices.exists(index=OPENSEARCH_INDEX):
        _client.indices.delete(index=OPENSEARCH_INDEX)
        print(f"[OpenSearch] 已删除索引: {OPENSEARCH_INDEX}")
