from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import engine
from app import models
from app.routers import auth, users, knowledge_bases, documents, chat, profile

models.Base.metadata.create_all(bind=engine)

# 为已有表添加缺失的列（简单迁移）
with engine.connect() as conn:
    # users 表添加 avatar 列
    conn.execute(text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar VARCHAR(500)"
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


@app.get("/")
async def root():
    return {"message": "科技企业知识助手 API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
