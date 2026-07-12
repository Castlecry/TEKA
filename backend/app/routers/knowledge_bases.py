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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    existing_kb = db.query(models.KnowledgeBase).filter(models.KnowledgeBase.name == kb.name).first()
    if existing_kb:
        raise HTTPException(status_code=400, detail="Knowledge base name already exists")
    db_kb = models.KnowledgeBase(**kb.model_dump(), owner_id=current_user.id)
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

    document_count = db.query(models.Document).filter(models.Document.knowledge_base_id == kb.id).count()
    if document_count > 0:
        raise HTTPException(status_code=400, detail="Cannot delete knowledge base with documents")

    db.delete(kb)
    db.commit()
