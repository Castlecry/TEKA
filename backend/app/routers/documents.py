import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import KNOWLEDGE_BASE_DIR, SUPPORTED_EXTENSIONS
from app.database import get_db
from app.routers.auth import get_current_user

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/", response_model=List[schemas.DocumentResponse])
async def get_documents(
    knowledge_base_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Document)
    if knowledge_base_id:
        query = query.filter(models.Document.knowledge_base_id == knowledge_base_id)
    documents = query.offset(skip).limit(limit).all()
    return documents


@router.get("/{doc_id}", response_model=schemas.DocumentResponse)
async def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/upload", response_model=schemas.DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    knowledge_base_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    kb = db.query(models.KnowledgeBase).filter(models.KnowledgeBase.id == knowledge_base_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}")

    kb_dir = os.path.join(KNOWLEDGE_BASE_DIR, str(knowledge_base_id))
    os.makedirs(kb_dir, exist_ok=True)

    file_path = os.path.join(kb_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    db_doc = models.Document(
        knowledge_base_id=knowledge_base_id,
        filename=file.filename,
        file_path=file_path,
        file_type=file_ext[1:],
        size=os.path.getsize(file_path),
        uploaded_by=current_user.id,
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()


@router.get("/{doc_id}/preview")
async def preview_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found")

    file_ext = os.path.splitext(doc.filename)[1].lower()
    if file_ext in (".txt", ".md"):
        with open(doc.file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return {"content": content, "file_type": file_ext}
    elif file_ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"):
        return {"message": "Image file - OCR text available via parsing pipeline", "file_type": file_ext}
    else:
        return {"message": "Preview not supported for this file type", "file_type": file_ext}
