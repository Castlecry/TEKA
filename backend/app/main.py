from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, func
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app import models
from app.routers import auth, users, knowledge_bases, documents, chat, profile, finetune, system_config, files

models.Base.metadata.create_all(bind=engine)

# 为已有表添加缺失的列（简单迁移）
with engine.connect() as conn:
    # users 表添加 avatar 列
    conn.execute(text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar VARCHAR(500)"
    ))
    # knowledge_bases 表添加 is_personal 列
    conn.execute(text(
        "ALTER TABLE knowledge_bases ADD COLUMN IF NOT EXISTS is_personal BOOLEAN DEFAULT FALSE"
    ))
    conn.commit()

app = FastAPI(title="科技企业知识助手", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(knowledge_bases.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(profile.router)
app.include_router(finetune.router)
app.include_router(system_config.router)
app.include_router(files.router)


@app.get("/")
async def root():
    return {"message": "科技企业知识助手 API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """获取仪表盘统计数据（带 Redis 缓存）"""
    import sys, os
    _BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _BACKEND_DIR not in sys.path:
        sys.path.insert(0, _BACKEND_DIR)
    import redis_cache as _redis_cache

    # 尝试从缓存获取
    cached = _redis_cache.get_dashboard_stats()
    if cached:
        return cached

    # 计算统计数据
    total_kbs = db.query(func.count(models.KnowledgeBase.id)).scalar() or 0
    total_docs = db.query(func.count(models.Document.id)).scalar() or 0
    total_convs = db.query(func.count(models.ConversationLog.id)).scalar() or 0
    active_users = db.query(func.count(models.User.id)).filter(
        models.User.status == True
    ).scalar() or 0

    hot_questions = _redis_cache.get_hot_questions(10)

    stats = {
        "total_knowledge_bases": total_kbs,
        "total_documents": total_docs,
        "total_conversations": total_convs,
        "active_users": active_users,
        "hot_questions": hot_questions,
    }

    # 缓存结果
    _redis_cache.set_dashboard_stats(stats)

    return stats
