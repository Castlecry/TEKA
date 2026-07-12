# 开发规范检查清单

## 环境配置
- [ ] 后端 `.env` 文件已创建，包含所有必需的环境变量
- [ ] `config/app_config.yaml` 已创建，包含完整的业务配置
- [ ] `app/config.py` 能正确加载 `.env` 和 `yaml` 配置
- [ ] 配置对象可通过 `from app.config import settings` 访问

## 数据库层
- [ ] `database.py` 配置了 SQLAlchemy 异步引擎
- [ ] 所有模型继承自 Base 基类
- [ ] Base 包含 id、created_at、updated_at、is_deleted 字段
- [ ] 用户模型包含用户名、密码哈希、邮箱、角色、状态字段
- [ ] 知识库模型包含名称、描述、负责人、Embedding 模型配置
- [ ] 文档模型包含文件名、路径、大小、知识库 ID、状态字段
- [ ] 对话日志模型包含会话 ID、用户 ID、问题、答案、来源、时间戳

## 核心组件
- [ ] `security.py` 实现了 JWT 生成和验证
- [ ] `security.py` 实现了密码哈希和验证
- [ ] `dependencies.py` 提供了获取当前用户的依赖
- [ ] `dependencies.py` 提供了获取数据库 session 的依赖
- [ ] `exceptions.py` 定义了统一的 AppException
- [ ] 全局异常处理器已注册到 FastAPI 应用

## API 规范
- [ ] 所有接口以 `/api/` 为前缀
- [ ] 统一响应格式：`{"code": 200, "message": "success", "data": {}}`
- [ ] 错误响应格式：`{"code": 400, "message": "错误描述", "data": null}`
- [ ] RESTful 风格：GET 查询、POST 创建、PUT 更新、DELETE 删除

## LLM 双模式
- [ ] `LLM_MODE=local` 时使用 Ollama 的 OpenAI 兼容接口
- [ ] `LLM_MODE=remote` 时使用 DeepSeek API
- [ ] 两种模式都通过 OpenAI 兼容接口调用
- [ ] 配置切换无需修改代码

## 前端项目
- [ ] Vue 3 + Vite 项目已初始化
- [ ] 所有必需依赖已安装（vue-router, pinia, axios, element-plus, marked, highlight.js）
- [ ] Axios 实例已封装，配置了请求/响应拦截器
- [ ] 路由配置已完成
- [ ] 用户状态管理 store 已创建

## 前端布局
- [ ] Layout.vue 实现了侧边栏 + 顶栏布局
- [ ] Login.vue 登录页面已创建
- [ ] Dashboard.vue 首页仪表盘已创建（占位）

## 命名规范
- [ ] 后端文件名使用 snake_case
- [ ] 后端类名使用 PascalCase
- [ ] 后端函数/变量使用 snake_case
- [ ] API 路径使用 kebab-case
- [ ] 前端组件文件名使用 PascalCase
- [ ] 前端 JS 文件名使用 camelCase
- [ ] 前端变量/函数使用 camelCase

## 外部工具
- [ ] Ollama 安装说明已提供（本地模式需要）
- [ ] 前端依赖安装命令已提供
