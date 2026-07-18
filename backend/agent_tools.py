"""Agent工具定义：Function Calling能力"""

import json
import os
import re
import uuid
from datetime import datetime
from typing import Dict, Any, List
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, LLM_MODEL
from opensearch_store import search as vector_search
from web_search import web_search
from llm_client import _safe_request


# 工具定义（符合OpenAI Function Calling格式）
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "搜索本地知识库，获取相关文档片段。当用户询问企业内部知识、技术文档、规范制度等问题时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询词"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回结果数量，默认5",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_document_by_title",
            "description": "按文档标题精确查找，当用户明确提到某个文档名称时使用。比如'帮我找一下《员工手册》'、'《报销制度》里怎么说的'。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "文档标题或文件名关键词"
                    },
                    "knowledge_base_id": {
                        "type": "integer",
                        "description": "限定在某个知识库中查找，可选"
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_documents",
            "description": "列出某个知识库中的所有文档。当用户想浏览知识库内容、了解有哪些文档时使用。比如'行政知识库有哪些文档？'、'列出产品技术文档'。",
            "parameters": {
                "type": "object",
                "properties": {
                    "knowledge_base_id": {
                        "type": "integer",
                        "description": "知识库ID，不传则列出所有可见文档"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量，默认20",
                        "default": 20
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_document_summary",
            "description": "获取某份文档的内容摘要。当用户想快速了解文档核心内容时使用。比如'总结一下《IT设备管理制度》'、'这份文档主要讲什么'。",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "integer",
                        "description": "文档ID"
                    },
                    "filename": {
                        "type": "string",
                        "description": "文档文件名（如果不知道ID，可以用文件名查找）"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "keyword_highlight_search",
            "description": "BM25关键词精确匹配搜索，适合查找专业术语、编号、人名等精确内容。当用户问的是非常具体的术语或关键词时使用，补充向量搜索的不足。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "关键词查询词"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回结果数量，默认5",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rewrite_query",
            "description": "将用户口语化、模糊的查询重写为更适合检索的专业查询词。当问题表述不清、有省略或指代时使用，可以提升搜索准确率。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "原始用户查询"
                    },
                    "strategy": {
                        "type": "string",
                        "enum": ["expand", "simplify", "professional"],
                        "description": "重写策略：expand(扩展相关词)、simplify(简化)、professional(专业化)，默认expand",
                        "default": "expand"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_followup_questions",
            "description": "根据当前问题和回答，生成用户可能想问的后续问题建议。回答完一个问题后，可以调用此工具给出追问建议，提升对话体验。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "用户的原始问题"
                    },
                    "answer": {
                        "type": "string",
                        "description": "AI 给出的回答"
                    },
                    "count": {
                        "type": "integer",
                        "description": "生成建议的数量，默认3",
                        "default": 3
                    }
                },
                "required": ["query", "answer"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索互联网，获取最新信息。当用户询问实时信息、最新动态、外部知识时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询词"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "执行数学计算。当用户需要进行数值计算、统计分析时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '2 + 3 * 4'"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_date",
            "description": "获取当前系统日期和时间。当用户询问'今天是哪天'、'现在几点'、'当前日期'，或需要根据当前时间生成查询（如'今天的新闻'）时，必须先调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "获取系统运行状态信息。当用户询问系统状态、性能指标时使用。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_document",
            "description": "将文本内容生成为 Word(.docx) 或 PDF 文档，并返回下载链接。当用户明确说'生成Word'、'生成PDF'、'导出文档'、'做成文件给我'、'下载报告'时使用。内容支持 Markdown 格式。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "文档标题"
                    },
                    "content": {
                        "type": "string",
                        "description": "文档内容（支持 Markdown 格式：标题、列表、代码块、表格、引用、加粗等）"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["word", "pdf"],
                        "description": "输出格式：word 或 pdf，默认为 word",
                        "default": "word"
                    }
                },
                "required": ["title", "content"]
            }
        }
    }
]


def _get_db_session():
    """获取数据库会话"""
    from app.database import SessionLocal
    return SessionLocal()


