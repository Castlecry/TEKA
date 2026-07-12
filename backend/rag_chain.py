"""RAG 链：查询重述 → 检索 → Rerank 精排 → LLM 流式生成"""

import json
import requests
from config import DEEPSEEK_BASE_URL, DEEPSEEK_API_KEY, LLM_MODEL, TOP_K
from opensearch_store import search as vector_search
from web_search import web_search
from conversation_store import save_message, get_history
from query_rewriter import rewrite_query
from reranker import rerank_chunks

SYSTEM_PROMPT = """你是一个智能助手，基于检索到的信息回答问题。
请优先使用提供的参考资料回答，如果资料不足以回答，可以结合你的知识补充。
回答时请引用来源。如果参考资料中没有相关信息，请明确说明。"""

_headers = {
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type": "application/json",
}


def rag_query(query: str, session_id: str = "default", use_web: bool = False,
              use_rerank: bool = True, use_rewrite: bool = True,
              stream_callback=None) -> str:
    """
    RAG 完整链路：
    1. 查询重述（多轮对话中补全省略/指代）
    2. 向量检索本地知识库
    3. Rerank 精排（LLM 对检索结果重新打分）
    4. 可选联网搜索
    5. 构建上下文 + 对话历史
    6. LLM 流式生成
    7. 保存对话历史
    """
    # 1. 查询重述
    search_query = query
    if use_rewrite:
        search_query = rewrite_query(query, session_id)

    # 2. 向量检索
    local_results = vector_search(search_query, top_k=TOP_K)
    print(f"[RAG] 向量检索返回 {len(local_results)} 条结果")

    # 3. Rerank 精排
    if use_rerank and len(local_results) > 1:
        local_results = rerank_chunks(search_query, local_results, top_k=3)
        print(f"[RAG] Rerank 精排后保留 {len(local_results)} 条结果")

    # 4. 构建上下文
    context_parts = []
    for i, r in enumerate(local_results, 1):
        context_parts.append(f"[{i}] (来源: {r['source']}) {r['content']}")

    # 5. 可选联网搜索
    if use_web:
        web_results = web_search(query)
        for i, r in enumerate(web_results, len(context_parts) + 1):
            context_parts.append(f"[{i}] (来源: {r['url']}) {r['title']}: {r['content']}")

    if context_parts:
        context = "\n\n".join(context_parts)
    else:
        context = "暂无相关参考资料。"

    # 6. 获取对话历史
    history = get_history(session_id)

    # 7. 构建消息列表
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history:
        messages.append(msg)

    user_msg = f"参考资料：\n{context}\n\n问题：{query}"
    messages.append({"role": "user", "content": user_msg})

    # 8. 调用 DeepSeek API（流式输出）
    print(f"\n[RAG] 调用 {LLM_MODEL} 生成回答...\n", flush=True)

    resp = requests.post(
        f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
        headers=_headers,
        json={"model": LLM_MODEL, "messages": messages, "stream": True},
        timeout=60,
        stream=True,
    )
    resp.raise_for_status()

    answer = ""
    for line in resp.iter_lines():
        if not line:
            continue
        line_str = line.decode("utf-8") if isinstance(line, bytes) else line
        if line_str.startswith("data: "):
            line_str = line_str[6:]
        if line_str.strip() == "[DONE]":
            break
        try:
            chunk = json.loads(line_str)
            delta = chunk.get("choices", [{}])[0].get("delta", {})
            token = delta.get("content", "")
            if token:
                answer += token
                if stream_callback:
                    stream_callback(token)
                else:
                    print(token, end="", flush=True)
        except json.JSONDecodeError:
            continue

    print()
    print(f"\n[RAG] 生成完毕，共 {len(answer)} 字符", flush=True)

    # 9. 保存对话历史
    save_message(session_id, "user", query)
    save_message(session_id, "assistant", answer)

    return answer
