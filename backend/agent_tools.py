"""Agent工具定义：Function Calling能力"""

import json
import requests
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
    stream_callback: 可选的流式回调函数，每生成一个token就调用
    """
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    
    # 第一轮：让LLM决定是否调用工具
    messages = [
        {
            "role": "system",
            "content": "你是一个智能助手，可以使用工具来帮助用户。如果需要使用工具，请调用相应的工具函数。"
        },
        {"role": "user", "content": query}
    ]
    
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
    
    result = response.json()
    message = result["choices"][0]["message"]
    
    # 检查是否有工具调用
    if "tool_calls" in message and message["tool_calls"]:
        # 执行工具调用
        tool_calls = message["tool_calls"]
        
        # 将assistant消息添加到历史
        messages.append(message)
        
        # 执行每个工具调用
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            tool_args = json.loads(tool_call["function"]["arguments"])
            
            print(f"[Agent] 调用工具: {tool_name}, 参数: {tool_args}")
            
            # 执行工具
            tool_result = execute_tool(tool_name, tool_args)
            
            # 将工具结果添加到消息历史
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": json.dumps(tool_result, ensure_ascii=False)
            })
        
        # 第二轮：让LLM基于工具结果生成最终回答
        if stream_callback:
            # 流式模式
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
                if line:
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
        else:
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
            answer = final_result["choices"][0]["message"]["content"]
            return answer
    
    else:
        # 没有工具调用，直接返回回答
        content = message.get("content", "抱歉，我无法回答这个问题。")
        if stream_callback:
            stream_callback(content)
        return content
