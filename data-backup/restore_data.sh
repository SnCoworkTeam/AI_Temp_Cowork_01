#!/bin/bash
set -e
cd /opt/enterprise-ai-platform
REMOTE_DATA_DIR="/opt/enterprise-ai-platform/data-backup"

echo "=== 恢复PostgreSQL数据库 ==="
if [ -f "\/postgres_backup.sql" ]; then
    echo "正在恢复数据库..."
    docker exec -i enterprise-ai-postgres psql -U ai_user -d ai_platform < "\/postgres_backup.sql" 2>&1 || echo "⚠️  数据库恢复可能有问题"
    echo "✅ 数据库恢复完成"
fi

echo ""
echo "=== 恢复ChromaDB数据 ==="
if [ -f "\/chroma_backup.tar.gz" ]; then
    echo "正在恢复ChromaDB..."
    docker exec enterprise-ai-knowledge-base sh -c "rm -rf /app/chroma_db/*" 2>&1 || true
    docker cp "\/chroma_backup.tar.gz" enterprise-ai-knowledge-base:/tmp/chroma_backup.tar.gz
    docker exec enterprise-ai-knowledge-base sh -c "cd /app && tar -xzf /tmp/chroma_backup.tar.gz -C chroma_db 2>&1 && rm /tmp/chroma_backup.tar.gz" || echo "⚠️  ChromaDB恢复可能有问题"
    docker restart enterprise-ai-knowledge-base
    echo "✅ ChromaDB恢复完成"
fi

echo ""
echo "=== 恢复知识库文档 ==="
if [ -f "\/documents_backup.tar.gz" ]; then
    echo "正在恢复文档..."
    docker exec enterprise-ai-knowledge-base sh -c "rm -rf /app/documents/*" 2>&1 || true
    docker cp "\/documents_backup.tar.gz" enterprise-ai-knowledge-base:/tmp/documents_backup.tar.gz
    docker exec enterprise-ai-knowledge-base sh -c "cd /app && tar -xzf /tmp/documents_backup.tar.gz -C documents 2>&1 && rm /tmp/documents_backup.tar.gz" || echo "⚠️  文档恢复可能有问题"
    docker restart enterprise-ai-knowledge-base
    echo "✅ 文档恢复完成"
fi

echo ""
echo "✅ 数据恢复完成！"