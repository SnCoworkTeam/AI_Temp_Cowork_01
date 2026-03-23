#!/bin/bash
# 紧急修复部署脚本
# 执行数据库迁移和部署错误处理

set -e  # 遇到错误立即退出

echo "=================================="
echo "LuminaOS 紧急修复部署"
echo "=================================="
echo ""

# 1. 备份数据库
echo "[1/5] 备份数据库..."
sudo -u postgres pg_dump enterprise_ai_platform > /tmp/enterprise_ai_platform_backup_$(date +%Y%m%d_%H%M%S).sql
echo "✅ 数据库备份完成"
echo ""

# 2. 执行数据库迁移
echo "[2/5] 执行数据库迁移..."
cd /opt/enterprise-ai-platform/database

# 确保alembic已安装
pip3 install alembic psycopg2-binary sqlalchemy --quiet

# 执行迁移
echo "  - 执行迁移 002: 修复 DocumentChunk 向量字段"
python3 -c "
import sys
sys.path.insert(0, '/opt/enterprise-ai-platform')
from database.src.migrations.versions import 002_fix_document_chunk_vector as m002
m002.upgrade()
print('✅ 002 完成')
"

echo "  - 执行迁移 003: 修复 KnowledgeGraphNode 字段映射"
python3 -c "
import sys
sys.path.insert(0, '/opt/enterprise-ai-platform')
from database.src.migrations.versions import 003_fix_knowledge_graph_node as m003
m003.upgrade()
print('✅ 003 完成')
"

echo "  - 执行迁移 004: 修复 WorkflowConnection 外键约束"
python3 -c "
import sys
sys.path.insert(0, '/opt/enterprise-ai-platform')
from database.src.migrations.versions import 004_fix_workflow_connection as m004
m004.upgrade()
print('✅ 004 完成')
"

echo "  - 执行迁移 005: 添加性能索引"
python3 -c "
import sys
sys.path.insert(0, '/opt/enterprise-ai-platform')
from database.src.migrations.versions import 005_add_performance_indexes as m005
m005.upgrade()
print('✅ 005 完成')
"

echo "✅ 所有数据库迁移完成"
echo ""

# 3. 验证数据库修复
echo "[3/5] 验证数据库修复..."
psql -U postgres -d enterprise_ai_platform -c "\d document_chunks" | grep -E "(embedding|embedding_model)" && echo "  ✅ DocumentChunk 修复成功"
psql -U postgres -d enterprise_ai_platform -c "\d knowledge_graph_nodes" | grep -E "(label|node_type|properties|document_id)" && echo "  ✅ KnowledgeGraphNode 修复成功"
psql -U postgres -d enterprise_ai_platform -c "\d workflow_connections" | grep -E "uuid" && echo "  ✅ WorkflowConnection 修复成功"
psql -U postgres -d enterprise_ai_platform -c "\di" | grep -E "(idx_workflow_execution_status|idx_document_chunk)" && echo "  ✅ 性能索引创建成功"
echo "✅ 数据库验证完成"
echo ""

# 4. 安装依赖
echo "[4/5] 安装新依赖..."
pip3 install httpx tenacity --quiet
echo "✅ 依赖安装完成"
echo ""

# 5. 重启服务
echo "[5/5] 重启服务以应用修复..."
cd /opt/enterprise-ai-platform

# 停止所有服务
echo "  - 停止所有服务..."
docker-compose down

# 启动服务
echo "  - 启动服务..."
docker-compose up -d

# 等待服务启动
echo "  - 等待服务启动..."
sleep 15

# 检查服务状态
echo "  - 检查服务状态..."
docker-compose ps

echo ""
echo "=================================="
echo "✅ 紧急修复部署完成！"
echo "=================================="
echo ""
echo "接下来的步骤："
echo "1. 测试知识库文档上传和搜索功能"
echo "2. 测试工作流创建和执行功能"
echo "3. 测试SSO登录功能"
echo "4. 监控服务日志：docker-compose logs -f"
echo ""
