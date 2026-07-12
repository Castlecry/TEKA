"""LLM 调用模块：支持 DeepSeek API 和 Ollama 本地模型"""

import json
import requests
from config import (
    DEEPSEEK_BASE_URL, DEEPSEEK_API_KEY, LLM_MODEL,
    OLLAMA_HOST, OLLAMA_CHAT_MODEL,
)


def _ollama_chat(messages: list[dict], stream: bool = False,
                 stream_callback=None, timeout: int = 120) -> str:
    """通过 Ollama 本地模型生成回答"""
    # 将 messages 转换为 Ollama prompt 格式
    system_prompt = ""
    user_prompt = ""
    for msg in messages:
        if msg["role"] == "system":
            system_prompt = msg["content"]
        elif msg["role"] == "user":
            user_prompt = msg["content"]

    payload = {
        "model": OLLAMA_CHAT_MODEL,
        "prompt": user_prompt,
        "system": system_prompt,
        "stream": stream,
        "options": {
            "temperature": 0.7,
            "num_predict": 2048,
        }
    }

    if stream and stream_callback:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=payload,
            stream=True,
            timeout=timeout,
        )
        resp.raise_for_status()
        answer = ""
        for line in resp.iter_lines():
            if not line:
                continue
            try:
                chunk = json.loads(line.decode("utf-8"))
                token = chunk.get("response", "")
                if token:
                    answer += token
                    stream_callback(token)
                if chunk.get("done"):
                    break
            except json.JSONDecodeError:
                continue
        return answer
    else:
        payload["stream"] = False
        resp = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=payload,
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")


def _deepseek_chat(messages: list[dict], stream: bool = False,
                   stream_callback=None, tools: list = None,
                   tool_choice: str = None, timeout: int = 60) -> str:
    """通过 DeepSeek API 生成回答"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "stream": stream,
    }
    if tools:
        payload["tools"] = tools
    if tool_choice:
        payload["tool_choice"] = tool_choice

    resp = requests.post(
        f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
        headers=headers,
        json=payload,
        stream=stream,
        timeout=timeout,
    )
    resp.raise_for_status()

    if stream:
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
            except json.JSONDecodeError:
                continue
        return answer
    else:
        result = resp.json()
        return result["choices"][0]["message"]["content"]


def deepseek_chat_with_tools(messages: list[dict], tools: list,
                              tool_choice: str = "auto", timeout: int = 60) -> dict:
    """DeepSeek API 带工具调用的非流式请求，返回完整响应对象"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "tools": tools,
        "tool_choice": tool_choice,
    }
    resp = requests.post(
        f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


def chat_completion(messages: list[dict], provider: str = "api",
                    stream: bool = False, stream_callback=None,
                    tools: list = None, tool_choice: str = None,
                    timeout: int = 120) -> str | dict:
    """
    统一的聊天补全接口

    Args:
        messages: 消息列表 [{"role": "user"/"system"/"assistant", "content": "..."}]
        provider: "api" (DeepSeek) 或 "local" (Ollama)
        stream: 是否流式输出
        stream_callback: 流式回调函数
        tools: 工具列表（仅 api 模式支持 Function Calling）
        tool_choice: 工具选择策略（仅 api 模式）
        timeout: 超时时间

    Returns:
        非流式返回字符串，带 tools 时返回 dict（仅 api 模式）
    """
    if provider == "local":
        return _ollama_chat(messages, stream=stream,
                           stream_callback=stream_callback, timeout=timeout)
    else:
        # DeepSeek API
        if tools:
            # 带工具的非流式请求，返回完整对象
            return deepseek_chat_with_tools(messages, tools, tool_choice, timeout)
        return _deepseek_chat(messages, stream=stream,
                             stream_callback=stream_callback,
                             tools=tools, tool_choice=tool_choice, timeout=timeout)
