#!/bin/bash

# PostgreSQL 备份脚本
# 支持全量备份、增量备份和日志备份

set -euo pipefail

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups/postgres}"
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/logs/backup}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
COMPRESSION="${COMPRESSION:-true}"
ENCRYPTION="${ENCRYPTION:-true}"

# 从环境变量读取数据库配置
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-enterprise_ai}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"
PGPASSWORD="${DB_PASSWORD}"

# 备份类型：full, incremental, log
BACKUP_TYPE="${1:-full}"

# 时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATE=$(date +"%Y%m%d")

# 创建目录
mkdir -p "$BACKUP_DIR/$DATE"
mkdir -p "$LOG_DIR"

# 日志文件
LOG_FILE="$LOG_DIR/postgres_backup_${BACKUP_TYPE}_${TIMESTAMP}.log"

# 日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

# 检查PostgreSQL连接
check_connection() {
    log "检查PostgreSQL连接..."
    if ! PGPASSWORD="$DB_PASSWORD" pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
        error_exit "无法连接到PostgreSQL服务器"
    fi
    log "PostgreSQL连接正常"
}

# 全量备份
full_backup() {
    log "开始全量备份..."
    
    BACKUP_FILE="$BACKUP_DIR/$DATE/postgres_full_${TIMESTAMP}.sql"
    
    # 执行pg_dump
    if PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --verbose \
        --clean \
        --if-exists \
        --create \
        > "$BACKUP_FILE" 2>>"$LOG_FILE"; then
        log "全量备份完成: $BACKUP_FILE"
    else
        error_exit "全量备份失败"
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
    "backup_type": "full",
    "timestamp": "$TIMESTAMP",
    "date": "$DATE",
    "database": "$DB_NAME",
    "host": "$DB_HOST",
    "port": "$DB_PORT",
    "size": "$BACKUP_SIZE",
    "checksum": "$BACKUP_CHECKSUM",
    "compressed": $COMPRESSION,
    "encrypted": $ENCRYPTION,
    "status": "success"
}
EOF
    
    echo "$BACKUP_FILE"
}

# 增量备份（基于WAL归档）
incremental_backup() {
    log "开始增量备份..."
    
    # 检查是否启用了WAL归档
    WAL_ARCHIVE_DIR="${WAL_ARCHIVE_DIR:-$BACKUP_DIR/wal_archive}"
    mkdir -p "$WAL_ARCHIVE_DIR"
    
    # 触发WAL切换
    log "触发WAL切换..."
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT pg_switch_wal();" > /dev/null 2>&1
    
    # 归档WAL文件
    BACKUP_FILE="$BACKUP_DIR/$DATE/postgres_incremental_${TIMESTAMP}.tar"
    
    # 收集自上次备份以来的WAL文件
    if tar -czf "$BACKUP_FILE" -C "$WAL_ARCHIVE_DIR" . 2>>"$LOG_FILE"; then
        log "增量备份完成: $BACKUP_FILE"
    else
        error_exit "增量备份失败"
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
    "backup_type": "incremental",
    "timestamp": "$TIMESTAMP",
    "date": "$DATE",
    "database": "$DB_NAME",
    "host": "$DB_HOST",
    "port": "$DB_PORT",
    "size": "$BACKUP_SIZE",
    "checksum": "$BACKUP_CHECKSUM",
    "compressed": true,
    "encrypted": $ENCRYPTION,
    "status": "success"
}
EOF
    
    echo "$BACKUP_FILE"
}

# 日志备份（WAL归档）
log_backup() {
    log "开始日志备份..."
    
    WAL_ARCHIVE_DIR="${WAL_ARCHIVE_DIR:-$BACKUP_DIR/wal_archive}"
    mkdir -p "$WAL_ARCHIVE_DIR"
    
    # 触发WAL切换并归档
    log "触发WAL切换..."
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT pg_switch_wal();" > /dev/null 2>&1
    
    # WAL文件应该已经由PostgreSQL自动归档到WAL_ARCHIVE_DIR
    log "日志备份完成（WAL已归档到 $WAL_ARCHIVE_DIR）"
}

