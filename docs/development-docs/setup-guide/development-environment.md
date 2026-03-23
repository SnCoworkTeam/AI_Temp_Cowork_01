# 开发环境搭建指南

## 系统要求

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd enterprise-ai-platform
```

### 2. 安装Python依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 启动数据库服务

```bash
docker-compose -f docker-compose.db.yml up -d
```

### 4. 配置环境变量

```bash
# 复制环境变量模板
cp env.example .env

# 编辑.env文件，配置数据库连接等信息
```

### 5. 运行数据库迁移

```bash
cd database
alembic upgrade head
```

### 6. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 或单独启动服务
cd mcp-gateway && uvicorn src.main:app --reload
cd workflow-engine && uvicorn src.main:app --reload
cd auth-service && uvicorn src.main:app --reload
cd knowledge-base && uvicorn src.main:app --reload
```

### 7. 启动前端

```bash
cd web-ui
npm install
npm run dev
```

## 验证安装

访问以下URL验证服务是否正常：

- MCP Gateway: http://localhost:8000/api/docs
- Workflow Engine: http://localhost:8001/api/docs
- Auth Service: http://localhost:8002/api/docs
- Knowledge Base: http://localhost:8004/api/docs
- Web UI: http://localhost:3000

## 常见问题

### 端口冲突
如果端口被占用，修改`.env`文件中的端口配置。

### 数据库连接失败
检查PostgreSQL是否启动，确认连接参数正确。

### 依赖安装失败
确保Python和pip版本正确，尝试使用国内镜像源。









