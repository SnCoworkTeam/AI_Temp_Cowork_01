# 完整部署手动步骤指南

由于PowerShell脚本可能存在执行环境问题，这里提供手动执行步骤。

## 前提条件
- Docker和Docker Compose已在服务器上运行
- 已通过SSH连接到服务器：`ssh root@43.143.139.197`

## 步骤1: 上传迁移文件到服务器

在本地Windows机器上执行：

```powershell
# 上传所有迁移文件
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

## 步骤2: 在服务器上执行部署脚本

SSH连接到服务器后执行：

```bash
# 1. 停止服务
cd /opt/enterprise-ai-platform
docker-compose stop metadata-service web-ui api-gateway agent-service

# 2. 备份数据库
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p /backup/database
docker exec enterprise-ai-postgres pg_dump -U ai_user -d ai_platform -F c -f /tmp/backup_${TIMESTAMP}.dump
docker cp enterprise-ai-postgres:/tmp/backup_${TIMESTAMP}.dump /backup/database/

# 3. 重建数据库（删除所有数据）
docker exec enterprise-ai-postgres psql -U ai_user -d postgres -c "DROP DATABASE IF EXISTS ai_platform;"
docker exec enterprise-ai-postgres psql -U ai_user -d postgres -c "CREATE DATABASE ai_platform;"

# 4. 执行所有迁移
docker-compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  metadata-service sh -c 'cd /database/src/migrations && alembic upgrade head'

# 5. 验证版本
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT version_num FROM alembic_version;"

# 6. 验证heads（应该只有一个）
docker-compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  metadata-service sh -c 'cd /database/src/migrations && alembic heads'

# 7. 验证字段
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'data_assets' AND column_name = 'classification_dimensions';"

# 8. 启动服务
docker-compose up -d metadata-service web-ui api-gateway agent-service

# 9. 等待服务启动
sleep 15

# 10. 检查服务状态
docker ps --filter name=metadata-service
docker ps --filter name=web-ui
docker ps --filter name=api-gateway
docker ps --filter name=agent-service
```

## 或者使用自动化脚本

### 方法1: 上传bash脚本到服务器执行

```powershell
# 在本地执行
scp scripts/deploy-to-server.sh root@43.143.139.197:/tmp/
ssh root@43.143.139.197 "chmod +x /tmp/deploy-to-server.sh && /tmp/deploy-to-server.sh"
```

### 方法2: 直接在服务器上创建并执行

```bash
# SSH到服务器后
cat > /tmp/deploy.sh << 'EOF'
#!/bin/bash
# ... (脚本内容)
EOF

chmod +x /tmp/deploy.sh
/tmp/deploy.sh
```

## 验证部署

```bash
# 检查数据库版本（应该是028）
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT version_num FROM alembic_version;"

# 检查heads（应该只有一个，值为028）
docker-compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  metadata-service sh -c 'cd /database/src/migrations && alembic heads'

# 检查字段
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "\d data_assets" | grep classification_dimensions

# 测试API
curl http://43.143.139.197:8005/api/health
```

## 故障排查

如果SSH连接失败：
1. 检查网络连接
2. 检查SSH密钥配置
3. 尝试手动SSH连接：`ssh root@43.143.139.197`

如果迁移失败：
1. 查看详细错误信息
2. 检查迁移文件是否完整上传
3. 检查Alembic配置文件是否正确
4. 参考 `docs/deployment/migration-troubleshooting.md`








