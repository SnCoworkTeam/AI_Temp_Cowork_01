# 手动部署命令（服务器端执行）

由于PowerShell脚本执行环境问题，请按照以下步骤手动执行。

## 步骤1: 在本地Windows机器上传文件

打开PowerShell，执行：

```powershell
cd E:\enterprise-ai-platform

$ServerIP = "43.143.139.197"
$ServerUser = "root"
$ServerPath = "/opt/enterprise-ai-platform"

# 上传所有迁移文件
$migrationFiles = Get-ChildItem -Path "database\src\migrations\versions" -Filter "*.py"
foreach ($file in $migrationFiles) {
    $remotePath = "$ServerPath/database/src/migrations/versions/$($file.Name)"
    scp $file.FullName "${ServerUser}@${ServerIP}:$remotePath"
}

# 上传Alembic配置文件
scp "database\src\migrations\alembic.ini" "${ServerUser}@${ServerIP}:$ServerPath/database/src/migrations/"
scp "database\src\migrations\env.py" "${ServerUser}@${ServerIP}:$ServerPath/database/src/migrations/"
```

## 步骤2: SSH到服务器

```bash
ssh root@43.143.139.197
# 或者使用密钥
ssh -i "E:\enterprise-ai-platform\enterprise_ai_platform.pem" root@43.143.139.197
```

## 步骤3: 在服务器上执行以下命令

```bash
# 1. 进入项目目录
cd /opt/enterprise-ai-platform

# 2. 停止服务
docker-compose stop metadata-service web-ui api-gateway agent-service

# 3. 备份数据库
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p /backup/database
docker exec enterprise-ai-postgres pg_dump -U ai_user -d ai_platform -F c -f /tmp/backup_${TIMESTAMP}.dump
docker cp enterprise-ai-postgres:/tmp/backup_${TIMESTAMP}.dump /backup/database/

# 4. 重建数据库（删除所有数据）
docker exec enterprise-ai-postgres psql -U ai_user -d postgres -c "DROP DATABASE IF EXISTS ai_platform;"
docker exec enterprise-ai-postgres psql -U ai_user -d postgres -c "CREATE DATABASE ai_platform;"

# 5. 执行所有迁移（从头开始）
docker-compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  metadata-service sh -c 'cd /database/src/migrations && alembic upgrade head'

# 6. 验证版本（应该是028）
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT version_num FROM alembic_version;"

# 7. 验证heads（应该只有一个，值为028）
docker-compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  metadata-service sh -c 'cd /database/src/migrations && alembic heads'

# 8. 验证字段
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'data_assets' AND column_name = 'classification_dimensions';"

# 9. 启动服务
docker-compose up -d metadata-service web-ui api-gateway agent-service

# 10. 等待服务启动
sleep 15

# 11. 检查服务状态
docker ps --filter name=metadata-service
docker ps --filter name=web-ui
docker ps --filter name=api-gateway
docker ps --filter name=agent-service
```

## 验证部署

```bash
# 检查数据库版本（应该是028）
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT version_num FROM alembic_version;"

# 检查heads（应该只有一个）
docker-compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  metadata-service sh -c 'cd /database/src/migrations && alembic heads'

# 测试API
curl http://43.143.139.197:8005/api/health
```

## 如果SSH连接失败

1. **检查网络连接**
2. **尝试直接连接**：
   ```powershell
   ssh root@43.143.139.197
   ```
3. **如果提示需要密钥**：
   ```powershell
   ssh -i "E:\enterprise-ai-platform\enterprise_ai_platform.pem" root@43.143.139.197
   ```
4. **检查密钥文件权限**（如果需要）：
   ```powershell
   icacls "E:\enterprise-ai-platform\enterprise_ai_platform.pem"
   ```
