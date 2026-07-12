# TEKA - 科技企业知识助手

Tech Enterprise Knowledge Assistant - 面向科技企业研发团队的智能知识管理平台与对话机器人。

## 功能特性

- **技术知识智能问答**：API文档问答、SDK手册问答、架构设计问答、代码示例生成
- **智能体工具调用**：代码搜索、Bug分析诊断、Pandas数据分析
- **高级智能体编排**：基于LangGraph的多步推理、状态管理、长短期记忆
- **知识库管理**：多知识库隔离、文档批量上传、自动向量化
- **对话机器人**：多轮对话、流式响应、答案溯源、联网搜索

## 技术栈

### 后端
- FastAPI - Web框架
- PostgreSQL + pgvector - 持久化存储与向量搜索
- Redis - 缓存与对话历史
- OpenSearch - 向量数据库
- Ollama - Embedding模型
- DeepSeek - LLM推理
- LangGraph - 高级智能体编排
- MinerU - 文档解析

### 前端
- Vue 3 + Vite
- Element Plus
- Pinia
- Axios

## 快速开始

### 环境要求
- Python 3.11+
- Docker & Docker Compose

### 启动服务

```bash
cd backend
docker-compose up -d
```

### 初始化数据库

```bash
docker-compose exec rag-app python init_db.py
```

### 访问服务

- API: http://localhost:8888
- 前端: http://localhost:5173
- Swagger文档: http://localhost:8888/docs

## 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 技术负责人 |

## API接口

### 认证
- `POST /auth/login` - 登录
- `POST /auth/register` - 注册
- `GET /auth/me` - 获取当前用户

### 用户管理
- `GET /users/` - 用户列表
- `POST /users/` - 创建用户
- `GET /users/{id}` - 用户详情
- `PUT /users/{id}` - 更新用户
- `DELETE /users/{id}` - 删除用户

### 知识库管理
- `GET /knowledge-bases/` - 知识库列表
- `POST /knowledge-bases/` - 创建知识库
- `GET /knowledge-bases/{id}` - 知识库详情
- `PUT /knowledge-bases/{id}` - 更新知识库
- `DELETE /knowledge-bases/{id}` - 删除知识库

### 文档管理
- `POST /documents/upload` - 上传文档
- `GET /documents/` - 文档列表
- `GET /documents/{id}` - 文档详情
- `GET /documents/{id}/preview` - 预览文档
- `DELETE /documents/{id}` - 删除文档

### 对话
- `POST /chat/message` - 发送消息
- `WS /chat/ws/{conversation_id}` - WebSocket流式对话
- `GET /chat/history/{conversation_id}` - 获取对话历史

## 项目结构

```
TEKA/
├── backend/                    # 后端代码
│   ├── app/                    # 主应用
│   │   ├── routers/            # 路由模块
│   │   ├── services/           # 服务模块
│   │   ├── middleware/         # 中间件
│   │   ├── config.py           # 配置
│   │   ├── database.py         # 数据库连接
│   │   ├── models.py           # 数据库模型
│   │   ├── schemas.py          # Pydantic模式
│   │   ├── security.py         # 安全认证
│   │   └── main.py             # 应用入口
│   ├── docker-compose.yml      # Docker配置
│   ├── Dockerfile
│   ├── requirements.txt
│   └── init_db.py              # 数据库初始化
├── frontend/                   # 前端代码
└── README.md
```

## License

MIT
