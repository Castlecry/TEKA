import json
import os
import sys
from datetime import datetime
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
    status_filter: Optional[str] = None,
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
    if status_filter:
        query = query.filter(models.Document.status == status_filter)
    # 待审核的文档排在最前面
    documents = query.order_by(
        models.Document.status == "pending_review",  # True=1 排前面
        models.Document.uploaded_at.desc(),
    ).offset(skip).limit(limit).all()
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


def _process_uploaded_document(doc_id: int, file_path: str, kb_id: int, filename: str, user_id: int):
    """后台处理上传的文档：内容审核 → 解析 → 切片 → 向量化 → 存储"""
    from app.database import SessionLocal
    from document_service import process_document
    from content_moderator import moderate_document, save_audit_record

    db = SessionLocal()
    try:
        doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
        if not doc:
            return

        # ===== 第一步：内容合规审核 =====
        print(f"[Audit] 正在审核文档: {filename} ...")
        try:
            from document_parser import parse_document
            text_content = parse_document(file_path)
        except Exception as e:
            print(f"[Audit] 文档解析失败，跳过审核: {e}")
            text_content = ""

        if text_content:
            audit_result = moderate_document(text_content, filename)
            audit_id = save_audit_record(
                document_id=doc_id,
                filename=filename,
                knowledge_base_id=kb_id,
                user_id=user_id,
                result=audit_result,
                db_session=db,
            )
            print(f"[Audit] 审核结果: {audit_result['verdict']} (置信度: {audit_result['confidence']})")

            if audit_result["verdict"] == "BLOCK":
                # 红灯：自动拒绝并删除文件
                doc.status = "rejected"
                doc.rejection_reason = f"内容违规: {'; '.join(audit_result['reasons'][:3])}"
                db.commit()
                try:
                    os.unlink(file_path)
                except Exception:
                    pass
                print(f"[Audit] 文档已拒绝并删除: {filename}")
                return

            elif audit_result["verdict"] == "REVIEW":
                # 黄灯：等待人工审核
                doc.status = "pending_review"
                doc.audit_id = audit_id
                db.commit()
                print(f"[Audit] 文档等待人工审核: {filename}")
                return

            # 绿灯：PASS，继续处理
        else:
            # 无法解析内容，记录审核但继续处理
            audit_result = {"verdict": "REVIEW", "confidence": 0.3, "reasons": ["无法解析文档内容"], "categories": []}
            audit_id = save_audit_record(
                document_id=doc_id, filename=filename,
                knowledge_base_id=kb_id, user_id=user_id,
                result=audit_result, db_session=db,
            )
            doc.audit_id = audit_id

        # ===== 第二步：正常处理文档 =====
        doc.status = "processing"
        doc.audit_status = "passed"
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

    # 后台异步处理文档（含内容审核）
    background_tasks.add_task(
        _process_uploaded_document,
        doc_id=db_doc.id,
        file_path=file_path,
        kb_id=knowledge_base_id,
        filename=file.filename,
        user_id=current_user.id,
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
        result = regenerate_for_document(doc.file_path, source=doc.filename, knowledge_base_id=doc.knowledge_base_id)

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


# ========== 内容审核管理 ==========

@router.get("/audit/pending")
async def get_pending_audits(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """获取待人工审核的文档列表（仅管理员）"""
    if not current_user.role or "all" not in (current_user.role.permissions or []):
        raise HTTPException(status_code=403, detail="仅管理员可访问")

    docs = (
        db.query(models.Document)
        .filter(models.Document.status == "pending_review")
        .order_by(models.Document.uploaded_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    results = []
    for doc in docs:
        audit = None
        if doc.audit_id:
            audit = db.query(models.ContentAuditLog).filter(
                models.ContentAuditLog.id == doc.audit_id
            ).first()

        results.append({
            "id": doc.id,
            "filename": doc.filename,
            "knowledge_base_id": doc.knowledge_base_id,
            "uploaded_by": doc.uploaded_by,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else "",
            "size": doc.size,
            "file_type": doc.file_type,
            "audit": {
                "id": audit.id if audit else None,
                "verdict": audit.verdict if audit else "",
                "confidence": audit.confidence if audit else 0,
                "categories": json.loads(audit.categories) if audit and audit.categories else [],
                "reasons": json.loads(audit.reasons) if audit and audit.reasons else [],
                "summary": audit.summary if audit else "",
            } if audit else None,
        })

    return results


@router.post("/audit/{doc_id}/approve")
async def approve_document(
    doc_id: int,
    comment: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """人工审核通过（绿灯），继续处理文档"""
    if not current_user.role or "all" not in (current_user.role.permissions or []):
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if doc.status != "pending_review":
        raise HTTPException(status_code=400, detail="该文档不在待审核状态")

    # 更新审核记录
    if doc.audit_id:
        audit = db.query(models.ContentAuditLog).filter(
            models.ContentAuditLog.id == doc.audit_id
        ).first()
        if audit:
            audit.status = "approved"
            audit.reviewer_id = current_user.id
            audit.reviewer_comment = comment or "人工审核通过"
            audit.reviewed_at = datetime.utcnow()

    # 更新文档状态，继续处理
    doc.status = "processing"
    doc.audit_status = "passed"
    db.commit()

    # 后台处理文档
    from document_service import process_document
    try:
        result = process_document(doc.file_path, kb_id=doc.knowledge_base_id, source=doc.filename)
        if result["success"]:
            doc.status = "completed"
            doc.chunk_count = result["chunk_count"]
        else:
            doc.status = "failed"
    except Exception as e:
        doc.status = "failed"
        print(f"[Audit Approve] 文档处理失败: {e}")

    db.commit()
    return {"message": "审核通过，文档已开始处理", "status": doc.status}


@router.post("/audit/{doc_id}/reject")
async def reject_document(
    doc_id: int,
    reason: str = "",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """人工审核拒绝（红灯），删除文档"""
    if not current_user.role or "all" not in (current_user.role.permissions or []):
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if doc.status != "pending_review":
        raise HTTPException(status_code=400, detail="该文档不在待审核状态")

    # 更新审核记录
    if doc.audit_id:
        audit = db.query(models.ContentAuditLog).filter(
            models.ContentAuditLog.id == doc.audit_id
        ).first()
        if audit:
            audit.status = "rejected"
            audit.reviewer_id = current_user.id
            audit.reviewer_comment = reason or "人工审核拒绝"
            audit.reviewed_at = datetime.utcnow()

    doc.status = "rejected"
    doc.audit_status = "rejected"
    doc.rejection_reason = reason or "人工审核拒绝"
    db.commit()

    # 删除文件
    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    return {"message": "审核拒绝，文档已删除"}


@router.get("/audit/logs")
async def get_audit_logs(
    verdict: Optional[str] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """获取审核日志列表（仅管理员）"""
    if not current_user.role or "all" not in (current_user.role.permissions or []):
        raise HTTPException(status_code=403, detail="仅管理员可访问")

    query = db.query(models.ContentAuditLog)
    if verdict:
        query = query.filter(models.ContentAuditLog.verdict == verdict)
    if status_filter:
        query = query.filter(models.ContentAuditLog.status == status_filter)

    logs = query.order_by(models.ContentAuditLog.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": log.id,
            "document_id": log.document_id,
            "filename": log.filename,
            "knowledge_base_id": log.knowledge_base_id,
            "user_id": log.user_id,
            "verdict": log.verdict,
            "confidence": log.confidence,
            "categories": json.loads(log.categories) if log.categories else [],
            "reasons": json.loads(log.reasons) if log.reasons else [],
            "summary": log.summary,
            "status": log.status,
            "reviewer_comment": log.reviewer_comment,
            "created_at": log.created_at.isoformat() if log.created_at else "",
            "reviewed_at": log.reviewed_at.isoformat() if log.reviewed_at else "",
        }
        for log in logs
    ]
