from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    department: Optional[str] = None
    role_id: Optional[int] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    role_id: Optional[int] = None
    status: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    status: bool
    created_at: datetime
    updated_at: datetime
    role: Optional["RoleResponse"] = None

    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Optional[List[str]] = []


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    id: int
    permissions: Optional[List[str]] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeBaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    department: Optional[str] = None
    embedding_model: Optional[str] = "qwen3-embedding:0.6b"
    module: Optional[str] = "general"  # policy / tech / admin / general


class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    embedding_model: Optional[str] = None
    module: Optional[str] = None


class KnowledgeBaseResponse(KnowledgeBaseBase):
    id: int
    owner_id: int
    is_personal: Optional[bool] = False
    is_shared: Optional[bool] = False
    is_locked: Optional[bool] = False
    status: bool
    created_at: datetime
    updated_at: datetime
    document_count: Optional[int] = 0

    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    filename: str
    file_type: str
    size: int


class DocumentCreate(BaseModel):
    knowledge_base_id: int


class DocumentResponse(DocumentBase):
    id: int
    knowledge_base_id: int
    file_path: Optional[str] = None
    chunk_count: int
    status: str
    uploaded_by: int
    uploaded_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    knowledge_base_ids: Optional[List[int]] = None
    use_web: Optional[bool] = False
    mode: Optional[str] = "rag"  # rag, agent, langgraph
    provider: Optional[str] = "api"  # api=DeepSeek, local=Ollama
    module: Optional[str] = "general"  # policy / tech / admin / general


class ChatResponse(BaseModel):
    answer: str
    sources: Optional[List[Dict[str, str]]] = []


class ConversationLogResponse(BaseModel):
    id: int
    conversation_id: str
    user_id: int
    query: str
    answer: str
    sources: Optional[List[Dict[str, str]]] = []
    knowledge_base_ids: Optional[List[int]] = []
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    conversation_id: str
    message_id: Optional[str] = None
    rating: int
    correction: Optional[str] = None


class FeedbackResponse(FeedbackCreate):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SystemConfigResponse(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class StatisticsResponse(BaseModel):
    total_knowledge_bases: int
    total_documents: int
    total_conversations: int
    active_users: int
    hot_questions: List[Dict[str, Any]]


class CodeSearchRequest(BaseModel):
    query: str
    knowledge_base_ids: Optional[List[int]] = None


class CodeSearchResponse(BaseModel):
    results: List[Dict[str, Any]]


class BugAnalysisRequest(BaseModel):
    error_log: str


class BugAnalysisResponse(BaseModel):
    analysis: str
    suggestions: List[str]


class PandasAnalysisRequest(BaseModel):
    file_id: int
    query: str


class PandasAnalysisResponse(BaseModel):
    result: str
    chart_data: Optional[Dict[str, Any]] = None


class ToolCall(BaseModel):
    name: str
    args: Dict[str, Any]
