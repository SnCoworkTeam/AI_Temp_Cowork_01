#!/bin/bash

# 向量数据库备份脚本
# 支持ChromaDB和Weaviate备份

set -euo pipefail

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups/vector}"
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/logs/backup}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
COMPRESSION="${COMPRESSION:-true}"
ENCRYPTION="${ENCRYPTION:-true}"

# 向量数据库类型：chroma, weaviate
VECTOR_DB_TYPE="${VECTOR_DB_TYPE:-chroma}"

# 时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATE=$(date +"%Y%m%d")

# 创建目录
mkdir -p "$BACKUP_DIR/$DATE"
mkdir -p "$LOG_DIR"

# 日志文件
LOG_FILE="$LOG_DIR/vector_backup_${VECTOR_DB_TYPE}_${TIMESTAMP}.log"

# 日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

# ChromaDB备份
backup_chroma() {
    log "开始ChromaDB备份..."
    
    CHROMA_DIR="${CHROMA_DIR:-$PROJECT_ROOT/data/chroma}"
    
    if [ ! -d "$CHROMA_DIR" ]; then
        error_exit "ChromaDB数据目录不存在: $CHROMA_DIR"
    fi
    
    BACKUP_FILE="$BACKUP_DIR/$DATE/chroma_${TIMESTAMP}.tar"
    
    # 打包整个ChromaDB目录
    if tar -czf "$BACKUP_FILE" -C "$(dirname "$CHROMA_DIR")" "$(basename "$CHROMA_DIR")" 2>>"$LOG_FILE"; then
        log "ChromaDB备份完成: $BACKUP_FILE"
    else
        error_exit "ChromaDB备份失败"
    fi
    
    # 加密
    if [ "$ENCRYPTION" = "true" ] && [ -n "${ENCRYPTION_KEY:-}" ]; then
        log "加密备份文件..."
        if openssl enc -aes-256-cbc -salt -in "$BACKUP_FILE" -out "${BACKUP_FILE}.enc" -pass "pass:${ENCRYPTION_KEY}" && rm "$BACKUP_FILE"; then
            BACKUP_FILE="${BACKUP_FILE}.enc"
            log "加密完成: $BACKUP_FILE"
        else
            error_exit "加密失败"
        fi
    fi
    
    # 计算文件大小和校验和
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    BACKUP_CHECKSUM=$(md5sum "$BACKUP_FILE" | cut -d' ' -f1)
    
    log "备份文件: $BACKUP_FILE"
    log "备份大小: $BACKUP_SIZE"
    log "MD5校验和: $BACKUP_CHECKSUM"
    
    # 保存元数据
    cat > "${BACKUP_FILE}.meta" <<EOF
{
    "backup_type": "chroma",
    "timestamp": "$TIMESTAMP",
    "date": "$DATE",
    "vector_db_type": "chroma",
    "data_dir": "$CHROMA_DIR",
    "size": "$BACKUP_SIZE",
    "checksum": "$BACKUP_CHECKSUM",
    "compressed": true,
    "encrypted": $ENCRYPTION,
    "status": "success"
}
EOF
    
    echo "$BACKUP_FILE"
}

# Weaviate备份
backup_weaviate() {
    log "开始Weaviate备份..."
    
    # Weaviate通常使用API导出数据
    WEAVIATE_URL="${WEAVIATE_URL:-http://localhost:8080}"
    
    BACKUP_FILE="$BACKUP_DIR/$DATE/weaviate_${TIMESTAMP}.json"
    
    # 使用Weaviate API导出数据
    if curl -s -X GET "${WEAVIATE_URL}/v1/backups" > "${BACKUP_FILE}.tmp" 2>>"$LOG_FILE"; then
        # 如果支持备份API，使用备份API
        if curl -s -X POST "${WEAVIATE_URL}/v1/backups/filesystem" \
            -H "Content-Type: application/json" \
            -d "{\"id\":\"backup_${TIMESTAMP}\"}" > /dev/null 2>>"$LOG_FILE"; then
            log "Weaviate备份API调用成功"
            # 等待备份完成
            sleep 10
            # 获取备份文件路径
            BACKUP_PATH=$(curl -s -X GET "${WEAVIATE_URL}/v1/backups/filesystem/backup_${TIMESTAMP}" | jq -r '.path' 2>/dev/null || echo "")
            if [ -n "$BACKUP_PATH" ] && [ -f "$BACKUP_PATH" ]; then
                cp "$BACKUP_PATH" "$BACKUP_FILE"
            fi
        else
            # 降级：导出所有对象
            log "使用数据导出API..."
            curl -s -X GET "${WEAVIATE_URL}/v1/objects" > "$BACKUP_FILE" 2>>"$LOG_FILE"
        fi
        
        if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
            log "Weaviate备份完成: $BACKUP_FILE"
        else
            error_exit "Weaviate备份失败"
        fi
    else
        error_exit "无法连接到Weaviate服务器"
    fi
    
    # 压缩
    if [ "$COMPRESSION" = "true" ]; then
        log "压缩备份文件..."
        if gzip "$BACKUP_FILE"; then
            BACKUP_FILE="${BACKUP_FILE}.gz"
            log "压缩完成: $BACKUP_FILE"
        else
            error_exit "压缩失败"
        fi
    fi
    
    # 加密
    if [ "$ENCRYPTION" = "true" ] && [ -n "${ENCRYPTION_KEY:-}" ]; then
        log "加密备份文件..."
        if openssl enc -aes-256-cbc -salt -in "$BACKUP_FILE" -out "${BACKUP_FILE}.enc" -pass "pass:${ENCRYPTION_KEY}" && rm "$BACKUP_FILE"; then
            BACKUP_FILE="${BACKUP_FILE}.enc"
            log "加密完成: $BACKUP_FILE"
        else
            error_exit "加密失败"
        fi
    fi
    
    # 计算文件大小和校验和
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    BACKUP_CHECKSUM=$(md5sum "$BACKUP_FILE" | cut -d' ' -f1)
    
    log "备份文件: $BACKUP_FILE"
    log "备份大小: $BACKUP_SIZE"
    log "MD5校验和: $BACKUP_CHECKSUM"
    
    # 保存元数据
    cat > "${BACKUP_FILE}.meta" <<EOF
{
    "backup_type": "weaviate",
    "timestamp": "$TIMESTAMP",
    "date": "$DATE",
    "vector_db_type": "weaviate",
    "url": "$WEAVIATE_URL",
    "size": "$BACKUP_SIZE",
    "checksum": "$BACKUP_CHECKSUM",
    "compressed": $COMPRESSION,
    "encrypted": $ENCRYPTION,
    "status": "success"
}
EOF
    
    echo "$BACKUP_FILE"
}

