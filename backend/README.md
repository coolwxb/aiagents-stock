# AI股票分析系统 - 后端API

基于FastAPI的AI股票分析系统后端服务。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置相关参数：

```bash
cp .env.example .env
```

### 3. 运行服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问API文档

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 项目结构

```
backend/
├── app/
│   ├── api/          # API路由
│   ├── core/         # 核心功能
│   ├── models/       # 数据模型
│   ├── schemas/      # Pydantic模式
│   ├── services/     # 业务逻辑
│   ├── data/         # 数据获取
│   ├── agents/       # AI智能体
│   ├── db/           # 数据库操作
│   ├── tasks/        # 后台任务
│   └── utils/        # 工具函数
├── alembic/          # 数据库迁移
├── requirements.txt  # 依赖列表
└── README.md         # 本文档
```

## 开发说明

### API版本

当前API版本为 v1，路径前缀为 `/api/v1`

### 数据库迁移

使用Alembic进行数据库迁移：

```bash
# 创建迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head
```

## 许可证

MIT License

