import json
import sys
import os
import uuid
import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse

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
import redis_cache as _redis_cache
from agent_tools import agent_with_tools
from langgraph_agent import run_agent
from config import TOP_K, WEB_SEARCH_COUNT

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message")
async def send_message(
    message: schemas.ChatMessage,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # 速率限制检查
    allowed, remaining = _redis_cache.check_rate_limit(current_user.id)
    if not allowed:
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

    # 追踪热门问题
    _redis_cache.track_question(message.message)

    conversation_id = message.conversation_id or str(uuid.uuid4())

    history = _conv_store.get_history(conversation_id)

    provider = message.provider or "api"

    # 根据模式选择不同的处理方式
    if message.mode == "agent":
        # Agent模式使用 Function Calling（仅 API 模式支持 tools）
        if provider == "local":
            # 本地模型不支持 Function Calling，回退到 RAG 模式
            response = _rag_chain.rag_query(
                query=message.message,
                session_id=conversation_id,
                use_web=message.use_web or False,
                use_rerank=True,
                use_rewrite=True,
                provider="local",
            )
        else:
            response = agent_with_tools(
                query=message.message,
                session_id=conversation_id
            )
        _conv_store.save_message(conversation_id, "user", message.message)
        _conv_store.save_message(conversation_id, "assistant", response)
    elif message.mode == "langgraph":
        # LangGraph 模式（仅 API 模式支持）
        if provider == "local":
            response = _rag_chain.rag_query(
                query=message.message,
                session_id=conversation_id,
                use_web=message.use_web or False,
                use_rerank=True,
                use_rewrite=True,
                provider="local",
            )
        else:
            response = run_agent(
                query=message.message,
                session_id=conversation_id
            )
        _conv_store.save_message(conversation_id, "user", message.message)
        _conv_store.save_message(conversation_id, "assistant", response)
    else:
        # 默认RAG模式（rag_chain 内部自动保存对话到 Redis）
        response = _rag_chain.rag_query(
            query=message.message,
            session_id=conversation_id,
            use_web=message.use_web or False,
            use_rerank=True,
            use_rewrite=True,
            provider=provider,
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


@router.post("/stream")
async def send_message_stream(
    message: schemas.ChatMessage,
    current_user: models.User = Depends(get_current_user),
):
    """流式聊天（HTTP SSE），使用 asyncio.Queue 实现真正的实时流式输出"""
    allowed, remaining = _redis_cache.check_rate_limit(current_user.id)
    if not allowed:
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

    _redis_cache.track_question(message.message)
    conversation_id = message.conversation_id or str(uuid.uuid4())
    provider = message.provider or "api"

    # 捕获变量供生成器使用
    _user_id = current_user.id
    _kb_ids = message.knowledge_base_ids or []

    import queue as _std_queue

    # 使用线程安全队列桥接同步回调和异步流
    sync_queue: _std_queue.Queue = _std_queue.Queue()

    async def generate():
        from app.database import SessionLocal

        full_answer_parts = []

        def sync_on_token(token: str):
            """同步回调（在线程池中执行）：将 token 放入线程安全队列"""
            full_answer_parts.append(token)
            sync_queue.put(token)

        try:
            # 执行 RAG/Agent/LangGraph
            if message.mode == "agent" and provider != "local":
                answer = agent_with_tools(query=message.message, session_id=conversation_id)
                _conv_store.save_message(conversation_id, "user", message.message)
                _conv_store.save_message(conversation_id, "assistant", answer)
                full_answer_parts.append(answer)
                sync_queue.put(answer)
            elif message.mode == "langgraph" and provider != "local":
                answer = run_agent(query=message.message, session_id=conversation_id)
                _conv_store.save_message(conversation_id, "user", message.message)
                _conv_store.save_message(conversation_id, "assistant", answer)
                full_answer_parts.append(answer)
                sync_queue.put(answer)
            else:
                # 在线程池中执行阻塞的 rag_query
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: _rag_chain.rag_query(
                        query=message.message,
                        session_id=conversation_id,
                        use_web=message.use_web or False,
                        use_rerank=True,
                        use_rewrite=True,
                        stream_callback=sync_on_token,
                        provider=provider,
                    )
                )
        except Exception as e:
            error_msg = f"生成回答时出错: {str(e)}"
            sync_queue.put(f"__ERROR__:{error_msg}")
            print(f"[Stream] RAG 查询异常: {e}")

        # 标记结束
        sync_queue.put("__DONE__")

        # 保存到 PostgreSQL（使用独立的数据库会话）
        full_answer = "".join(full_answer_parts) if full_answer_parts else ""
        db = SessionLocal()
        try:
            db_log = models.ConversationLog(
                conversation_id=conversation_id,
                user_id=_user_id,
                query=message.message,
                answer=full_answer,
                sources=[],
                knowledge_base_ids=_kb_ids,
            )
            db.add(db_log)
            db.commit()
        except Exception as e:
            print(f"[Stream] 保存对话日志失败: {e}")
            db.rollback()
        finally:
            db.close()

    async def stream_generator():
        """从线程安全队列读取数据，通过 asyncio.Queue 中转 yield"""
        async_queue: asyncio.Queue = asyncio.Queue()

        def reader_thread():
            """后台线程：从 sync_queue 读取并放入 async_queue"""
            while True:
                token = sync_queue.get()
                if token == "__DONE__":
                    async_queue.put_nowait(None)
                    break
                if token.startswith("__ERROR__:"):
                    async_queue.put_nowait(f"data: {json.dumps({'type': 'chunk', 'content': token[10:]})}\n\n")
                else:
                    async_queue.put_nowait(f"data: {json.dumps({'type': 'chunk', 'content': token})}\n\n")

        import threading
        t = threading.Thread(target=reader_thread, daemon=True)
        t.start()

        while True:
            chunk = await async_queue.get()
            if chunk is None:
                yield "data: [DONE]\n\n"
                break
            yield chunk

    # 启动后台任务，将 generate() 作为并发协程运行
    generate_task = asyncio.create_task(generate())

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/upload-and-ask")
async def upload_and_ask(
    file: UploadFile = File(...),
    message: str = "请分析这个文件的内容",
    conversation_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """上传文件并提问——通过 MinerU 解析后结合 RAG 回答"""
    import tempfile
    from document_parser import parse_document

    # 保存上传文件到临时目录
    suffix = os.path.splitext(file.filename or "upload")[1] or ".txt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        # 解析文件内容
        parsed_content = parse_document(tmp_path)
    except Exception as e:
        os.unlink(tmp_path)
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")

    os.unlink(tmp_path)

    # 构建查询：将文件内容作为上下文，用户消息作为问题
    full_query = f"文件内容：\n{parsed_content[:4000]}\n\n用户问题：{message}"

    conv_id = conversation_id or str(uuid.uuid4())

    response = _rag_chain.rag_query(
        query=full_query,
        session_id=conv_id,
        use_web=False,
        use_rerank=True,
        use_rewrite=False,
    )

    db_log = models.ConversationLog(
        conversation_id=conv_id,
        user_id=current_user.id,
        query=f"[文件: {file.filename}] {message}",
        answer=response,
        sources=[],
        knowledge_base_ids=[],
    )
    db.add(db_log)
    db.commit()

    return {
        "answer": response,
        "conversation_id": conv_id,
        "filename": file.filename,
    }


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


@router.get("/logs")
async def get_conversation_logs(
    search: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """获取对话日志列表。管理员看全部，普通用户只看自己的。"""
    query = db.query(models.ConversationLog)

    # 权限过滤
    is_admin = current_user.role and "all" in (current_user.role.permissions or [])
    if not is_admin:
        query = query.filter(models.ConversationLog.user_id == current_user.id)

    # 搜索关键词（匹配问题或回答）
    if search:
        keyword = f"%{search}%"
        query = query.filter(
            models.ConversationLog.query.ilike(keyword) |
            models.ConversationLog.answer.ilike(keyword)
        )

    # 按用户名筛选（仅管理员）
    if user_id and is_admin:
        try:
            uid = int(user_id)
            query = query.filter(models.ConversationLog.user_id == uid)
        except ValueError:
            # 按用户名查找
            user = db.query(models.User).filter(models.User.username == user_id).first()
            if user:
                query = query.filter(models.ConversationLog.user_id == user.id)

    # 日期范围
    if start_date:
        query = query.filter(models.ConversationLog.created_at >= start_date)
    if end_date:
        query = query.filter(models.ConversationLog.created_at <= end_date + " 23:59:59")

    # 排序和分页
    logs = query.order_by(models.ConversationLog.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": log.id,
            "conversation_id": log.conversation_id,
            "user_id": log.user_id,
            "query": log.query,
            "answer": log.answer,
            "sources": log.sources or [],
            "knowledge_base_ids": log.knowledge_base_ids or [],
            "created_at": log.created_at.isoformat() if log.created_at else "",
        }
        for log in logs
    ]


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
