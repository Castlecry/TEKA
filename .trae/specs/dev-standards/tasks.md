# Tasks

- [ ] Task 1: 创建后端配置系统
  - [ ] 1.1 创建 `backend/.env` 文件，包含 LLM_MODE、Ollama、DeepSeek、JWT 等环境变量
  - [ ] 1.2 创建 `backend/config/app_config.yaml`，包含应用、服务器、数据库、ChromaDB、文档、检索、聊天、LLM 配置
  - [ ] 1.3 创建 `backend/app/config.py`，加载 .env 和 yaml，导出全局 settings 对象
  - [ ] 1.4 创建 `backend/app/main.py`，初始化 FastAPI 应用，注册配置

- [ ] Task 2: 创建后端数据库层
  - [ ] 2.1 创建 `backend/app/database.py`，配置 SQLAlchemy 异步引擎和 session
  - [ ] 2.2 创建 `backend/app/models/base.py`，定义 Base 基类（id, created_at, updated_at, is_deleted）
  - [ ] 2.3 创建 `backend/app/models/user.py`，用户模型
  - [ ] 2.4 创建 `backend/app/models/knowledge_base.py`，知识库模型
  - [ ] 2.5 创建 `backend/app/models/document.py`，文档模型
  - [ ] 2.6 创建 `backend/app/models/conversation.py`，对话日志模型

- [ ] Task 3: 创建后端核心组件
  - [ ] 3.1 创建 `backend/app/core/security.py`，JWT 生成/验证、密码哈希
  - [ ] 3.2 创建 `backend/app/core/dependencies.py`，依赖注入（获取当前用户、数据库 session）
  - [ ] 3.3 创建 `backend/app/core/exceptions.py`，统一异常处理

- [ ] Task 4: 初始化前端项目
  - [ ] 4.1 在 `frontend/` 目录初始化 Vue 3 + Vite 项目
  - [ ] 4.2 安装前端依赖：vue-router, pinia, axios, element-plus, marked, highlight.js
  - [ ] 4.3 创建 `frontend/src/utils/request.js`，封装 Axios 实例，配置拦截器
  - [ ] 4.4 创建 `frontend/src/router/index.js`，配置基础路由
  - [ ] 4.5 创建 `frontend/src/stores/user.js`，用户状态管理

- [ ] Task 5: 创建前端基础布局
  - [ ] 5.1 创建 `frontend/src/components/Layout.vue`，侧边栏 + 顶栏布局
  - [ ] 5.2 创建 `frontend/src/views/Login.vue`，登录页面
  - [ ] 5.3 创建 `frontend/src/views/Dashboard.vue`，首页仪表盘（占位）

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
- [Task 4] depends on [Task 1]
- [Task 5] depends on [Task 4]
