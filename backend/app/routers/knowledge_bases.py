from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.routers.auth import get_current_user

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.get("/", response_model=List[schemas.KnowledgeBaseResponse])
async def get_knowledge_bases(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.KnowledgeBase)
    
    # 判断用户是否是管理员
    is_admin = current_user.role and "all" in (current_user.role.permissions or [])
    
    if is_admin:
        # 管理员可以看到所有知识库（全局 + 个人）
        pass
    else:
        # 普通用户只能看到全局知识库和自己的个人知识库
        query = query.filter(
            (models.KnowledgeBase.is_personal == False) |  # 全局知识库
            ((models.KnowledgeBase.is_personal == True) & (models.KnowledgeBase.owner_id == current_user.id))  # 自己的个人知识库
        )
    
    if name:
        query = query.filter(models.KnowledgeBase.name.contains(name))
    if department:
        query = query.filter(models.KnowledgeBase.department == department)
    
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
    is_personal: bool = False,  # 新增参数：是否为个人知识库
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # 判断用户是否是管理员
    is_admin = current_user.role and "all" in (current_user.role.permissions or [])
    
    # 普通用户只能创建个人知识库
    if not is_admin and not is_personal:
        raise HTTPException(status_code=403, detail="普通用户只能创建个人知识库")
    
    # 检查知识库名称是否重复（只在自己的范围内检查）
    query = db.query(models.KnowledgeBase).filter(models.KnowledgeBase.name == kb.name)
    if is_personal:
        # 个人知识库：只检查自己的个人知识库
        query = query.filter(
            models.KnowledgeBase.owner_id == current_user.id,
            models.KnowledgeBase.is_personal == True
        )
    else:
        # 全局知识库：检查所有全局知识库
        query = query.filter(models.KnowledgeBase.is_personal == False)
    
    existing_kb = query.first()
    if existing_kb:
        raise HTTPException(status_code=400, detail="Knowledge base name already exists")
    
    db_kb = models.KnowledgeBase(
        **kb.model_dump(),
        owner_id=current_user.id,
        is_personal=is_personal
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
    
    # 判断用户是否是管理员
    is_admin = current_user.role and "all" in (current_user.role.permissions or [])
    
    # 权限检查：管理员可以修改所有知识库，普通用户只能修改自己的个人知识库
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
    
    # 判断用户是否是管理员
    is_admin = current_user.role and "all" in (current_user.role.permissions or [])
    
    # 权限检查：管理员可以删除所有知识库，普通用户只能删除自己的个人知识库
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
