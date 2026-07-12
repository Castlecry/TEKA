"""Agent工具定义：Function Calling能力"""

import json
import requests
from datetime import datetime
from typing import Dict, Any, List
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, LLM_MODEL
from opensearch_store import search as vector_search
from web_search import web_search


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
    }
]


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
        
        else:
            return {"success": False, "error": f"未知工具: {tool_name}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def agent_with_tools(query: str, session_id: str = "default", stream_callback=None) -> str:
    """
    Agent with Function Calling
    让LLM自主决定调用哪些工具来回答问题

    Args:
        query: 用户查询
        session_id: 会话 ID（用于 Redis 对话历史）
        stream_callback: 可选的流式回调函数，每生成一个token就调用

    Returns:
        LLM 生成的最终回答
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
                "2. web_search - 联网搜索\n"
                "3. calculate - 数学计算\n"
                "4. get_current_date - 获取当前日期时间（涉及时间相关问题必须先调用）\n"
                "5. get_system_info - 查看系统信息\n\n"
                "重要规则：\n"
                "- 涉及'今天'、'现在'、'最新'、'当前'、'近期'等时间相关问题时，必须先调用 get_current_date 获取准确日期\n"
                "- 再用真实日期生成查询词（如 '2026年7月12日 新闻'），避免编造日期\n"
                "- 对于需要外部信息的问题，优先调用 search_knowledge_base 搜索本地知识库\n"
                "- 如果本地知识库没有找到相关信息，再考虑使用 web_search 联网搜索\n"
                "- 对于数学计算类问题，使用 calculate 工具\n"
                "请用中文回答，回答要准确、简洁、专业。"
            )
        }
    ]
    for msg in history:
        messages.append(msg)
    messages.append({"role": "user", "content": query})

    try:
        response = requests.post(
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
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
    except requests.RequestException as e:
        error_msg = f"调用模型失败: {str(e)}"
        print(f"[Agent] {error_msg}")
        return error_msg

    result = response.json()
    if "choices" not in result or not result["choices"]:
        return "抱歉，模型暂时无法响应，请稍后再试。"

    message = result["choices"][0]["message"]

    # 检查是否有工具调用
    if "tool_calls" in message and message["tool_calls"]:
        tool_calls = message["tool_calls"]
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

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": json.dumps(tool_result, ensure_ascii=False)
            })

        # 第二轮：让LLM基于工具结果生成最终回答
        return _generate_with_messages(headers, messages, stream_callback)

    else:
        # 没有工具调用，直接返回回答
        content = message.get("content", "抱歉，我无法回答这个问题。")
        if stream_callback:
            stream_callback(content)
        return content


def _generate_with_messages(headers: dict, messages: list, stream_callback=None) -> str:
    """基于消息历史生成最终回答（流式或非流式）"""
    if stream_callback:
        try:
            final_response = requests.post(
                f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
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
                        content = delta.get("content", "")
                        if content:
                            answer += content
                            stream_callback(content)
                    except json.JSONDecodeError:
                        continue
            return answer
        except requests.RequestException as e:
            return f"生成回答时出错: {str(e)}"
    else:
        try:
            final_response = requests.post(
                f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
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
        except (requests.RequestException, KeyError, IndexError) as e:
            return f"生成回答时出错: {str(e)}"
