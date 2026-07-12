"""LangGraph高级智能体编排"""

from typing import Dict, List, Any, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, LLM_MODEL
from agent_tools import execute_tool, TOOLS
from llm_client import _safe_request
import json


class AgentState(TypedDict):
    """智能体状态"""
    messages: List[Dict[str, str]]
    next_action: str
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    final_answer: str
    iteration: int
    stream_callback: Any  # 可选的流式回调函数


def should_continue(state: AgentState) -> str:
    """决定下一步动作"""
    if state["iteration"] >= 5:  # 最大迭代次数
        return "end"
    
    if state["next_action"] == "use_tool":
        return "execute_tool"
    elif state["next_action"] == "answer":
        return "generate_answer"
    else:
        return "end"


def analyze_query(state: AgentState) -> AgentState:
    """分析用户查询，决定是否需要使用工具"""
    messages = state["messages"]
    query = messages[-1]["content"] if messages else ""
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    
    # 让LLM分析是否需要工具
    system_prompt = """你是一个智能任务分析器。分析用户的问题，决定是否需要使用工具。

可用工具：
1. search_knowledge_base - 搜索本地知识库
2. web_search - 搜索互联网
3. calculate - 数学计算
4. get_current_date - 获取当前系统日期时间
5. get_system_info - 获取系统信息
6. create_document - 生成 Word/PDF 文档（当用户要求导出/下载/生成文档时使用）

重要规则：
- 涉及"今天"、"现在"、"最新"、"当前"、"近期"等时间相关问题时，必须先调用 get_current_date 获取真实日期
- 再用真实日期生成查询词（如 "2026年7月12日 新闻"），避免编造日期
- 如果问题需要实时信息、外部知识、计算或系统状态，请返回JSON：
{"need_tool": true, "tool": "工具名", "args": {参数}}

如果可以直接回答，返回：
{"need_tool": false}

只返回JSON，不要其他内容。"""
    
    response = _safe_request(
        "POST",
        f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
        max_retries=3,
        headers=headers,
        json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "temperature": 0.1
        },
        timeout=30
    )
    
    try:
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        decision = json.loads(content)
        
        if decision.get("need_tool"):
            state["next_action"] = "use_tool"
            state["tool_calls"] = [{
                "tool": decision["tool"],
                "args": decision.get("args", {})
            }]
        else:
            state["next_action"] = "answer"
    except:
        state["next_action"] = "answer"
    
    state["iteration"] += 1
    return state


def execute_tool_node(state: AgentState) -> AgentState:
    """执行工具调用"""
    tool_calls = state.get("tool_calls", [])
    tool_results = []
    
    for tool_call in tool_calls:
        tool_name = tool_call["tool"]
        tool_args = tool_call["args"]
        
        print(f"[LangGraph] 执行工具: {tool_name}, 参数: {tool_args}")
        
        result = execute_tool(tool_name, tool_args)
        tool_results.append({
            "tool": tool_name,
            "result": result
        })
    
    state["tool_results"] = tool_results
    state["next_action"] = "generate_answer"
    state["iteration"] += 1
    return state


def generate_answer(state: AgentState) -> AgentState:
    """基于工具结果生成最终答案"""
    messages = state["messages"]
    tool_results = state.get("tool_results", [])
    stream_callback = state.get("stream_callback")
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    
    # 构建包含工具结果的上下文
    context_parts = []
    for tr in tool_results:
        if tr["result"].get("success"):
            context_parts.append(f"工具 {tr['tool']} 返回结果: {json.dumps(tr['result']['data'], ensure_ascii=False)}")
        else:
            context_parts.append(f"工具 {tr['tool']} 执行失败: {tr['result'].get('error', '未知错误')}")
    
    system_prompt = """你是一个智能助手，基于工具返回的结果回答用户问题。
请综合所有信息，给出准确、完整的回答。
如果工具返回的信息不足，请说明局限性。"""
    
    user_content = messages[-1]["content"] if messages else ""
    if context_parts:
        user_content += "\n\n工具返回的信息：\n" + "\n".join(context_parts)
    
    if stream_callback:
        # 流式模式
        response = _safe_request(
            "POST",
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
            max_retries=3,
            headers=headers,
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.7,
                "stream": True
            },
            stream=True,
            timeout=60
        )
        response.raise_for_status()
        
        answer = ""
        for line in response.iter_lines():
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
    else:
        # 非流式模式
        response = _safe_request(
            "POST",
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
            max_retries=3,
            headers=headers,
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.7
            },
            timeout=60
        )

        result = response.json()
        answer = result["choices"][0]["message"]["content"]
    
    state["final_answer"] = answer
    state["next_action"] = "end"
    state["iteration"] += 1
    return state


def create_agent_graph():
    """创建LangGraph智能体图"""
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("analyze", analyze_query)
    workflow.add_node("execute_tool", execute_tool_node)
    workflow.add_node("generate_answer", generate_answer)
    
    # 设置入口
    workflow.set_entry_point("analyze")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "analyze",
        should_continue,
        {
            "execute_tool": "execute_tool",
            "generate_answer": "generate_answer",
            "end": END
        }
    )
    
    workflow.add_edge("execute_tool", "generate_answer")
    workflow.add_edge("generate_answer", END)
    
    return workflow.compile()


def run_agent(query: str, session_id: str = "default", stream_callback=None) -> str:
    """运行LangGraph智能体

    Args:
        query: 用户查询
        session_id: 会话 ID（用于对话历史）
        stream_callback: 可选的流式回调函数，每生成一个token就调用
    """
    # 加载对话历史
    try:
        from conversation_store import get_history
        history = get_history(session_id, turns=5)  # LangGraph 上下文更长，限制 5 轮
    except Exception:
        history = []

    graph = create_agent_graph()

    initial_state = {
        "messages": [
            *history,
            {"role": "user", "content": query}
        ],
        "next_action": "analyze",
        "tool_calls": [],
        "tool_results": [],
        "final_answer": "",
        "iteration": 0,
        "stream_callback": stream_callback
    }

    print(f"\n[LangGraph] 开始处理查询: {query[:50]}...")

    try:
        # 运行图
        final_state = graph.invoke(initial_state)
        answer = final_state.get("final_answer", "抱歉，我无法回答这个问题。")
        print(f"[LangGraph] 生成答案完成，共 {len(answer)} 字符\n")
        return answer
    except Exception as e:
        error_msg = f"LangGraph 智能体执行失败: {str(e)}"
        print(f"[LangGraph] {error_msg}")
        return error_msg
