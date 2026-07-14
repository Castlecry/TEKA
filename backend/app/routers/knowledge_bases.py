from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.routers.auth import get_current_user

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])

# 模块定义
MODULES = [
    {
        "id": "policy",
        "name": "规章制度",
        "description": "企业规章制度、流程规范、管理制度",
        "icon": "Document",
        "color": "#4f6ef7",
        "example_questions": [
            "报销流程是什么？",
            "请假制度是怎样的？",
            "考勤规定有哪些？",
            "差旅报销标准是什么？",
            "加班申请流程？",
        ],
    },
    {
        "id": "tech",
        "name": "产品技术",
        "description": "技术文档、产品手册、API说明、开发规范",
        "icon": "Monitor",
        "color": "#22c55e",
        "example_questions": [
            "API接口文档在哪？",
            "系统架构是怎样的？",
            "数据库设计规范？",
            "部署流程是什么？",
            "技术选型标准？",
        ],
    },
    {
        "id": "admin",
        "name": "行政服务",
        "description": "办公场地、IT支持、福利政策、行政事务",
        "icon": "OfficeBuilding",
        "color": "#f59e0b",
        "example_questions": [
            "办公场地怎么申请？",
            "IT设备报修流程？",
            "员工福利有哪些？",
            "会议室怎么预定？",
            "办公用品怎么领？",
        ],
    },
    {
        "id": "general",
        "name": "自由问答",
        "description": "通用知识库，回答任何问题",
        "icon": "ChatLineRound",
        "color": "#8b5cf6",
        "example_questions": [
            "什么是RAG技术？",
            "帮我写一份周报",
            "解释一下机器学习",
            "如何提高工作效率？",
        ],
    },
]


@router.get("/modules")
async def get_modules():
    """获取所有模块列表"""
    return MODULES


@router.get("/", response_model=List[schemas.KnowledgeBaseResponse])
async def get_knowledge_bases(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    department: Optional[str] = None,
    module: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.KnowledgeBase)

    # 判断用户是否是管理员
    is_admin = current_user.role and "all" in (current_user.role.permissions or [])

    if is_admin:
        # 管理员可以看到所有知识库
        pass
    else:
        # 普通用户只能看到：共享知识库 + 自己的个人知识库
        query = query.filter(
            (models.KnowledgeBase.is_shared == True)
            | ((models.KnowledgeBase.is_personal == True) & (models.KnowledgeBase.owner_id == current_user.id))
        )

    if name:
        query = query.filter(models.KnowledgeBase.name.contains(name))
    if department:
        query = query.filter(models.KnowledgeBase.department == department)
    if module:
        query = query.filter(models.KnowledgeBase.module == module)

    kbs = query.offset(skip).limit(limit).all()
    for kb in kbs:
        kb.document_count = db.query(models.Document).filter(models.Document.knowledge_base_id == kb.id).count()
    return kbs


@router.get("/{kb_id}", response_model=schemas.KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    kb = db.query(models.KnowledgeBase).filter(models.KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    kb.document_count = db.query(models.Document).filter(models.Document.knowledge_base_id == kb.id).count()
    return kb


@router.post("/", response_model=schemas.KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    kb: schemas.KnowledgeBaseCreate,
    is_personal: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    is_admin = current_user.role and "all" in (current_user.role.permissions or [])

    # 普通用户只能创建个人知识库
    if not is_admin and not is_personal:
        raise HTTPException(status_code=403, detail="普通用户只能创建个人知识库")

    # 检查知识库名称是否重复
    query = db.query(models.KnowledgeBase).filter(models.KnowledgeBase.name == kb.name)
    if is_personal:
        query = query.filter(
            models.KnowledgeBase.owner_id == current_user.id,
            models.KnowledgeBase.is_personal == True,
        )
    else:
        query = query.filter(models.KnowledgeBase.is_personal == False)

    existing_kb = query.first()
    if existing_kb:
        raise HTTPException(status_code=400, detail="Knowledge base name already exists")

    # 管理员为 policy/tech/admin 模块创建的知识库默认共享
    module = kb.module or "general"
    is_shared = is_admin and module != "general" and not is_personal

    db_kb = models.KnowledgeBase(
        **kb.model_dump(),
        owner_id=current_user.id,
        is_personal=is_personal,
        is_shared=is_shared,
    )
    db.add(db_kb)
    db.commit()
    db.refresh(db_kb)
    return db_kb


@router.put("/{kb_id}", response_model=schemas.KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: int,
    kb_update: schemas.KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_kb = db.query(models.KnowledgeBase).filter(models.KnowledgeBase.id == kb_id).first()
    if not db_kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    is_admin = current_user.role and "all" in (current_user.role.permissions or [])

    if not is_admin:
        if db_kb.is_personal and db_kb.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权修改他人的个人知识库")
        elif not db_kb.is_personal:
            raise HTTPException(status_code=403, detail="普通用户无权修改全局知识库")

    for field, value in kb_update.model_dump(exclude_unset=True).items():
        setattr(db_kb, field, value)

    db.commit()
    db.refresh(db_kb)
    return db_kb


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    kb = db.query(models.KnowledgeBase).filter(models.KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # 系统内置的初始知识库不允许删除
    if kb.is_locked:
        raise HTTPException(status_code=403, detail="系统初始知识库不可删除")

    is_admin = current_user.role and "all" in (current_user.role.permissions or [])

    if not is_admin:
        if kb.is_personal and kb.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权删除他人的个人知识库")
        elif not kb.is_personal:
            raise HTTPException(status_code=403, detail="普通用户无权删除全局知识库")

    document_count = db.query(models.Document).filter(models.Document.knowledge_base_id == kb.id).count()
    if document_count > 0:
        raise HTTPException(status_code=400, detail="Cannot delete knowledge base with documents")

    db.delete(kb)
    db.commit()
