#!/bin/bash

# Redis 备份脚本
# 支持RDB快照备份和AOF备份

set -euo pipefail

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups/redis}"
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/logs/backup}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
COMPRESSION="${COMPRESSION:-true}"
ENCRYPTION="${ENCRYPTION:-true}"

# Redis配置
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"
REDIS_CLI="${REDIS_CLI:-redis-cli}"

# 备份类型：rdb, aof, both
BACKUP_TYPE="${1:-rdb}"

# 时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATE=$(date +"%Y%m%d")

# 创建目录
mkdir -p "$BACKUP_DIR/$DATE"
mkdir -p "$LOG_DIR"

# 日志文件
LOG_FILE="$LOG_DIR/redis_backup_${BACKUP_TYPE}_${TIMESTAMP}.log"

# 日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

# 构建Redis CLI命令
redis_cmd() {
    local cmd="$1"
    if [ -n "$REDIS_PASSWORD" ]; then
        $REDIS_CLI -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" "$cmd"
    else
        $REDIS_CLI -h "$REDIS_HOST" -p "$REDIS_PORT" "$cmd"
    fi
}

# 检查Redis连接
check_connection() {
    log "检查Redis连接..."
    if ! redis_cmd "PING" | grep -q "PONG"; then
        error_exit "无法连接到Redis服务器"
    fi
    log "Redis连接正常"
}

# 获取Redis配置
get_redis_config() {
    local config_key="$1"
    redis_cmd "CONFIG GET $config_key" | tail -n 1
}

# RDB备份
rdb_backup() {
    log "开始RDB备份..."
    
    # 获取RDB文件路径
    RDB_DIR=$(get_redis_config "dir")
    RDB_FILE=$(get_redis_config "dbfilename")
    RDB_PATH="${RDB_DIR}/${RDB_FILE}"
    
    if [ ! -f "$RDB_PATH" ]; then
        error_exit "RDB文件不存在: $RDB_PATH"
    fi
    
    # 触发BGSAVE
    log "触发BGSAVE..."
    if redis_cmd "BGSAVE" | grep -q "OK"; then
        log "等待BGSAVE完成..."
        
        # 等待BGSAVE完成（最多等待60秒）
        local max_wait=60
        local waited=0
        while [ $waited -lt $max_wait ]; do
            if redis_cmd "LASTSAVE" > /dev/null 2>&1; then
                local last_save=$(redis_cmd "LASTSAVE")
                sleep 2
                local current_save=$(redis_cmd "LASTSAVE")
                if [ "$last_save" = "$current_save" ]; then
                    log "BGSAVE完成"
                    break
                fi
            fi
            sleep 1
            waited=$((waited + 1))
        done
        
        if [ $waited -ge $max_wait ]; then
            log "警告: BGSAVE可能未完成"
        fi
    else
        error_exit "BGSAVE失败"
    fi
    
    # 复制RDB文件
    BACKUP_FILE="$BACKUP_DIR/$DATE/redis_rdb_${TIMESTAMP}.rdb"
    
    if cp "$RDB_PATH" "$BACKUP_FILE" 2>>"$LOG_FILE"; then
        log "RDB备份完成: $BACKUP_FILE"
    else
        error_exit "RDB备份失败"
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
    "backup_type": "rdb",
    "timestamp": "$TIMESTAMP",
    "date": "$DATE",
    "host": "$REDIS_HOST",
    "port": "$REDIS_PORT",
    "size": "$BACKUP_SIZE",
    "checksum": "$BACKUP_CHECKSUM",
    "compressed": $COMPRESSION,
    "encrypted": $ENCRYPTION,
    "status": "success"
}
EOF
    
    echo "$BACKUP_FILE"
}

# AOF备份
aof_backup() {
    log "开始AOF备份..."
    
    # 检查是否启用了AOF
    if ! redis_cmd "CONFIG GET appendonly" | grep -q "yes"; then
        log "警告: AOF未启用，跳过AOF备份"
        return
    fi
    
    # 获取AOF文件路径
    AOF_DIR=$(get_redis_config "dir")
    AOF_FILE=$(get_redis_config "appendfilename")
    AOF_PATH="${AOF_DIR}/${AOF_FILE}"
    
    if [ ! -f "$AOF_PATH" ]; then
        log "警告: AOF文件不存在: $AOF_PATH"
        return
    fi
    
    # 触发AOF重写（可选，会产生新的AOF文件）
    log "触发AOF重写..."
    redis_cmd "BGREWRITEAOF" > /dev/null 2>&1 || true
    
    # 等待AOF重写完成
    sleep 5
    
    # 复制AOF文件
    BACKUP_FILE="$BACKUP_DIR/$DATE/redis_aof_${TIMESTAMP}.aof"
    
    if cp "$AOF_PATH" "$BACKUP_FILE" 2>>"$LOG_FILE"; then
        log "AOF备份完成: $BACKUP_FILE"
    else
        error_exit "AOF备份失败"
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
    "backup_type": "aof",
    "timestamp": "$TIMESTAMP",
    "date": "$DATE",
    "host": "$REDIS_HOST",
    "port": "$REDIS_PORT",
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
    
    if find "$BACKUP_DIR" -type f \( -name "*.rdb*" -o -name "*.aof*" \) -mtime +${RETENTION_DAYS} -delete 2>/dev/null; then
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
                    S3_PATH="s3://${S3_BUCKET}/redis/$(basename "$BACKUP_FILE")"
                    
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
                    OSS_PATH="oss://${OSS_BUCKET}/redis/$(basename "$BACKUP_FILE")"
                    
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
    log "Redis备份开始"
    log "备份类型: $BACKUP_TYPE"
    log "=========================================="
    
    check_connection
    
    BACKUP_FILES=()
    
    case "$BACKUP_TYPE" in
        rdb)
            BACKUP_FILES+=($(rdb_backup))
            ;;
        aof)
            BACKUP_FILES+=($(aof_backup))
            ;;
        both)
            BACKUP_FILES+=($(rdb_backup))
            BACKUP_FILES+=($(aof_backup))
            ;;
        *)
            error_exit "不支持的备份类型: $BACKUP_TYPE (支持: rdb, aof, both)"
            ;;
    esac
    
    for BACKUP_FILE in "${BACKUP_FILES[@]}"; do
        if [ -n "$BACKUP_FILE" ]; then
            upload_to_cloud "$BACKUP_FILE"
        fi
    done
    
    cleanup_old_backups
    
    log "=========================================="
    log "Redis备份完成"
    log "=========================================="
    
    exit 0
}

# 执行主函数
main









