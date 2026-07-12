from sqlalchemy.orm import Session

from app.database import engine, SessionLocal
from app import models
from app.security import get_password_hash

DEFAULT_ROLES = [
    {
        "name": "技术负责人",
        "description": "拥有系统所有权限，可管理所有知识库和用户",
        "permissions": ["all"],
    },
    {
        "name": "团队负责人",
        "description": "可管理本团队的知识库和文档",
        "permissions": ["read_all", "write_team", "manage_team_users"],
    },
    {
        "name": "开发工程师",
        "description": "可查询知识库，上传文档",
        "permissions": ["read_all", "write_documents"],
    },
    {
        "name": "测试工程师",
        "description": "仅可查询知识库",
        "permissions": ["read_all"],
    },
]

DEFAULT_USERS = [
    {
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin123",
        "full_name": "管理员",
        "department": "技术部",
        "role_name": "技术负责人",
    },
]


def init_db():
    db = SessionLocal()
    try:
        for role_data in DEFAULT_ROLES:
            existing_role = db.query(models.Role).filter(models.Role.name == role_data["name"]).first()
            if not existing_role:
                role = models.Role(**role_data)
                db.add(role)
                db.commit()
                db.refresh(role)
                print(f"Created role: {role.name}")

        for user_data in DEFAULT_USERS:
            existing_user = db.query(models.User).filter(models.User.username == user_data["username"]).first()
            if not existing_user:
                role = db.query(models.Role).filter(models.Role.name == user_data["role_name"]).first()
                hashed_password = get_password_hash(user_data["password"])
                user = models.User(
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=hashed_password,
                    full_name=user_data["full_name"],
                    department=user_data["department"],
                    role_id=role.id if role else 3,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"Created user: {user.username}")

        print("Database initialization complete!")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
