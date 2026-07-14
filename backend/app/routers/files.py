"""文件下载路由"""
import os
import mimetypes
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app import models
from app.database import get_db
from app.security import SECRET_KEY, ALGORITHM
from document_generator import get_file_path

router = APIRouter(prefix="/files", tags=["files"])


def _resolve_user(
    authorization: str | None,
    token: str | None,
    db: Session,
) -> models.User:
    """优先用 Authorization header，否则用 query token"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="需要登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    raw_token: str | None = None
    if authorization and authorization.lower().startswith("bearer "):
        raw_token = authorization[7:]
    elif token:
        raw_token = token

    if not raw_token:
        raise credentials_exception

    try:
        payload = jwt.decode(raw_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    token: str | None = Query(default=None),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """根据 file_id 下载生成的文件（word/pdf），支持 Authorization header 或 query token"""
    _resolve_user(authorization, token, db)  # 鉴权

    file_path = get_file_path(file_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="文件不存在或已过期")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件已被删除")

    filename = os.path.basename(file_path)
    media_type, _ = mimetypes.guess_type(filename)
    if not media_type:
        ext = Path(filename).suffix.lower()
        media_type = {
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".pdf": "application/pdf",
            ".txt": "text/plain",
        }.get(ext, "application/octet-stream")

    # RFC 5987: 中文文件名需要 URL-encode，否则 latin-1 编码会报错
    from urllib.parse import quote
    encoded_filename = quote(filename)

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        },
    )