# 清理旧备份
cleanup_old_backups() {
    log "清理 ${RETENTION_DAYS} 天前的备份..."
    
    if find "$BACKUP_DIR" -type f -name "*.tar*" -o -name "*.json*" -mtime +${RETENTION_DAYS} -delete 2>/dev/null; then
        log "清理完成"
    else
        log "警告: 清理旧备份时出现错误"
    fi
}

# 上传到云存储
upload_to_cloud() {
    if [ -n "${CLOUD_STORAGE_TYPE:-}" ]; then
        log "上传备份到云存储 ($CLOUD_STORAGE_TYPE)..."
        
        case "$CLOUD_STORAGE_TYPE" in
            s3)
                if [ -n "${AWS_ACCESS_KEY_ID:-}" ] && [ -n "${AWS_SECRET_ACCESS_KEY:-}" ] && [ -n "${S3_BUCKET:-}" ]; then
                    BACKUP_FILE="$1"
                    S3_PATH="s3://${S3_BUCKET}/vector/$(basename "$BACKUP_FILE")"
                    
                    if aws s3 cp "$BACKUP_FILE" "$S3_PATH" 2>>"$LOG_FILE"; then
                        log "上传到S3成功: $S3_PATH"
                        if [ -f "${BACKUP_FILE}.meta" ]; then
                            aws s3 cp "${BACKUP_FILE}.meta" "${S3_PATH}.meta" 2>>"$LOG_FILE"
                        fi
                    else
                        log "警告: 上传到S3失败"
                    fi
                fi
                ;;
            oss)
                if [ -n "${OSS_ACCESS_KEY_ID:-}" ] && [ -n "${OSS_ACCESS_KEY_SECRET:-}" ] && [ -n "${OSS_BUCKET:-}" ] && [ -n "${OSS_ENDPOINT:-}" ]; then
                    BACKUP_FILE="$1"
                    OSS_PATH="oss://${OSS_BUCKET}/vector/$(basename "$BACKUP_FILE")"
                    
                    if ossutil cp "$BACKUP_FILE" "$OSS_PATH" --endpoint "$OSS_ENDPOINT" 2>>"$LOG_FILE"; then
                        log "上传到OSS成功: $OSS_PATH"
                        if [ -f "${BACKUP_FILE}.meta" ]; then
                            ossutil cp "${BACKUP_FILE}.meta" "${OSS_PATH}.meta" --endpoint "$OSS_ENDPOINT" 2>>"$LOG_FILE"
                        fi
                    else
                        log "警告: 上传到OSS失败"
                    fi
                fi
                ;;
        esac
    fi
}

# 主函数
main() {
    log "=========================================="
    log "向量数据库备份开始"
    log "数据库类型: $VECTOR_DB_TYPE"
    log "=========================================="
    
    BACKUP_FILE=""
    
    case "$VECTOR_DB_TYPE" in
        chroma)
            BACKUP_FILE=$(backup_chroma)
            ;;
        weaviate)
            BACKUP_FILE=$(backup_weaviate)
            ;;
        *)
            error_exit "不支持的向量数据库类型: $VECTOR_DB_TYPE (支持: chroma, weaviate)"
            ;;
    esac
    
    if [ -n "$BACKUP_FILE" ]; then
        upload_to_cloud "$BACKUP_FILE"
    fi
    
    cleanup_old_backups
    
    log "=========================================="
    log "向量数据库备份完成"
    log "=========================================="
    
    exit 0
}

# 执行主函数
main









