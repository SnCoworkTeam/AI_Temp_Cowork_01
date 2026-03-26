#!/bin/bash
# 在服务器上恢复元数据和知识库数据

set -e

SYNC_PACKAGE="${1:-/opt/enterprise-ai-platform/backups/metadata_knowledge_sync_20251204_141922.tar.gz}"

if [ ! -f "$SYNC_PACKAGE" ]; then
    echo "错误: 同步包不存在: $SYNC_PACKAGE"
    exit 1
fi

echo "========================================"
echo "  恢复元数据和知识库数据"
echo "========================================"
echo ""
echo "同步包: $SYNC_PACKAGE"
echo ""

# 解压目录
EXTRACT_DIR="/tmp/sync_restore_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$EXTRACT_DIR"

echo "[解压] 解压同步包..."
tar -xzf "$SYNC_PACKAGE" -C "$EXTRACT_DIR"

# 读取元数据
METADATA_FILE=$(find "$EXTRACT_DIR" -name "metadata_*.json" | head -1)
if [ -z "$METADATA_FILE" ]; then
    echo "错误: 未找到元数据文件"
    exit 1
fi

echo "  元数据文件: $METADATA_FILE"
echo ""

# 1. 恢复PostgreSQL数据
POSTGRES_FILE=$(find "$EXTRACT_DIR" -name "postgres_*.sql.gz" | head -1)
if [ -n "$POSTGRES_FILE" ]; then
    echo "[1/3] 恢复PostgreSQL数据..."
    echo "  文件: $(basename $POSTGRES_FILE)"
    
    # 解压SQL文件（先检查文件格式）
    SQL_FILE="${POSTGRES_FILE%.gz}"
    
    # 尝试解压，如果失败则直接使用原文件
    if gunzip -t "$POSTGRES_FILE" 2>/dev/null; then
        echo "  使用gzip解压..."
        gunzip -c "$POSTGRES_FILE" > "$SQL_FILE"
    else
        echo "  文件可能不是gzip格式，尝试直接使用..."
        cp "$POSTGRES_FILE" "$SQL_FILE"
    fi
    
    # 检查SQL文件大小
    if [ ! -s "$SQL_FILE" ]; then
        echo "  错误: SQL文件为空，跳过恢复"
    else
        echo "  SQL文件大小: $(du -h "$SQL_FILE" | cut -f1)"
        # 恢复数据库
        sudo docker exec -i enterprise-ai-postgres psql -U ai_user -d ai_platform < "$SQL_FILE" || {
            echo "  警告: PostgreSQL恢复可能有问题，但继续执行..."
        }
    fi
    
    echo "  [OK] PostgreSQL数据恢复完成"
    echo ""
fi

# 2. 恢复Chroma向量数据库
CHROMA_FILE=$(find "$EXTRACT_DIR" -name "chroma_*.tar.gz" | head -1)
if [ -n "$CHROMA_FILE" ]; then
    echo "[2/3] 恢复Chroma向量数据库..."
    echo "  文件: $(basename $CHROMA_FILE)"
    
    # 创建临时容器恢复数据
    TEMP_CONTAINER="chroma_restore_$(date +%Y%m%d%H%M%S)"
    sudo docker run --rm -d --name "$TEMP_CONTAINER" \
        -v enterprise-ai-platform_knowledge_base_chroma:/data \
        alpine sleep 3600
    
    # 清空现有数据
    sudo docker exec "$TEMP_CONTAINER" sh -c "rm -rf /data/*" || true
    
    # 恢复数据（检查文件格式）
    if gunzip -t "$CHROMA_FILE" 2>/dev/null; then
        echo "  使用gzip解压Chroma数据..."
        gunzip -c "$CHROMA_FILE" | sudo docker exec -i "$TEMP_CONTAINER" tar -xzf - -C /data
    else
        echo "  直接解压Chroma数据..."
        sudo docker exec -i "$TEMP_CONTAINER" tar -xzf "$CHROMA_FILE" -C /data
    fi
    
    sudo docker rm -f "$TEMP_CONTAINER" 2>/dev/null || true
    
    echo "  [OK] Chroma数据恢复完成"
    echo ""
fi

# 3. 恢复文档文件
DOCUMENTS_FILE=$(find "$EXTRACT_DIR" -name "documents_*.tar.gz" | head -1)
if [ -n "$DOCUMENTS_FILE" ]; then
    echo "[3/3] 恢复文档文件..."
    echo "  文件: $(basename $DOCUMENTS_FILE)"
    
    TEMP_CONTAINER="docs_restore_$(date +%Y%m%d%H%M%S)"
    docker run --rm -d --name "$TEMP_CONTAINER" \
        -v enterprise-ai-platform_knowledge_base_documents:/data \
        alpine sleep 3600
    
    docker exec "$TEMP_CONTAINER" sh -c "rm -rf /data/*" || true
    gunzip -c "$DOCUMENTS_FILE" | docker exec -i "$TEMP_CONTAINER" tar -xzf - -C /data
    
    docker rm -f "$TEMP_CONTAINER" 2>/dev/null || true
    
    echo "  [OK] 文档文件恢复完成"
    echo ""
fi

# 清理临时目录
rm -rf "$EXTRACT_DIR"

echo "========================================"
echo "  数据恢复完成！"
echo "========================================"
echo ""
echo "建议重启相关服务:"
echo "  docker-compose restart metadata-service knowledge-base"
echo ""

