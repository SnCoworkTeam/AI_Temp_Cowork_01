#!/bin/bash
# 检查知识库服务问题

echo "=========================================="
echo "知识库服务诊断"
echo "=========================================="

# 1. 检查服务状态
echo ""
echo "[1] 检查服务状态..."
docker ps --filter "name=knowledge" --format "table {{.Names}}\t{{.Status}}"

# 2. 检查最近的错误日志
echo ""
echo "[2] 检查最近的错误日志..."
docker logs enterprise-ai-knowledge-base --tail 50 2>&1 | grep -i "error\|exception\|failed\|timeout" | tail -20

# 3. 检查文档处理中的文档
echo ""
echo "[3] 检查处理中的文档..."
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT id, filename, status, created_at FROM documents WHERE status = 'processing' ORDER BY created_at DESC LIMIT 5;" 2>&1

# 4. 检查向量数据库连接
echo ""
echo "[4] 检查向量数据库..."
docker exec enterprise-ai-knowledge-base ls -la /app/chroma_db 2>&1 | head -5

# 5. 检查内存使用
echo ""
echo "[5] 检查容器资源使用..."
docker stats enterprise-ai-knowledge-base --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo ""
echo "=========================================="
echo "诊断完成"
echo "=========================================="


