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
    scoped_id = f"{current_user.id}:{conversation_id}"

    history = _conv_store.get_history(scoped_id)

    provider = message.provider or "api"

    # 根据模式选择不同的处理方式
    if message.mode == "agent":
        # Agent模式使用 Function Calling（仅 API 模式支持 tools）
        if provider == "local":
            # 本地模型不支持 Function Calling，回退到 RAG 模式
            response = _rag_chain.rag_query(
                query=message.message,
                session_id=scoped_id,
                use_web=message.use_web or False,
                use_rerank=True,
                use_rewrite=True,
                provider="local",
            )
        else:
            response = agent_with_tools(
                query=message.message,
                session_id=scoped_id
            )
        _conv_store.save_message(scoped_id, "user", message.message)
        _conv_store.save_message(scoped_id, "assistant", response)
    elif message.mode == "langgraph":
        # LangGraph 模式（仅 API 模式支持）
        if provider == "local":
            response = _rag_chain.rag_query(
                query=message.message,
                session_id=scoped_id,
                use_web=message.use_web or False,
                use_rerank=True,
                use_rewrite=True,
                provider="local",
            )
        else:
            response = run_agent(
                query=message.message,
                session_id=scoped_id
            )
        _conv_store.save_message(scoped_id, "user", message.message)
        _conv_store.save_message(scoped_id, "assistant", response)
    else:
        # 默认RAG模式（rag_chain 内部自动保存对话到 Redis）
        response = _rag_chain.rag_query(
            query=message.message,
            session_id=scoped_id,
            use_web=message.use_web or False,
            use_rerank=True,
            use_rewrite=True,
            provider=provider,
        )

    # 提取最终回答文本（兼容 dict 和 str 两种返回格式）
    if isinstance(response, dict):
        answer_text = response.get("answer", str(response))
    else:
        answer_text = str(response)

    # 从 Redis 获取来源（简化处理：检索阶段没有直接返回 sources）
    sources = []

    db_log = models.ConversationLog(
        conversation_id=conversation_id,
        user_id=current_user.id,
        query=message.message,
        answer=answer_text,
        sources=sources,
        knowledge_base_ids=message.knowledge_base_ids or [],
        module=message.module or "general",
    )
    db.add(db_log)
    db.commit()

    return {"answer": response, "sources": sources, "conversation_id": conversation_id}


