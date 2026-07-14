from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Enum,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    permissions = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    department = Column(String(50))
    role_id = Column(Integer, ForeignKey("roles.id"))
    status = Column(Boolean, default=True)
    avatar = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role = relationship("Role")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    department = Column(String(50))
    owner_id = Column(Integer, ForeignKey("users.id"))
    embedding_model = Column(String(100), default="qwen3-embedding:0.6b")
    is_personal = Column(Boolean, default=False)  # 是否为个人知识库
    module = Column(String(50), default="general")  # 所属模块: policy / tech / admin / general
    is_shared = Column(Boolean, default=False)  # 是否为共享知识库（管理员创建，所有用户可见）
    is_locked = Column(Boolean, default=False)  # 是否为系统内置的初始知识库（不可删除）
    status = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"))
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500))
    file_type = Column(String(50))
    size = Column(Integer)
    chunk_count = Column(Integer, default=0)
    status = Column(Enum("pending", "processing", "completed", "failed", name="document_status"), default="pending")
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    knowledge_base = relationship("KnowledgeBase")
    uploaded_by_user = relationship("User")


class ConversationLog(Base):
    __tablename__ = "conversation_logs"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(50), index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    query = Column(Text)
    answer = Column(Text)
    sources = Column(JSON)
    knowledge_base_ids = Column(JSON)
    module = Column(String(50), default="general")  # 关联的模块
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(50), index=True)
    message_id = Column(String(50))
    user_id = Column(Integer, ForeignKey("users.id"))
    rating = Column(Integer)
    correction = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class ConversationFavorite(Base):
    __tablename__ = "conversation_favorites"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(50), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200))  # 收藏时的对话标题（第一条用户消息）
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
