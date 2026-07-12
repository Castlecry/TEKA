import json
import sys
import os
import uuid
import asyncio
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.routers.auth import get_current_user

# 将 backend 根目录加入 path，以便导入根级 RAG 模块
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import rag_chain as _rag_chain
import conversation_store as _conv_store
from agent_tools import agent_with_tools
from langgraph_agent import run_agent
from config import TOP_K, WEB_SEARCH_COUNT

router = APIRouter(prefix="/chat", tags=["chat"])


async def _stream_rag_query(query: str, session_id: str, use_web: bool = False,
                            use_rerank: bool = True, use_rewrite: bool = True,
                            knowledge_base_ids: Optional[List[int]] = None):
    """将 rag_chain.rag_query 的回调模式包装为 async generator"""
    chunks: list = []
    loop = asyncio.get_event_loop()

    def _on_token(token: str):
        chunks.append(token)

    await loop.run_in_executor(
        None,
        lambda: _rag_chain.rag_query(
            query=query,
            session_id=session_id,
            use_web=use_web,
            use_rerank=use_rerank,
            use_rewrite=use_rewrite,
            stream_callback=_on_token,
        )
    )

    for token in chunks:
        yield token


def _extract_last_answer(session_id: str) -> str:
    """从 Redis 对话历史中提取最后一条 assistant 消息"""
    history = _conv_store.get_history(session_id, turns=1)
    for msg in reversed(history):
        if msg.get("role") == "assistant":
            return msg.get("content", "")
    return ""


@router.post("/message")
async def send_message(
    message: schemas.ChatMessage,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    conversation_id = message.conversation_id or str(uuid.uuid4())

    history = _conv_store.get_history(conversation_id)

    # 根据模式选择不同的处理方式
    if message.mode == "agent":
        # Agent模式：使用Function Calling
        response = agent_with_tools(
            query=message.message,
            session_id=conversation_id
        )
    elif message.mode == "langgraph":
        # LangGraph模式：使用高级智能体编排
        response = run_agent(
            query=message.message,
            session_id=conversation_id
        )
    else:
        # 默认RAG模式
        response = _rag_chain.rag_query(
            query=message.message,
            session_id=conversation_id,
            use_web=message.use_web or False,
            use_rerank=True,
            use_rewrite=True,
        )

    # 从 Redis 获取来源（简化处理：检索阶段没有直接返回 sources）
    sources = []

    db_log = models.ConversationLog(
        conversation_id=conversation_id,
        user_id=current_user.id,
        query=message.message,
        answer=response,
        sources=sources,
        knowledge_base_ids=message.knowledge_base_ids or [],
    )
    db.add(db_log)
    db.commit()

    return {"answer": response, "sources": sources, "conversation_id": conversation_id}


@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            query = message_data.get("message", "")
            use_web = message_data.get("use_web", False)
            mode = message_data.get("mode", "rag")  # 默认使用 rag 模式

            full_answer = ""

            if mode == "agent":
                # Agent 模式：使用 Function Calling
                loop = asyncio.get_event_loop()

                def stream_callback(token):
                    # 在线程中调用回调，需要通过 asyncio 发送 WebSocket 消息
                    asyncio.run_coroutine_threadsafe(
                        websocket.send_text(json.dumps({"type": "chunk", "content": token})),
                        loop
                    )

                def run_agent_stream():
                    return agent_with_tools(
                        query=query,
                        session_id=conversation_id,
                        stream_callback=stream_callback
                    )

                full_answer = await loop.run_in_executor(None, run_agent_stream)

            elif mode == "langgraph":
                # LangGraph 模式：使用高级智能体编排
                loop = asyncio.get_event_loop()

                def stream_callback(token):
                    # 在线程中调用回调，需要通过 asyncio 发送 WebSocket 消息
                    asyncio.run_coroutine_threadsafe(
                        websocket.send_text(json.dumps({"type": "chunk", "content": token})),
                        loop
                    )

                def run_langgraph_stream():
                    return run_agent(
                        query=query,
                        session_id=conversation_id,
                        stream_callback=stream_callback
                    )

                full_answer = await loop.run_in_executor(None, run_langgraph_stream)

            else:
                # 默认 RAG 模式
                async for chunk in _stream_rag_query(
                    query=query,
                    session_id=conversation_id,
                    use_web=use_web,
                ):
                    full_answer += chunk
                    await websocket.send_text(json.dumps({"type": "chunk", "content": chunk}))

            await websocket.send_text(json.dumps({"type": "end", "content": full_answer}))

    except WebSocketDisconnect:
        pass


@router.get("/history/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    history = _conv_store.get_history(conversation_id)
    return {"conversation_id": conversation_id, "history": history}


@router.get("/sessions")
async def get_conversation_sessions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    logs = (
        db.query(models.ConversationLog)
        .filter(models.ConversationLog.user_id == current_user.id)
        .order_by(models.ConversationLog.created_at.desc())
        .all()
    )

    sessions = {}
    for log in logs:
        if log.conversation_id not in sessions:
            sessions[log.conversation_id] = {
                "conversation_id": log.conversation_id,
                "last_message": log.query,
                "last_time": log.created_at.isoformat() if log.created_at else "",
                "user_id": current_user.id,
                "created_at": log.created_at.isoformat() if log.created_at else "",
            }

    return list(sessions.values())


@router.delete("/history/{conversation_id}")
async def delete_conversation_history(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _conv_store.clear_session(conversation_id)

    db.query(models.ConversationLog).filter(
        models.ConversationLog.conversation_id == conversation_id,
        models.ConversationLog.user_id == current_user.id,
    ).delete()
    db.commit()

    return {"message": "Conversation history deleted"}