@router.post("/stream")
async def send_message_stream(
    message: schemas.ChatMessage,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """流式聊天（HTTP SSE）"""
    allowed, remaining = _redis_cache.check_rate_limit(current_user.id)
    if not allowed:
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

    _redis_cache.track_question(message.message)
    conversation_id = message.conversation_id or str(uuid.uuid4())
    scoped_id = f"{current_user.id}:{conversation_id}"
    provider = message.provider or "api"

    _user_id = current_user.id
    _kb_ids = message.knowledge_base_ids or []

    # 如果用户没有指定知识库，根据模块自动选择共享知识库
    if not _kb_ids and message.module:
        module_kbs = db.query(models.KnowledgeBase).filter(
            models.KnowledgeBase.module == message.module,
            models.KnowledgeBase.is_shared == True,
            models.KnowledgeBase.status == True,
        ).all()
        if module_kbs:
            _kb_ids = [kb.id for kb in module_kbs]

    _full_answer = []  # 仅累计 content（保存到数据库用），不含 reasoning
    _attachments: list[dict] = []

    # 捕获当前事件循环引用，用于跨线程安全地往队列写数据
    _loop = asyncio.get_running_loop()

    async def run_rag():
        """在后台线程中执行 RAG 查询"""
        def on_token(chunk_type: str, token: str):
            # chunk_type: "reasoning" (推理模型的思考) 或 "content" (最终回答)
            if chunk_type == "content":
                _full_answer.append(token)
            # 跨线程安全：使用 call_soon_threadsafe 把 put_nowait 调度到事件循环
            try:
                _loop.call_soon_threadsafe(_queue.put_nowait, {"type": chunk_type, "text": token})
            except Exception:
                pass

        try:
            if message.mode == "agent" and provider != "local":
                result = await asyncio.to_thread(
                    agent_with_tools,
                    message.message, scoped_id, on_token,
                )
                if isinstance(result, dict):
                    answer = result.get("answer", "")
                    _attachments.extend(result.get("attachments", []))
                else:
                    answer = str(result)

                _try_rescue_document_hallucination(answer, _attachments, message.message)

                _conv_store.save_message(scoped_id, "user", message.message)
                _conv_store.save_message(scoped_id, "assistant", answer)
                if not _full_answer:
                    _full_answer.append(answer)
                    _loop.call_soon_threadsafe(_queue.put_nowait, {"type": "content", "text": answer})
            elif message.mode == "langgraph" and provider != "local":
                answer = await asyncio.to_thread(
                    run_agent,
                    message.message, scoped_id, on_token,
                )
                _conv_store.save_message(scoped_id, "user", message.message)
                _conv_store.save_message(scoped_id, "assistant", answer)
                if not _full_answer:
                    _full_answer.append(answer)
                    _loop.call_soon_threadsafe(_queue.put_nowait, {"type": "content", "text": answer})
            else:
                await asyncio.to_thread(
                    _rag_chain.rag_query,
                    query=message.message,
                    session_id=scoped_id,
                    use_web=message.use_web or False,
                    use_rerank=True,
                    use_rewrite=True,
                    stream_callback=on_token,
                    provider=provider,
                )
        except Exception as e:
            try:
                _loop.call_soon_threadsafe(_queue.put_nowait, f"__ERROR__:{str(e)}")
            except Exception:
                pass
            print(f"[Stream] RAG 查询异常: {e}")
        finally:
            _loop.call_soon_threadsafe(_queue.put_nowait, "__DONE__")

    async def save_log():
        """保存对话日志"""
        from app.database import SessionLocal

        # 等待流式输出完成（通过 _is_stream_done 事件判断）
        try:
            await asyncio.wait_for(_is_stream_done.wait(), timeout=120)
        except asyncio.TimeoutError:
            print("[Stream] save_log 等待超时，强制保存")

        full_text = "".join(_full_answer)
        db = SessionLocal()
        try:
            db_log = models.ConversationLog(
                conversation_id=conversation_id,
                user_id=_user_id,
                query=message.message,
                answer=full_text,
                sources=[],
                knowledge_base_ids=_kb_ids,
                module=message.module or "general",
            )
            db.add(db_log)
            db.commit()
        except Exception as e:
            print(f"[Stream] 保存对话日志失败: {e}")
            db.rollback()
        finally:
            db.close()

    _queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
    _is_stream_done = asyncio.Event()

    asyncio.create_task(run_rag())
    asyncio.create_task(save_log())

    async def stream_generator():
        # 第一帧：发送会话 ID（前端可用于同步状态）
        yield f"data: {json.dumps({'type': 'meta', 'conversation_id': conversation_id, 'module': message.module}, ensure_ascii=False)}\n\n"
        while True:
            item = await _queue.get()
            if item == "__DONE__":
                # 流式结束前，如果有附件，发送附件元数据
                if _attachments:
                    yield f"data: {json.dumps({'type': 'attachments', 'items': _attachments}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
                _is_stream_done.set()
                break
            if isinstance(item, str) and item.startswith("__ERROR__:"):
                yield f"data: {json.dumps({'type': 'error', 'content': item[10:]}, ensure_ascii=False)}\n\n"
                _is_stream_done.set()
            elif isinstance(item, dict):
                # 推理模型的流式 chunk：包含 type (reasoning/content) + text
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
            else:
                # 兼容旧格式：纯字符串 token
                yield f"data: {json.dumps({'type': 'chunk', 'content': item}, ensure_ascii=False)}\n\n"

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
    scoped_id = f"{current_user.id}:{conv_id}"

    response = _rag_chain.rag_query(
        query=full_query,
        session_id=scoped_id,
        use_web=False,
        use_rerank=True,
        use_rewrite=False,
    )

    answer_text = response.get("answer", str(response)) if isinstance(response, dict) else str(response)

    db_log = models.ConversationLog(
        conversation_id=conv_id,
        user_id=current_user.id,
        query=f"[文件: {file.filename}] {message}",
        answer=answer_text,
        sources=[],
        knowledge_base_ids=[],
        module=message.module or "general",
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
    is_admin = current_user.role and "all" in (current_user.role.permissions or [])
    scoped_id = f"{current_user.id}:{conversation_id}" if not is_admin else conversation_id
    history = _conv_store.get_history(scoped_id)
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
                "module": log.module or "general",
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
    scoped_id = f"{current_user.id}:{conversation_id}"
    _conv_store.clear_session(scoped_id)

    db.query(models.ConversationLog).filter(
        models.ConversationLog.conversation_id == conversation_id,
        models.ConversationLog.user_id == current_user.id,
    ).delete()
    db.commit()

    return {"message": "Conversation history deleted"}


def _try_rescue_document_hallucination(answer: str, attachments: list, user_query: str) -> None:
    """
    兜底：检测 LLM 在 answer 里"幻觉"地提到了"文档已生成"/"点击下载"等措辞，
    但实际没有调 create_document 工具（attachments 为空）。
    一旦命中，直接用 LLM 的回答内容生成一份文档并加入 attachments。
    """
    if attachments:
        return  # 已经有真实附件，不处理

    hallucination_keywords = [
        "文档已生成", "文档已创建", "已生成", "文件已生成",
        "点击下载", "点击以下链接下载", "下载链接", "Word 文档",
    ]
    if not any(kw in answer for kw in hallucination_keywords):
        return

    # 不像是文档生成请求
    if not any(kw in user_query for kw in ["生成", "导出", "做成", "下载", "Word", "PDF", "word", "pdf", "文档", "文件"]):
        return

    # 从 answer 里去掉"链接"等装饰性文字，作为文档内容
    content = answer.strip()
    # 简单去除外层包装
    if len(content) < 20:
        return

    # 检测格式
    fmt = "pdf" if "pdf" in user_query.lower() else "word"
    title = "生成的文档"
    # 尝试从用户 query 提取标题
    for prefix in ["做成", "生成", "导出"]:
        if prefix in user_query:
            title = user_query.split(prefix, 1)[1].strip(" ：:，,。了吗呢吗？?")
            break

    try:
        from document_generator import generate_document
        file_id, filename, file_path = generate_document(content, format=fmt, title=title or "生成的文档")
        size_bytes = os.path.getsize(file_path)
        attachments.append({
            "file_id": file_id,
            "filename": filename,
            "format": fmt,
            "size_kb": round(size_bytes / 1024, 1),
            "download_url": f"/files/download/{file_id}",
        })
        print(f"[Rescue] 兜底成功：幻觉检测，强制生成文档 {filename}")
    except Exception as e:
        print(f"[Rescue] 兜底失败: {e}")


def _require_admin(current_user: models.User):
    if not current_user.role or "all" not in (current_user.role.permissions or []):
        raise HTTPException(status_code=403, detail="需要管理员权限")


@router.delete("/logs/{log_id}")
async def delete_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """删除单条对话日志（仅管理员）"""
    _require_admin(current_user)
    log = db.query(models.ConversationLog).filter(models.ConversationLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")

    user_scoped_id = f"{log.user_id}:{log.conversation_id}"
    _conv_store.clear_session(user_scoped_id)

    db.delete(log)
    db.commit()
    return {"message": "日志已删除", "log_id": log_id}


@router.delete("/logs")
async def delete_logs_batch(
    log_ids: list[int],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """批量删除对话日志（仅管理员）"""
    _require_admin(current_user)
    if not log_ids:
        raise HTTPException(status_code=400, detail="请选择要删除的日志")

    logs = db.query(models.ConversationLog).filter(models.ConversationLog.id.in_(log_ids)).all()
    deleted_count = 0
    for log in logs:
        user_scoped_id = f"{log.user_id}:{log.conversation_id}"
        _conv_store.clear_session(user_scoped_id)
        db.delete(log)
        deleted_count += 1
    db.commit()
    return {"message": f"已删除 {deleted_count} 条日志", "deleted_count": deleted_count}


# ========== 消息反馈 ==========

from pydantic import BaseModel


class FeedbackRequest(BaseModel):
    conversation_id: str
    message_id: str
    rating: int  # 1 = 点赞, -1 = 点踩
    correction: Optional[str] = None


@router.post("/feedback")
async def submit_feedback(
    req: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """提交消息反馈（点赞/点踩 + 修正意见，rating=0 表示取消反馈）"""
    if req.rating not in (-1, 0, 1):
        raise HTTPException(status_code=400, detail="rating 只能是 -1、0 或 1")

    existing = db.query(models.Feedback).filter(
        models.Feedback.conversation_id == req.conversation_id,
        models.Feedback.message_id == req.message_id,
        models.Feedback.user_id == current_user.id,
    ).first()

    # rating = 0 表示取消/删除反馈
    if req.rating == 0:
        if existing:
            db.delete(existing)
            db.commit()
        return {"message": "反馈已取消", "rating": 0}

    if existing:
        existing.rating = req.rating
        existing.correction = req.correction
        db.commit()
        return {"message": "反馈已更新", "id": existing.id}

    fb = models.Feedback(
        conversation_id=req.conversation_id,
        message_id=req.message_id,
        user_id=current_user.id,
        rating=req.rating,
        correction=req.correction,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return {"message": "反馈已提交", "id": fb.id}


@router.get("/feedback/{conversation_id}/{message_id}")
async def get_feedback(
    conversation_id: str,
    message_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """获取某条消息的当前用户反馈"""
    fb = db.query(models.Feedback).filter(
        models.Feedback.conversation_id == conversation_id,
        models.Feedback.message_id == message_id,
        models.Feedback.user_id == current_user.id,
    ).first()
    if not fb:
        return {"rating": 0, "correction": ""}
    return {"rating": fb.rating, "correction": fb.correction or ""}


# ========== 对话收藏 ==========

class FavoriteRequest(BaseModel):
    conversation_id: str
    title: Optional[str] = None


@router.post("/favorite")
async def toggle_favorite(
    req: FavoriteRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """收藏/取消收藏对话（切换）"""
    existing = db.query(models.ConversationFavorite).filter(
        models.ConversationFavorite.conversation_id == req.conversation_id,
        models.ConversationFavorite.user_id == current_user.id,
    ).first()

    if existing:
        # 已收藏 → 取消收藏
        db.delete(existing)
        db.commit()
        return {"favorited": False, "message": "已取消收藏"}

    # 未收藏 → 添加收藏
    fav = models.ConversationFavorite(
        conversation_id=req.conversation_id,
        user_id=current_user.id,
        title=req.title,
    )
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return {"favorited": True, "id": fav.id, "message": "已收藏"}


@router.get("/favorites")
async def get_favorites(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """获取当前用户的收藏列表"""
    favorites = (
        db.query(models.ConversationFavorite)
        .filter(models.ConversationFavorite.user_id == current_user.id)
        .order_by(models.ConversationFavorite.created_at.desc())
        .all()
    )
    return [
        {
            "id": f.id,
            "conversation_id": f.conversation_id,
            "title": f.title,
            "created_at": f.created_at.isoformat() if f.created_at else "",
        }
        for f in favorites
    ]


@router.get("/favorites/check/{conversation_id}")
async def check_favorite(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """检查某个对话是否已收藏"""
    fav = db.query(models.ConversationFavorite).filter(
        models.ConversationFavorite.conversation_id == conversation_id,
        models.ConversationFavorite.user_id == current_user.id,
    ).first()
    return {"favorited": fav is not None}