# 清理旧备份
cleanup_old_backups() {
    log "清理 ${RETENTION_DAYS} 天前的备份..."
    
    if find "$BACKUP_DIR" -type f -name "*.sql*" -mtime +${RETENTION_DAYS} -delete 2>/dev/null; then
        log "清理完成"
    else
        log "警告: 清理旧备份时出现错误"
    fi
}

# 上传到云存储（如果配置）
upload_to_cloud() {
    if [ -n "${CLOUD_STORAGE_TYPE:-}" ]; then
        log "上传备份到云存储 ($CLOUD_STORAGE_TYPE)..."
        
        case "$CLOUD_STORAGE_TYPE" in
            s3)
                if [ -n "${AWS_ACCESS_KEY_ID:-}" ] && [ -n "${AWS_SECRET_ACCESS_KEY:-}" ] && [ -n "${S3_BUCKET:-}" ]; then
                    BACKUP_FILE="$1"
                    S3_PATH="s3://${S3_BUCKET}/postgres/$(basename "$BACKUP_FILE")"
                    
                    if aws s3 cp "$BACKUP_FILE" "$S3_PATH" 2>>"$LOG_FILE"; then
                        log "上传到S3成功: $S3_PATH"
                        # 同时上传元数据
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
                    OSS_PATH="oss://${OSS_BUCKET}/postgres/$(basename "$BACKUP_FILE")"
                    
                    if ossutil cp "$BACKUP_FILE" "$OSS_PATH" --endpoint "$OSS_ENDPOINT" 2>>"$LOG_FILE"; then
                        log "上传到OSS成功: $OSS_PATH"
                        # 同时上传元数据
                        if [ -f "${BACKUP_FILE}.meta" ]; then
                            ossutil cp "${BACKUP_FILE}.meta" "${OSS_PATH}.meta" --endpoint "$OSS_ENDPOINT" 2>>"$LOG_FILE"
                        fi
                    else
                        log "警告: 上传到OSS失败"
                    fi
                fi
                ;;
            *)
                log "警告: 不支持的云存储类型: $CLOUD_STORAGE_TYPE"
                ;;
        esac
    fi
}

# 发送告警通知
send_alert() {
    local status="$1"
    local message="$2"
    
    if [ "$status" = "failure" ]; then
        log "发送失败告警: $message"
        
        # 发送邮件（如果配置）
        if [ -n "${ALERT_EMAIL:-}" ] && command -v mail > /dev/null 2>&1; then
            echo "$message" | mail -s "数据库备份失败告警" "$ALERT_EMAIL"
        fi
        
        # 发送Webhook（如果配置）
        if [ -n "${ALERT_WEBHOOK:-}" ]; then
            curl -X POST "$ALERT_WEBHOOK" \
                -H "Content-Type: application/json" \
                -d "{\"status\":\"failure\",\"message\":\"$message\",\"timestamp\":\"$TIMESTAMP\"}" \
                2>>"$LOG_FILE" || true
        fi
    fi
}

# 主函数
main() {
    log "=========================================="
    log "PostgreSQL备份开始"
    log "备份类型: $BACKUP_TYPE"
    log "=========================================="
    
    check_connection
    
    BACKUP_FILE=""
    case "$BACKUP_TYPE" in
        full)
            BACKUP_FILE=$(full_backup)
            ;;
        incremental)
            BACKUP_FILE=$(incremental_backup)
            ;;
        log)
            log_backup
            ;;
        *)
            error_exit "不支持的备份类型: $BACKUP_TYPE (支持: full, incremental, log)"
            ;;
    esac
    
    if [ -n "$BACKUP_FILE" ]; then
        upload_to_cloud "$BACKUP_FILE"
    fi
    
    cleanup_old_backups
    
    log "=========================================="
    log "PostgreSQL备份完成"
    log "=========================================="
    
    exit 0
}

# 执行主函数
main









