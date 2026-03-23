#!/bin/bash
# 修复43服务器数据库迁移脚本
# 用途：上传修复后的迁移文件并执行数据库迁移

set -e

echo "=========================================="
echo "修复43服务器数据库迁移"
echo "=========================================="

# 服务器信息
SERVER="ubuntu@43.143.139.197"
KEY_FILE="enterprise_ai_platform.pem"
REMOTE_DIR="/opt/enterprise-ai-platform"

echo ""
echo "步骤1: 上传修复后的迁移文件..."
scp -i "$KEY_FILE" -o StrictHostKeyChecking=no \
    database/src/migrations/versions/028_add_classification_dimensions.py \
    "$SERVER:$REMOTE_DIR/database/src/migrations/versions/"

echo ""
echo "步骤2: 连接到服务器并执行迁移..."
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no "$SERVER" << 'ENDSSH'
cd /opt/enterprise-ai-platform

echo ""
echo "=== 检查当前迁移状态 ==="
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT version_num FROM alembic_version;" 2>&1 | grep -v "^$" | tail -3

echo ""
echo "=== 执行数据库迁移 ==="
cd database
docker exec -w /app/database enterprise-ai-postgres alembic upgrade head 2>&1

echo ""
echo "=== 验证迁移结果 ==="
echo "检查 workflow_metadata 表是否存在..."
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='workflow_metadata';" 2>&1

echo ""
echo "检查 data_assets 表的 classification_dimensions 列..."
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT column_name FROM information_schema.columns WHERE table_name='data_assets' AND column_name='classification_dimensions';" 2>&1

echo ""
echo "=== 重启 metadata-service 容器 ==="
docker restart enterprise-ai-metadata-service

echo ""
echo "=== 等待服务启动 ==="
sleep 5

echo ""
echo "=== 测试 API ==="
curl -s http://localhost:8005/api/data-assets?skip=0&limit=5 | head -20

echo ""
echo "=========================================="
echo "迁移完成！"
echo "=========================================="
ENDSSH

echo ""
echo "脚本执行完成！"
