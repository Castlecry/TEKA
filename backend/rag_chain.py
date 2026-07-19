"""RAG 链：查询重述 → 检索 → Rerank 精排 → LLM 流式生成"""

import json
import sys
from config import TOP_K
from opensearch_store import search as vector_search
from web_search import web_search
from conversation_store import save_message, get_history
from query_rewriter import rewrite_query
from reranker import rerank_chunks
from llm_client import chat_completion
from redis_cache import get_search_cache, set_search_cache
from persona_system import build_system_prompt, build_few_shot_messages


def _safe_print(*args, **kwargs):
    """安全打印，忽略 Windows GBK 编码错误"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        try:
            print(*(str(a).encode('ascii', errors='replace').decode('ascii') for a in args), **kwargs)
        except Exception:
            pass

# 模块描述映射（用于 prompt 和模块隔离）
MODULE_DESCRIPTIONS = {
    "policy": "规章制度",
    "tech": "产品技术",
    "admin": "行政服务",
    "general": "自由问答",
}

_MAX_CONTEXT_LENGTH = 8000


def _truncate_text(text: str, max_len: int) -> str:
    """截断文本并添加省略标记"""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def rag_query(query: str, session_id: str = "default", use_web: bool = False,
              use_rerank: bool = True, use_rewrite: bool = True,
              stream_callback=None, provider: str = "api",
              module: str = "general", knowledge_base_ids: list = None) -> str:
    """
    RAG 完整链路：
    1. 查询重述（多轮对话中补全省略/指代）
    2. 向量检索本地知识库（带缓存，支持模块隔离）
    3. Rerank 精排（LLM 对检索结果重新打分）
    4. 可选联网搜索
    5. 构建上下文 + 对话历史（带长度限制）
    6. LLM 流式生成
    7. 保存对话历史

    Args:
        provider: "api" = DeepSeek API, "local" = Ollama 本地模型
        module: 当前模块 (policy/tech/admin/general)
        knowledge_base_ids: 限定的知识库 ID 列表，None 表示按模块自动选择
    """
    # 获取系统 prompt（人设系统生成
    system_prompt = build_system_prompt(module)

    # 1. 查询重述
    search_query = query
    if use_rewrite:
        search_query = rewrite_query(query, session_id)

    # 2. 向量检索（带缓存，支持知识库过滤）
    cache_key = f"{search_query}|{','.join(map(str, knowledge_base_ids))}" if knowledge_base_ids else search_query
    cached_results = get_search_cache(cache_key)
    if cached_results:
        local_results = cached_results
        _safe_print(f"[RAG] 命中搜索缓存，返回 {len(local_results)} 条结果")
    else:
        local_results = vector_search(search_query, top_k=TOP_K, knowledge_base_ids=knowledge_base_ids)
        set_search_cache(cache_key, local_results)
        _safe_print(f"[RAG] 向量检索返回 {len(local_results)} 条结果 (kb_ids={knowledge_base_ids})")

    # 3. Rerank 精排
    if use_rerank and len(local_results) > 1:
        local_results = rerank_chunks(search_query, local_results, top_k=3)
        _safe_print(f"[RAG] Rerank 精排后保留 {len(local_results)} 条结果")

    # 4. 构建上下文（截断过长内容）
    context_parts = []
    for i, r in enumerate(local_results, 1):
        content = _truncate_text(r.get("content", ""), 2000)
        context_parts.append(f"[{i}] (来源: {r.get('source', '')}) {content}")

    # 5. 可选联网搜索（自由问答模块默认允许，其他模块仅在知识库无结果时）
    if use_web:
        web_results = web_search(query)
        for i, r in enumerate(web_results, len(context_parts) + 1):
            content = _truncate_text(r.get("content", ""), 500)
            context_parts.append(f"[{i}] (来源: {r.get('url', '')}) {r.get('title', '')}: {content}")

    if context_parts:
        context = "\n\n".join(context_parts)
        context = _truncate_text(context, _MAX_CONTEXT_LENGTH)
    else:
        context = "暂无相关参考资料。"

    # 6. 获取对话历史（限制长度）
    history = get_history(session_id)

    # 7. 构建消息列表（计算 token 消耗，避免超过限制）
    messages = [{"role": "system", "content": system_prompt}]

    # 加入少样本示例（Few-shot），帮助模型理解输出风格
    few_shot_msgs = build_few_shot_messages(module)
    for msg in few_shot_msgs:
        messages.append(msg)

    history_text = ""
    for msg in history:
        msg_text = f"{msg['role']}: {msg['content']}\n"
        if len(history_text) + len(msg_text) < 3000:
            history_text += msg_text
            messages.append(msg)

    user_msg = f"参考资料：\n{context}\n\n问题：{query}"
    messages.append({"role": "user", "content": user_msg})

    # 8. 调用 LLM（API 或本地模型）
    from config import LLM_MODEL
    model_label = "Ollama 本地" if provider == "local" else LLM_MODEL
    _safe_print(f"\n[RAG] 调用 {model_label} 生成回答 (模块: {module})...\n", flush=True)

    answer = chat_completion(
        messages=messages,
        provider=provider,
        stream=True,
        stream_callback=stream_callback or (lambda ctype, t: _safe_print(t, end="", flush=True)),
        timeout=120 if provider == "local" else 60,
    )

    _safe_print()
    _safe_print(f"\n[RAG] 生成完毕，共 {len(answer)} 字符", flush=True)

    # 9. 保存对话历史
    save_message(session_id, "user", query)
    save_message(session_id, "assistant", answer)

    return answer