def execute_tool(tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
    """执行工具调用"""
    try:
        if tool_name == "search_knowledge_base":
            query = tool_args.get("query", "")
            top_k = tool_args.get("top_k", 5)
            results = vector_search(query, top_k=top_k)
            return {
                "success": True,
                "data": {
                    "results": [
                        {
                            "content": r.get("content", ""),
                            "source": r.get("source", ""),
                            "score": r.get("score", 0)
                        }
                        for r in results
                    ],
                    "count": len(results)
                }
            }

        elif tool_name == "search_document_by_title":
            title = tool_args.get("title", "")
            kb_id = tool_args.get("knowledge_base_id")
            db = _get_db_session()
            try:
                from app.models import Document
                query = db.query(Document).filter(Document.filename.contains(title))
                if kb_id:
                    query = query.filter(Document.knowledge_base_id == kb_id)
                query = query.filter(Document.status == "completed")
                docs = query.order_by(Document.uploaded_at.desc()).limit(10).all()
                return {
                    "success": True,
                    "data": {
                        "results": [
                            {
                                "id": d.id,
                                "filename": d.filename,
                                "knowledge_base_id": d.knowledge_base_id,
                                "size": d.size,
                                "chunk_count": d.chunk_count,
                                "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else "",
                            }
                            for d in docs
                        ],
                        "count": len(docs)
                    }
                }
            finally:
                db.close()

        elif tool_name == "list_documents":
            kb_id = tool_args.get("knowledge_base_id")
            limit = tool_args.get("limit", 20)
            db = _get_db_session()
            try:
                from app.models import Document, KnowledgeBase
                query = db.query(Document).filter(Document.status == "completed")
                if kb_id:
                    query = query.filter(Document.knowledge_base_id == kb_id)
                docs = query.order_by(Document.uploaded_at.desc()).limit(limit).all()

                kb_info = None
                if kb_id:
                    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
                    if kb:
                        kb_info = {"id": kb.id, "name": kb.name, "description": kb.description}

                return {
                    "success": True,
                    "data": {
                        "knowledge_base": kb_info,
                        "results": [
                            {
                                "id": d.id,
                                "filename": d.filename,
                                "knowledge_base_id": d.knowledge_base_id,
                                "size": d.size,
                                "chunk_count": d.chunk_count,
                                "file_type": d.file_type,
                                "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else "",
                            }
                            for d in docs
                        ],
                        "count": len(docs)
                    }
                }
            finally:
                db.close()

        elif tool_name == "get_document_summary":
            doc_id = tool_args.get("document_id")
            filename = tool_args.get("filename")
            db = _get_db_session()
            try:
                from app.models import Document
                doc = None
                if doc_id:
                    doc = db.query(Document).filter(Document.id == doc_id).first()
                elif filename:
                    doc = db.query(Document).filter(Document.filename.contains(filename)).first()

                if not doc or not doc.file_path:
                    return {"success": False, "error": "文档不存在或无法读取"}

                if not os.path.exists(doc.file_path):
                    return {"success": False, "error": "文档文件不存在"}

                from document_parser import parse_document
                try:
                    content = parse_document(doc.file_path)
                except Exception as e:
                    return {"success": False, "error": f"文档解析失败: {str(e)}"}

                if not content:
                    return {"success": False, "error": "文档内容为空"}

                content_preview = content[:4000] if len(content) > 4000 else content

                headers = {
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                }
                summary_prompt = f"""请为以下文档生成一个简洁的摘要，包含文档的核心内容和要点。
要求：
1. 用中文回答
2. 分点列出主要内容（3-5个要点）
3. 总字数控制在300字以内
4. 准确反映文档的核心信息

文档内容：
{content_preview}

摘要："""

                resp = _safe_request(
                    "POST",
                    f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
                    max_retries=2,
                    headers=headers,
                    json={
                        "model": LLM_MODEL,
                        "messages": [{"role": "user", "content": summary_prompt}],
                        "temperature": 0.3,
                    },
                    timeout=30,
                )
                result = resp.json()
                summary = result["choices"][0]["message"]["content"]

                return {
                    "success": True,
                    "data": {
                        "document_id": doc.id,
                        "filename": doc.filename,
                        "summary": summary,
                        "total_chars": len(content),
                        "chunk_count": doc.chunk_count,
                    }
                }
            finally:
                db.close()

        elif tool_name == "keyword_highlight_search":
            query = tool_args.get("query", "")
            top_k = tool_args.get("top_k", 5)
            try:
                from opensearch_store import _client, ensure_index, OPENSEARCH_INDEX
                ensure_index()

                bm25_query = {
                    "multi_match": {
                        "query": query,
                        "fields": ["content"],
                        "type": "best_fields",
                        "minimum_should_match": "50%",
                    }
                }
                bm25_body = {
                    "size": top_k * 2,
                    "query": bm25_query,
                    "highlight": {
                        "fields": {
                            "content": {
                                "pre_tags": ["<mark>"],
                                "post_tags": ["</mark>"],
                                "fragment_size": 150,
                                "number_of_fragments": 3,
                            }
                        }
                    },
                }
                resp = _client.search(index=OPENSEARCH_INDEX, body=bm25_body)
                hits = resp["hits"]["hits"]

                results = []
                for h in hits[:top_k]:
                    source = h["_source"]
                    highlights = h.get("highlight", {}).get("content", [])
                    highlight_text = " ... ".join(highlights) if highlights else source["content"][:300]
                    results.append({
                        "content": source["content"],
                        "highlight": highlight_text,
                        "source": source.get("source", ""),
                        "score": h["_score"],
                    })

                return {
                    "success": True,
                    "data": {
                        "results": results,
                        "count": len(results),
                    }
                }
            except Exception as e:
                return {"success": False, "error": f"关键词搜索失败: {str(e)}"}

        elif tool_name == "rewrite_query":
            query = tool_args.get("query", "")
            strategy = tool_args.get("strategy", "expand")
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            }

            strategy_desc = {
                "expand": "扩展相关的专业术语和同义词，生成2-3个不同表述的查询词，覆盖面更广",
                "simplify": "简化口语化表达，提取核心问题关键词",
                "professional": "转化为更专业的企业内部术语表达",
            }.get(strategy, "扩展相关的专业术语和同义词")

            rewrite_prompt = f"""你是一个查询优化助手。请对用户的问题进行重写，使其更适合知识库检索。

策略：{strategy_desc}

要求：
1. 保持原意不变
2. 生成3个不同角度的优化查询词
3. 每个查询词用一行表示
4. 直接输出查询词，不要编号，不要解释

原始问题：{query}

优化后的查询词："""

            try:
                resp = _safe_request(
                    "POST",
                    f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
                    max_retries=2,
                    headers=headers,
                    json={
                        "model": LLM_MODEL,
                        "messages": [{"role": "user", "content": rewrite_prompt}],
                        "temperature": 0.3,
                    },
                    timeout=20,
                )
                result = resp.json()
                rewritten_text = result["choices"][0]["message"]["content"].strip()
                rewritten_queries = [
                    line.strip()
                    for line in rewritten_text.split("\n")
                    if line.strip() and len(line.strip()) > 2
                ][:3]

                if not rewritten_queries:
                    rewritten_queries = [query]

                print(f"[RewriteQuery] \"{query}\" → {rewritten_queries}")

                return {
                    "success": True,
                    "data": {
                        "original": query,
                        "rewritten_queries": rewritten_queries,
                        "strategy": strategy,
                        "best_query": rewritten_queries[0],
                    }
                }
            except Exception as e:
                return {
                    "success": True,
                    "data": {
                        "original": query,
                        "rewritten_queries": [query],
                        "strategy": strategy,
                        "best_query": query,
                    }
                }

        elif tool_name == "generate_followup_questions":
            query = tool_args.get("query", "")
            answer = tool_args.get("answer", "")
            count = tool_args.get("count", 3)
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            }

            followup_prompt = f"""基于以下的问答对，生成 {count} 个用户可能会继续追问的相关问题。

用户的问题：{query}

AI的回答：{answer[:2000]}

要求：
1. 问题要与当前主题高度相关
2. 问题应该是用户自然会深入询问的方向
3. 问题要具体，不要太宽泛
4. 每个问题单独一行
5. 不要编号，不要解释，直接输出问题

可能的追问："""

            try:
                resp = _safe_request(
                    "POST",
                    f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
                    max_retries=2,
                    headers=headers,
                    json={
                        "model": LLM_MODEL,
                        "messages": [{"role": "user", "content": followup_prompt}],
                        "temperature": 0.7,
                    },
                    timeout=20,
                )
                result = resp.json()
                questions_text = result["choices"][0]["message"]["content"].strip()
                questions = [
                    q.strip().lstrip("- ").lstrip("0123456789. ")
                    for q in questions_text.split("\n")
                    if q.strip() and len(q.strip()) > 3
                ][:count]

                return {
                    "success": True,
                    "data": {
                        "questions": questions,
                        "count": len(questions),
                    }
                }
            except Exception as e:
                return {"success": False, "error": f"生成追问失败: {str(e)}"}
        
        elif tool_name == "web_search":
            query = tool_args.get("query", "")
            results = web_search(query)
            return {
                "success": True,
                "data": {
                    "results": [
                        {
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "content": r.get("content", "")
                        }
                        for r in results
                    ],
                    "count": len(results)
                }
            }
        
        elif tool_name == "calculate":
            expression = tool_args.get("expression", "")
            # 安全计算（只允许数学运算）
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                return {"success": False, "error": "不允许的字符"}
            result = eval(expression)
            return {"success": True, "data": {"result": result}}
        
        elif tool_name == "get_current_date":
            now = datetime.now()
            return {
                "success": True,
                "data": {
                    "date": now.strftime("%Y-%m-%d"),
                    "time": now.strftime("%H:%M:%S"),
                    "weekday": ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][now.weekday()],
                    "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "timestamp": int(now.timestamp()),
                    "iso_format": now.isoformat()
                }
            }

        elif tool_name == "get_system_info":
            # 模拟系统信息
            return {
                "success": True,
                "data": {
                    "status": "healthy",
                    "version": "1.0.0",
                    "knowledge_bases": 5,
                    "documents": 120,
                    "active_users": 8
                }
            }

        elif tool_name == "create_document":
            from document_generator import generate_document
            title = tool_args.get("title", "文档")
            content = tool_args.get("content", "")
            fmt = tool_args.get("format", "word").lower()
            if not content:
                return {"success": False, "error": "文档内容不能为空"}
            try:
                file_id, filename, file_path = generate_document(content, format=fmt, title=title)
            except ValueError as ve:
                return {"success": False, "error": str(ve)}
            size_bytes = os.path.getsize(file_path)
            return {
                "success": True,
                "data": {
                    "file_id": file_id,
                    "filename": filename,
                    "format": fmt,
                    "size_bytes": size_bytes,
                    "size_kb": round(size_bytes / 1024, 1),
                    "download_url": f"/files/download/{file_id}",
                }
            }

        else:
            return {"success": False, "error": f"未知工具: {tool_name}"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_dsml_tool_calls(content: str) -> list:
    """
    解析 DeepSeek DSML 格式的工具调用
    格式示例（注意空格变化）：
    <| | DSML | | tool_calls>
    <| | DSML | | invoke name="web_search">
    <| | DSML | | parameter name="query" string="true">公司报税</| | DSML | | parameter>
    </| | DSML | | invoke>
    </| | DSML | | tool_calls>
    """
    tool_calls = []
    
    # 匹配所有 invoke 块（兼容多种空格格式）
    invoke_pattern = r'<\|[\s|]*DSML[\s|]*\|[\s|]*invoke\s+name="([^"]+)"[\s|]*>(.*?)</\|[\s|]*DSML[\s|]*\|[\s|]*invoke[\s|]*>'
    invokes = re.findall(invoke_pattern, content, re.DOTALL)
    
    for tool_name, params_str in invokes:
        # 解析参数
        params = {}
        param_pattern = r'<\|[\s|]*DSML[\s|]*\|[\s|]*parameter\s+name="([^"]+)"[^>]*>(.*?)</\|[\s|]*DSML[\s|]*\|[\s|]*parameter[\s|]*>'
        param_matches = re.findall(param_pattern, params_str, re.DOTALL)
        
        for param_name, param_value in param_matches:
            # 尝试解析 JSON
            try:
                params[param_name] = json.loads(param_value.strip())
            except json.JSONDecodeError:
                params[param_name] = param_value.strip()
        
        tool_calls.append({
            "id": str(uuid.uuid4()),
            "function": {
                "name": tool_name,
                "arguments": json.dumps(params, ensure_ascii=False)
            }
        })
    
    return tool_calls


def agent_with_tools(query: str, session_id: str = "default", stream_callback=None) -> dict:
    """
    Agent with Function Calling
    让LLM自主决定调用哪些工具来回答问题

    Args:
        query: 用户查询
        session_id: 会话 ID（用于 Redis 对话历史）
        stream_callback: 可选的流式回调函数，每生成一个token就调用

    Returns:
        {"answer": "最终回答", "attachments": [{"file_id", "filename", "format", "size_kb", "download_url"}]}
    """
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    # 加载对话历史
    try:
        from conversation_store import get_history
        history = get_history(session_id)
    except Exception:
        history = []

    # 构建消息列表（系统提示 + 历史 + 当前问题）
    messages = [
        {
            "role": "system",
            "content": (
                "你是一个科技企业智能助手，可以使用工具来帮助用户解决问题。\n"
                "可用工具：\n"
                "1. search_knowledge_base - 搜索本地知识库\n"
                "2. search_document_by_title - 按文档标题精确查找（当用户提到具体文档名时使用）\n"
                "3. list_documents - 列出知识库中的文档（浏览知识库内容时使用）\n"
                "4. get_document_summary - 获取文档摘要（快速了解文档核心内容时使用）\n"
                "5. keyword_highlight_search - BM25关键词精确搜索（查找专业术语、编号、人名等精确内容）\n"
                "6. rewrite_query - 查询重写优化（问题表述不清时，先重写再搜索）\n"
                "7. generate_followup_questions - 生成追问建议\n"
                "8. web_search - 联网搜索\n"
                "9. calculate - 数学计算\n"
                "10. get_current_date - 获取当前日期时间（涉及时间相关问题必须先调用）\n"
                "11. get_system_info - 查看系统信息\n"
                "12. create_document - 生成 Word/PDF 文档（当用户要求导出/下载/生成文档时使用）\n\n"
                "重要规则：\n"
                "- 涉及'今天'、'现在'、'最新'、'当前'、'近期'等时间相关问题时，必须先调用 get_current_date 获取准确日期\n"
                "- 再用真实日期生成查询词（如 '2026年7月12日 新闻'），避免编造日期\n"
                "- 对于需要外部信息的问题，优先调用 search_knowledge_base 搜索本地知识库\n"
                "- 如果本地知识库没有找到相关信息，再考虑使用 web_search 联网搜索\n"
                "- 当用户明确提到某份文档名称时，先调用 search_document_by_title 定位文档\n"
                "- 对于表述模糊或口语化的问题，可以先调用 rewrite_query 重写后再搜索\n"
                "- 对于数学计算类问题，使用 calculate 工具\n"
                "- 当用户要求'生成Word'、'生成PDF'、'导出文档'、'下载为文件'、'做成文件给我'、'做成word/pdf文档给我'时：\n"
                "  - 必须调用 create_document 工具（这是生成真实文件的唯一途径）\n"
                "  - format 参数：word（默认）或 pdf\n"
                "  - content 参数应使用 Markdown 格式组织内容（标题/列表/表格/代码块等）\n"
                "  - 如果用户没有指定格式，默认生成 word 文档\n"
                "  - 严禁不调用工具就告诉用户'文档已生成'或编造下载链接——这会误导用户！\n"
                "- 调用 create_document 后，用一句话告诉用户文档已生成（不要在文案里编具体的链接文本）\n"
                "请用中文回答，回答要准确、简洁、专业。"
            )
        }
    ]
    for msg in history:
        messages.append(msg)
    messages.append({"role": "user", "content": query})

    attachments: list[dict] = []

    try:
        response = _safe_request(
            "POST",
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
            max_retries=3,
            headers=headers,
            json={
                "model": LLM_MODEL,
                "messages": messages,
                "tools": TOOLS,
                "tool_choice": "auto"
            },
            timeout=60
        )
        response.raise_for_status()
    except Exception as e:
        error_msg = f"调用模型失败: {str(e)}"
        print(f"[Agent] {error_msg}")
        return {"answer": error_msg, "attachments": []}

    result = response.json()
    if "choices" not in result or not result["choices"]:
        return {"answer": "抱歉，模型暂时无法响应，请稍后再试。", "attachments": []}

    message = result["choices"][0]["message"]

    # 优先检查 OpenAI 标准 tool_calls 字段
    tool_calls = message.get("tool_calls") or []

    # 如果没有标准 tool_calls，尝试从 content 中解析 DSML 格式
    if not tool_calls:
        content = message.get("content", "")
        if "<|DSML|" in content or "<| | DSML |" in content:
            tool_calls = _parse_dsml_tool_calls(content)
            # 从 content 中移除 DSML 工具调用块，保留普通文本
            content = re.sub(
                r'<\|[\s|]*DSML[\s|]*\|[\s|]*tool_calls[\s|]*>.*?</\|[\s|]*DSML[\s|]*\|[\s|]*tool_calls[\s|]*>',
                '', content, flags=re.DOTALL
            ).strip()
            message["content"] = content

    # 检查是否有工具调用
    if tool_calls:
        messages.append(message)

        # 执行每个工具调用
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            try:
                tool_args = json.loads(tool_call["function"]["arguments"])
            except json.JSONDecodeError:
                tool_args = {}

            print(f"[Agent] 调用工具: {tool_name}, 参数: {tool_args}")

            tool_result = execute_tool(tool_name, tool_args)

            # 收集 create_document 工具的附件
            if tool_name == "create_document" and tool_result.get("success"):
                data = tool_result.get("data", {})
                if "file_id" in data:
                    attachments.append({
                        "file_id": data["file_id"],
                        "filename": data["filename"],
                        "format": data["format"],
                        "size_kb": data["size_kb"],
                        "download_url": data["download_url"],
                    })

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": json.dumps(tool_result, ensure_ascii=False)
            })

        # 第二轮：让LLM基于工具结果生成最终回答
        final_answer = _generate_with_messages(headers, messages, stream_callback)
        return {"answer": final_answer, "attachments": attachments}

    else:
        # 没有工具调用，直接返回回答
        content = message.get("content", "抱歉，我无法回答这个问题。")
        if stream_callback:
            stream_callback("content", content)
        return {"answer": content, "attachments": []}


