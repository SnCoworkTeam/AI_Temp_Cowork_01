# 快速迁移指南

## ⚡ 快速执行（3步）

### 1. 启动数据库（如果未运行）

```bash
# Docker方式
docker-compose -f docker-compose.db.yml up -d

# 或检查是否已运行
docker ps --filter "name=enterprise-ai-postgres"
```

### 2. 设置环境变量

**Windows PowerShell**:
```powershell
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:DB_USER = "ai_user"
$env:DB_PASSWORD = "ai_password"
$env:DB_NAME = "ai_platform"
```

**Linux/Mac**:
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=ai_user
export DB_PASSWORD=ai_password
export DB_NAME=ai_platform
```

### 3. 执行迁移

```bash
cd database
pip install -r requirements.txt  # 如果还没安装
alembic upgrade head
```

---

## ✅ 验证

```bash
# 检查迁移版本
alembic current

# 应该显示: 020 (head)
```

---

## 🆘 如果遇到问题

1. **数据库未运行**: 先启动数据库服务
2. **连接失败**: 检查环境变量和端口
3. **依赖缺失**: 运行 `pip install -r requirements.txt`

详细说明请查看 [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)








