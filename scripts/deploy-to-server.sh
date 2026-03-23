#!/bin/bash
# 完整部署脚本 - 在服务器上执行
# 使用方法: 上传到服务器后执行 bash deploy-to-server.sh

set -e

SERVER_PATH="/opt/enterprise-ai-platform"

echo "=========================================="
echo "完整部署：同步迁移并启动服务"
echo "=========================================="
echo ""

# 步骤1: 停止服务
echo "[1/8] 停止服务..."
cd $SERVER_PATH
docker-compose stop metadata-service web-ui api-gateway agent-service || true
echo "[OK] 服务已停止"

# 步骤2: 备份数据库
echo ""
echo "[2/8] 备份数据库..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p /backup/database
docker exec enterprise-ai-postgres pg_dump -U ai_user -d ai_platform -F c -f /tmp/backup_${TIMESTAMP}.dump 2>&1 || true
docker cp enterprise-ai-postgres:/tmp/backup_${TIMESTAMP}.dump /backup/database/ 2>&1 || true
echo "[OK] 数据库已备份到 /backup/database/backup_${TIMESTAMP}.dump"

# 步骤3: 重建数据库
echo ""
echo "[3/8] 重建数据库..."
echo "警告：这将删除所有现有数据！"
docker exec enterprise-ai-postgres psql -U ai_user -d postgres -c "DROP DATABASE IF EXISTS ai_platform;" 2>&1 || true
sleep 2
docker exec enterprise-ai-postgres psql -U ai_user -d postgres -c "CREATE DATABASE ai_platform;" 2>&1
echo "[OK] 数据库已重建"

# 步骤4: 执行所有迁移
echo ""
echo "[4/8] 执行数据库迁移（从头开始）..."
echo "这可能需要一些时间，请耐心等待..."
cd $SERVER_PATH
docker-compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  metadata-service sh -c 'cd /database/src/migrations && alembic upgrade head' 2>&1

if [ $? -eq 0 ]; then
    echo "[OK] 数据库迁移成功完成！"
else
    echo "[错误] 数据库迁移失败"
    exit 1
fi

# 步骤5: 验证迁移版本
echo ""
echo "[5/8] 验证迁移版本..."
FINAL_VERSION=$(docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -A -c "SELECT version_num FROM alembic_version;" 2>&1 | tr -d '[:space:]')
echo "数据库版本: $FINAL_VERSION"

# 检查heads
HEADS_RESULT=$(docker-compose run --rm \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=ai_user \
  -e DB_PASSWORD=ai_password \
  -e DB_NAME=ai_platform \
  metadata-service sh -c 'cd /database/src/migrations && alembic heads' 2>&1)
HEAD_COUNT=$(echo "$HEADS_RESULT" | grep -E '^[a-f0-9]+$|^[0-9]+$|^[a-f0-9]+_[a-z_]+$' | wc -l)

echo "Heads数量: $HEAD_COUNT"
if [ "$HEAD_COUNT" -eq 1 ]; then
    echo "[OK] 版本一致，只有一个head"
else
    echo "[警告] 有 $HEAD_COUNT 个heads"
    echo "$HEADS_RESULT"
fi

# 步骤6: 验证字段
echo ""
echo "[6/8] 验证数据库字段..."
FIELD_CHECK=$(docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -A -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'data_assets' AND column_name = 'classification_dimensions';" 2>&1 | tr -d '[:space:]')

if [ "$FIELD_CHECK" -gt 0 ]; then
    echo "[OK] classification_dimensions 字段已存在"
else
    echo "[警告] classification_dimensions 字段不存在"
fi

# 步骤7: 启动服务
echo ""
echo "[7/8] 启动服务..."
cd $SERVER_PATH
docker-compose up -d metadata-service web-ui api-gateway agent-service
echo "[OK] 服务启动命令已执行"
echo "等待服务启动..."
sleep 15

# 步骤8: 验证服务状态
echo ""
echo "[8/8] 验证服务状态..."

SERVICES=("metadata-service" "web-ui" "api-gateway" "agent-service")
for service in "${SERVICES[@]}"; do
    STATUS=$(docker ps --filter name=$service --format '{{.Status}}' 2>&1)
    if echo "$STATUS" | grep -q "Up"; then
        echo "  [OK] $service 运行中"
    else
        echo "  [警告] $service 状态: $STATUS"
    fi
done

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "部署摘要："
echo "  数据库版本: $FINAL_VERSION"
echo "  Heads数量: $HEAD_COUNT"
echo ""
echo "访问地址："
echo "  前端: http://$(hostname -I | awk '{print $1}'):3000"
echo "  API: http://$(hostname -I | awk '{print $1}'):8005"
echo "  元数据管理: http://$(hostname -I | awk '{print $1}'):3000/admin/metadata"
echo ""
