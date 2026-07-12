import json
import uuid
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.routers.auth import get_current_user
from app.rag_chain import rag_chain
from app.conversation_store import ConversationStore

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message")
async def send_message(
    message: schemas.ChatMessage,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    conversation_id = message.conversation_id or str(uuid.uuid4())
    conversation_store = ConversationStore()

    history = conversation_store.get_history(conversation_id)
    response, sources = rag_chain.query(
        message.message,
        history=history,
        knowledge_base_ids=message.knowledge_base_ids,
    )

    conversation_store.add_message(conversation_id, message.message, response)

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
    db: Session = Depends(get_db),
):
    await websocket.accept()
    conversation_store = ConversationStore()

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message = message_data.get("message", "")
            knowledge_base_ids = message_data.get("knowledge_base_ids", [])

            history = conversation_store.get_history(conversation_id)

            async for chunk in rag_chain.stream_query(
                message,
                history=history,
                knowledge_base_ids=knowledge_base_ids,
            ):
                await websocket.send_text(json.dumps({"type": "chunk", "content": chunk}))

            response = conversation_store.get_last_response(conversation_id)
            sources = []

            await websocket.send_text(json.dumps({"type": "sources", "content": sources}))
            await websocket.send_text(json.dumps({"type": "end"}))

    except WebSocketDisconnect:
        pass


@router.get("/history/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    conversation_store = ConversationStore()
    history = conversation_store.get_history(conversation_id)
    return {"conversation_id": conversation_id, "history": history}


@router.get("/sessions")
async def get_conversation_sessions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    logs = db.query(models.ConversationLog).filter(
        models.ConversationLog.user_id == current_user.id
    ).order_by(models.ConversationLog.created_at.desc()).all()

    sessions = {}
    for log in logs:
        if log.conversation_id not in sessions:
            sessions[log.conversation_id] = {
                "conversation_id": log.conversation_id,
                "last_message": log.query,
                "last_time": log.created_at,
            }

    return list(sessions.values())


@router.delete("/history/{conversation_id}")
async def delete_conversation_history(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    conversation_store = ConversationStore()
    conversation_store.clear_history(conversation_id)

    db.query(models.ConversationLog).filter(
        models.ConversationLog.conversation_id == conversation_id,
        models.ConversationLog.user_id == current_user.id,
    ).delete()
    db.commit()

    return {"message": "Conversation history deleted"}
