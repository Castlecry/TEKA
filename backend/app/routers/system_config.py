"""系统配置 API 路由"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import models
from app.database import get_db
from app.routers.auth import get_current_user

router = APIRouter(prefix="/system/config", tags=["system"])


def require_admin(current_user: models.User = Depends(get_current_user)):
    if not current_user.role or "all" not in (current_user.role.permissions or []):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


@router.get("/")
async def get_all_configs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """获取所有系统配置（普通用户也可读取）"""
    configs = db.query(models.SystemConfig).all()
    result = {}
    for c in configs:
        result[c.key] = c.value
    return result


@router.post("/")
async def save_configs(
    config: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """批量保存系统配置（仅管理员）"""
    saved = 0
    for key, value in config.items():
        if key == "id":
            continue
        existing = db.query(models.SystemConfig).filter(
            models.SystemConfig.key == key
        ).first()
        if existing:
            existing.value = str(value)
        else:
            db.add(models.SystemConfig(key=key, value=str(value)))
        saved += 1

    db.commit()
    return {"message": f"已保存 {saved} 项配置", "count": saved}
