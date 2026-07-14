import os
import sys
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import KNOWLEDGE_BASE_DIR, SUPPORTED_EXTENSIONS
from app.database import get_db
from app.routers.auth import get_current_user

# 将 backend 根目录加入 path
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/", response_model=List[schemas.DocumentResponse])
async def get_documents(
    knowledge_base_id: Optional[int] = None,
    filename: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Document)
    if knowledge_base_id:
        query = query.filter(models.Document.knowledge_base_id == knowledge_base_id)
    if filename:
        query = query.filter(models.Document.filename.contains(filename))
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


def _process_uploaded_document(doc_id: int, file_path: str, kb_id: int, filename: str):
    """后台处理上传的文档：解析 → 切片 → 向量化 → 存储"""
    from app.database import SessionLocal
    from document_service import process_document

    db = SessionLocal()
    try:
        doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
        if not doc:
            return

        doc.status = "processing"
        db.commit()

        result = process_document(file_path, kb_id=kb_id, source=filename)

        if result["success"]:
            doc.status = "completed"
            doc.chunk_count = result["chunk_count"]
        else:
            doc.status = "failed"
            print(f"[Upload] 文档处理失败: {result.get('error')}")
    except Exception as e:
        doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
        if doc:
            doc.status = "failed"
        print(f"[Upload] 文档处理异常: {e}")
    finally:
        db.commit()
        db.close()


@router.post("/upload", response_model=schemas.DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    knowledge_base_id: int,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
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
    content_bytes = await file.read()
    with open(file_path, "wb") as f:
        f.write(content_bytes)

    file_size = os.path.getsize(file_path)

    # 创建文档记录（状态：pending，后台处理）
    db_doc = models.Document(
        knowledge_base_id=knowledge_base_id,
        filename=file.filename,
        file_path=file_path,
        file_type=file_ext[1:],
        size=file_size,
        uploaded_by=current_user.id,
        status="pending",
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # 后台异步处理文档
    background_tasks.add_task(
        _process_uploaded_document,
        doc_id=db_doc.id,
        file_path=file_path,
        kb_id=knowledge_base_id,
        filename=file.filename,
    )

    return db_doc


@router.post("/{doc_id}/regenerate")
async def regenerate_document_vectors(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """重新生成文档向量（解析 → 切片 → 向量化 → 存储）"""
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    # 更新状态为处理中
    doc.status = "processing"
    db.commit()

    try:
        from document_service import regenerate_for_document
        result = regenerate_for_document(doc.file_path, source=doc.filename)

        if result["success"]:
            doc.status = "completed"
            doc.chunk_count = result["chunk_count"]
        else:
            doc.status = "failed"
    except Exception as e:
        doc.status = "failed"
        print(f"[Regenerate] 异常: {e}")

    db.commit()
    db.refresh(doc)

    return {
        "message": "向量重新生成完成" if doc.status == "completed" else "向量生成失败",
        "status": doc.status,
        "chunk_count": doc.chunk_count,
    }


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
    """预览文档解析后的内容"""
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found")

    file_ext = os.path.splitext(doc.filename)[1].lower()

    # 纯文本直接返回
    if file_ext in (".txt", ".md"):
        with open(doc.file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return {
            "content": content,
            "file_type": file_ext,
            "filename": doc.filename,
            "chunk_count": doc.chunk_count,
            "status": doc.status,
        }

    # 其他格式：尝试用 MinerU 解析后返回
    try:
        from document_parser import parse_document
        content = parse_document(doc.file_path)
        return {
            "content": content,
            "file_type": file_ext,
            "filename": doc.filename,
            "chunk_count": doc.chunk_count,
            "status": doc.status,
        }
    except Exception as e:
        # 如果 MinerU 不可用，返回基本信息
        return {
            "content": f"[预览不可用] 文件类型 {file_ext} 需要 MinerU API 进行解析。\n错误: {str(e)}",
            "file_type": file_ext,
            "filename": doc.filename,
            "chunk_count": doc.chunk_count,
            "status": doc.status,
        }
