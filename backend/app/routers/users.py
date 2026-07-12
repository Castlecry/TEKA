from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.routers.auth import get_current_user
from app.security import get_password_hash

router = APIRouter(prefix="/users", tags=["users"])


def require_admin(current_user: models.User = Depends(get_current_user)):
    """检查用户是否是管理员"""
    if not current_user.role or "all" not in (current_user.role.permissions or []):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


@router.get("/", response_model=List[schemas.UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    username: Optional[str] = None,
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    query = db.query(models.User)
    if username:
        query = query.filter(models.User.username.contains(username))
    if department:
        query = query.filter(models.User.department == department)
    users = query.offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=schemas.UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in user_update.model_dump(exclude_unset=True).items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    db.delete(user)
    db.commit()


@router.get("/roles/", response_model=List[schemas.RoleResponse])
async def get_roles(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    roles = db.query(models.Role).all()
    return roles


@router.post("/roles/", response_model=schemas.RoleResponse)
async def create_role(
    role: schemas.RoleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    existing_role = db.query(models.Role).filter(models.Role.name == role.name).first()
    if existing_role:
        raise HTTPException(status_code=400, detail="Role already exists")
    db_role = models.Role(**role.model_dump())
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role
