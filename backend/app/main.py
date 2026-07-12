from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app import models
from app.routers import auth, users, knowledge_bases, documents, chat

models.Base.metadata.create_all(bind=engine)

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


@app.get("/")
async def root():
    return {"message": "科技企业知识助手 API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
