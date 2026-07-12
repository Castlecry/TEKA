from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.routers.auth import get_current_user
from app.security import get_password_hash, verify_password

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    department: Optional[str] = None
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    avatar: Optional[str] = None


class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str


@router.get("/", response_model=ProfileResponse)
async def get_profile(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.put("/", response_model=ProfileResponse)
async def update_profile(
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if data.email is not None:
        existing = db.query(models.User).filter(
            models.User.email == data.email,
            models.User.id != current_user.id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="邮箱已被使用")
        current_user.email = data.email
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.department is not None:
        current_user.department = data.department
    if data.avatar is not None:
        current_user.avatar = data.avatar

    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/password")
async def update_password(
    data: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度不能少于6位")
    current_user.password_hash = get_password_hash(data.new_password)
    db.commit()
    return {"message": "密码修改成功"}
