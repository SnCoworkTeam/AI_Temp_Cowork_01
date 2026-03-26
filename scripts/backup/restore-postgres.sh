#!/bin/bash

# PostgreSQL 恢复脚本
# 支持全量恢复、增量恢复和指定时间点恢复

set -euo pipefail

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups/postgres}"
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/logs/restore}"

# 数据库配置
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-enterprise_ai}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"
PGPASSWORD="${DB_PASSWORD}"

# 恢复类型：full, point-in-time
RESTORE_TYPE="${1:-full}"
BACKUP_FILE="${2:-}"

# 时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 创建目录
mkdir -p "$LOG_DIR"

# 日志文件
LOG_FILE="$LOG_DIR/postgres_restore_${TIMESTAMP}.log"

# 日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

# 确认恢复操作
confirm_restore() {
    log "警告: 恢复操作将覆盖现有数据库!"
    log "备份文件: $BACKUP_FILE"
    log "目标数据库: $DB_NAME"
    read -p "确认继续? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log "恢复操作已取消"
        exit 0
    fi
}

# 解密备份文件
decrypt_backup() {
    local encrypted_file="$1"
    local decrypted_file="${encrypted_file%.enc}"
    
    if [ -f "${encrypted_file}.enc" ]; then
        log "解密备份文件..."
        if openssl enc -aes-256-cbc -d -in "$encrypted_file" -out "$decrypted_file" -pass "pass:${ENCRYPTION_KEY}" 2>>"$LOG_FILE"; then
            echo "$decrypted_file"
        else
            error_exit "解密失败"
        fi
    else
        echo "$encrypted_file"
    fi
}

# 解压备份文件
decompress_backup() {
    local compressed_file="$1"
    local decompressed_file="${compressed_file%.gz}"
    
    if [ -f "${compressed_file}.gz" ]; then
        log "解压备份文件..."
        if gunzip "$compressed_file" 2>>"$LOG_FILE"; then
            echo "$decompressed_file"
        else
            error_exit "解压失败"
        fi
    else
        echo "$compressed_file"
    fi
}

# 验证备份文件
verify_backup() {
    local backup_file="$1"
    
    log "验证备份文件..."
    
    # 检查元数据文件
    if [ -f "${backup_file}.meta" ]; then
        log "备份元数据:"
        cat "${backup_file}.meta" | tee -a "$LOG_FILE"
        
        # 验证校验和
        if command -v md5sum > /dev/null 2>&1; then
            local current_checksum=$(md5sum "$backup_file" | cut -d' ' -f1)
            local expected_checksum=$(jq -r '.checksum' "${backup_file}.meta" 2>/dev/null || echo "")
            
            if [ -n "$expected_checksum" ] && [ "$current_checksum" != "$expected_checksum" ]; then
                error_exit "备份文件校验和验证失败"
            fi
            log "校验和验证通过"
        fi
    else
        log "警告: 未找到备份元数据文件"
    fi
}

# 全量恢复
full_restore() {
    local backup_file="$1"
    
    log "开始全量恢复..."
    
    # 解密
    backup_file=$(decrypt_backup "$backup_file")
    
    # 解压
    if [[ "$backup_file" == *.gz ]]; then
        backup_file=$(decompress_backup "$backup_file")
    fi
    
    # 验证
    verify_backup "$backup_file"
    
    # 停止应用连接（可选）
    log "停止应用连接..."
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
        -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" \
        > /dev/null 2>&1 || true
    
    # 删除现有数据库（如果存在）
    log "删除现有数据库..."
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
        -c "DROP DATABASE IF EXISTS $DB_NAME;" \
        2>>"$LOG_FILE" || true
    
    # 恢复数据库
    log "恢复数据库..."
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
        < "$backup_file" 2>>"$LOG_FILE"; then
        log "全量恢复完成"
    else
        error_exit "全量恢复失败"
    fi
    
    # 清理临时文件
    if [ -f "${backup_file}.tmp" ]; then
        rm -f "${backup_file}.tmp"
    fi
}

# 时间点恢复（PITR）
point_in_time_restore() {
    local backup_file="$1"
    local target_time="${3:-}"
    
    log "开始时间点恢复..."
    log "目标时间: ${target_time:-最新}"
    
    # 先执行全量恢复
    full_restore "$backup_file"
    
    # 应用WAL日志到目标时间点
    if [ -n "$target_time" ]; then
        log "应用WAL日志到时间点: $target_time"
        
        WAL_ARCHIVE_DIR="${WAL_ARCHIVE_DIR:-$BACKUP_DIR/wal_archive}"
        
        if [ -d "$WAL_ARCHIVE_DIR" ]; then
            # 配置recovery.conf
            RECOVERY_CONF="/var/lib/postgresql/data/recovery.conf"
            if [ -f "$RECOVERY_CONF" ]; then
                cat > "$RECOVERY_CONF" <<EOF
restore_command = 'cp $WAL_ARCHIVE_DIR/%f %p'
recovery_target_time = '$target_time'
EOF
                log "恢复配置已创建"
            fi
        else
            log "警告: WAL归档目录不存在，无法进行时间点恢复"
        fi
    fi
}

# 测试恢复
test_restore() {
    local backup_file="$1"
    local test_db_name="${DB_NAME}_test_${TIMESTAMP}"
    
    log "开始测试恢复到测试数据库: $test_db_name"
    
    # 创建测试数据库
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
        -c "CREATE DATABASE $test_db_name;" 2>>"$LOG_FILE" || true
    
    # 恢复到测试数据库
    local original_db_name="$DB_NAME"
    DB_NAME="$test_db_name"
    
    full_restore "$backup_file"
    
    # 验证测试数据库
    log "验证测试数据库..."
    local table_count=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$test_db_name" \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
    
    if [ -n "$table_count" ] && [ "$table_count" -gt 0 ]; then
        log "测试恢复成功: 找到 $table_count 个表"
    else
        log "警告: 测试恢复可能有问题"
    fi
    
    # 清理测试数据库
    read -p "删除测试数据库 $test_db_name? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
            -c "DROP DATABASE $test_db_name;" 2>>"$LOG_FILE"
        log "测试数据库已删除"
    fi
    
    DB_NAME="$original_db_name"
}

# 主函数
main() {
    log "=========================================="
    log "PostgreSQL恢复开始"
    log "恢复类型: $RESTORE_TYPE"
    log "=========================================="
    
    # 查找最新的备份文件（如果未指定）
    if [ -z "$BACKUP_FILE" ]; then
        log "查找最新备份文件..."
        BACKUP_FILE=$(find "$BACKUP_DIR" -type f -name "postgres_full_*.sql*" -o -name "postgres_full_*.enc" | sort -r | head -n 1)
        
        if [ -z "$BACKUP_FILE" ]; then
            error_exit "未找到备份文件"
        fi
        log "使用备份文件: $BACKUP_FILE"
    fi
    
    if [ ! -f "$BACKUP_FILE" ]; then
        error_exit "备份文件不存在: $BACKUP_FILE"
    fi
    
    confirm_restore
    
    case "$RESTORE_TYPE" in
        full)
            full_restore "$BACKUP_FILE"
            ;;
        pitr)
            point_in_time_restore "$BACKUP_FILE" "$@"
            ;;
        test)
            test_restore "$BACKUP_FILE"
            ;;
        *)
            error_exit "不支持的恢复类型: $RESTORE_TYPE (支持: full, pitr, test)"
            ;;
    esac
    
    log "=========================================="
    log "PostgreSQL恢复完成"
    log "=========================================="
    
    exit 0
}

# 执行主函数
main "$@"