def _generate_with_messages(headers: dict, messages: list, stream_callback=None) -> str:
    """基于消息历史生成最终回答（流式或非流式）"""
    if stream_callback:
        try:
            final_response = _safe_request(
                "POST",
                f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
                max_retries=3,
                headers=headers,
                json={
                    "model": LLM_MODEL,
                    "messages": messages,
                    "stream": True
                },
                stream=True,
                timeout=60
            )
            final_response.raise_for_status()

            answer = ""
            for line in final_response.iter_lines():
                if not line:
                    continue
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    data_str = line_str[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        # 推理模型：reasoning_content + content 分阶段推送
                        reasoning = delta.get("reasoning_content", "")
                        content = delta.get("content", "")
                        if reasoning:
                            stream_callback("reasoning", reasoning)
                        if content:
                            answer += content
                            stream_callback("content", content)
                    except json.JSONDecodeError:
                        continue
            return answer
        except Exception as e:
            return f"生成回答时出错: {str(e)}"
    else:
        try:
            final_response = _safe_request(
                "POST",
                f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
                max_retries=3,
                headers=headers,
                json={
                    "model": LLM_MODEL,
                    "messages": messages
                },
                timeout=60
            )
            final_response.raise_for_status()
            final_result = final_response.json()
            return final_result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"生成回答时出错: {str(e)}"
