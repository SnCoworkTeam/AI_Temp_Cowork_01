#!/bin/bash

# 备份验证脚本
# 验证备份文件的完整性和可恢复性

set -euo pipefail

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/logs/backup}"

# 验证类型：all, postgres, redis, vector, specific
VERIFY_TYPE="${1:-all}"
BACKUP_FILE="${2:-}"

# 时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 创建目录
mkdir -p "$LOG_DIR"

# 日志文件
LOG_FILE="$LOG_DIR/verify_${TIMESTAMP}.log"

# 日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

# 验证文件完整性
verify_file_integrity() {
    local backup_file="$1"
    local meta_file="${backup_file}.meta"
    
    log "验证文件完整性: $backup_file"
    
    # 检查文件存在
    if [ ! -f "$backup_file" ]; then
        error_exit "备份文件不存在: $backup_file"
    fi
    
    # 检查文件大小
    local file_size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file" 2>/dev/null || echo "0")
    if [ "$file_size" -eq 0 ]; then
        error_exit "备份文件为空: $backup_file"
    fi
    log "文件大小: $file_size 字节"
    
    # 验证校验和（如果存在元数据）
    if [ -f "$meta_file" ]; then
        local expected_checksum=$(jq -r '.checksum' "$meta_file" 2>/dev/null || echo "")
        
        if [ -n "$expected_checksum" ]; then
            local actual_checksum=$(md5sum "$backup_file" | cut -d' ' -f1)
            
            if [ "$actual_checksum" = "$expected_checksum" ]; then
                log "校验和验证通过: $actual_checksum"
                return 0
            else
                error_exit "校验和验证失败: 期望 $expected_checksum, 实际 $actual_checksum"
            fi
        else
            log "警告: 元数据中未找到校验和"
        fi
    else
        log "警告: 未找到元数据文件"
    fi
    
    return 0
}

# 验证压缩文件
verify_compression() {
    local backup_file="$1"
    
    if [[ "$backup_file" == *.gz ]]; then
        log "验证压缩文件..."
        if gzip -t "$backup_file" 2>>"$LOG_FILE"; then
            log "压缩文件验证通过"
            return 0
        else
            error_exit "压缩文件损坏"
        fi
    fi
    
    return 0
}

# 验证加密文件
verify_encryption() {
    local backup_file="$1"
    
    if [[ "$backup_file" == *.enc ]]; then
        log "验证加密文件..."
        
        if [ -z "${ENCRYPTION_KEY:-}" ]; then
            log "警告: 未设置加密密钥，跳过加密验证"
            return 0
        fi
        
        # 尝试解密（不保存文件）
        if openssl enc -aes-256-cbc -d -in "$backup_file" -out /dev/null -pass "pass:${ENCRYPTION_KEY}" 2>>"$LOG_FILE"; then
            log "加密文件验证通过"
            return 0
        else
            error_exit "加密文件解密失败"
        fi
    fi
    
    return 0
}

# 验证PostgreSQL备份
verify_postgres_backup() {
    local backup_file="$1"
    
    log "验证PostgreSQL备份..."
    
    # 解密
    local temp_file="$backup_file"
    if [[ "$backup_file" == *.enc ]]; then
        if [ -z "${ENCRYPTION_KEY:-}" ]; then
            log "警告: 无法解密，跳过内容验证"
            return 0
        fi
        
        temp_file="${backup_file%.enc}.tmp"
        openssl enc -aes-256-cbc -d -in "$backup_file" -out "$temp_file" -pass "pass:${ENCRYPTION_KEY}" 2>>"$LOG_FILE"
    fi
    
    # 解压
    if [[ "$temp_file" == *.gz ]]; then
        gunzip -c "$temp_file" > "${temp_file%.gz}.sql" 2>>"$LOG_FILE"
        temp_file="${temp_file%.gz}.sql"
    fi
    
    # 验证SQL语法（基本检查）
    if command -v pg_restore > /dev/null 2>&1 || [ -f "$temp_file" ]; then
        # 检查SQL文件是否包含基本的PostgreSQL命令
        if grep -q "CREATE\|ALTER\|INSERT" "$temp_file" 2>/dev/null; then
            log "PostgreSQL备份内容验证通过"
        else
            log "警告: PostgreSQL备份内容可能不完整"
        fi
    fi
    
    # 清理临时文件
    if [ "$temp_file" != "$backup_file" ] && [ -f "$temp_file" ]; then
        rm -f "$temp_file"
    fi
    
    return 0
}

# 验证Redis备份
verify_redis_backup() {
    local backup_file="$1"
    
    log "验证Redis备份..."
    
    # 解密
    local temp_file="$backup_file"
    if [[ "$backup_file" == *.enc ]]; then
        if [ -z "${ENCRYPTION_KEY:-}" ]; then
            log "警告: 无法解密，跳过内容验证"
            return 0
        fi
        
        temp_file="${backup_file%.enc}.tmp"
        openssl enc -aes-256-cbc -d -in "$backup_file" -out "$temp_file" -pass "pass:${ENCRYPTION_KEY}" 2>>"$LOG_FILE"
    fi
    
    # 解压
    if [[ "$temp_file" == *.gz ]]; then
        gunzip -c "$temp_file" > "${temp_file%.gz}.rdb" 2>>"$LOG_FILE"
        temp_file="${temp_file%.gz}.rdb"
    fi
    
    # 验证RDB文件（检查文件头）
    if [[ "$temp_file" == *.rdb ]]; then
        # RDB文件应该以 "REDIS" 开头
        if head -c 5 "$temp_file" | grep -q "REDIS" 2>/dev/null || file "$temp_file" | grep -q "data" 2>/dev/null; then
            log "Redis备份内容验证通过"
        else
            log "警告: Redis备份文件可能损坏"
        fi
    fi
    
    # 清理临时文件
    if [ "$temp_file" != "$backup_file" ] && [ -f "$temp_file" ]; then
        rm -f "$temp_file"
    fi
    
    return 0
}

# 验证向量数据库备份
verify_vector_backup() {
    local backup_file="$1"
    
    log "验证向量数据库备份..."
    
    # 解密
    local temp_file="$backup_file"
    if [[ "$backup_file" == *.enc ]]; then
        if [ -z "${ENCRYPTION_KEY:-}" ]; then
            log "警告: 无法解密，跳过内容验证"
            return 0
        fi
        
        temp_file="${backup_file%.enc}.tmp"
        openssl enc -aes-256-cbc -d -in "$backup_file" -out "$temp_file" -pass "pass:${ENCRYPTION_KEY}" 2>>"$LOG_FILE"
    fi
    
    # 解压
    if [[ "$temp_file" == *.gz ]]; then
        gunzip -c "$temp_file" > "${temp_file%.gz}.tar" 2>>"$LOG_FILE"
        temp_file="${temp_file%.gz}.tar"
    fi
    
    # 验证tar文件
    if [[ "$temp_file" == *.tar ]]; then
        if tar -tzf "$temp_file" > /dev/null 2>>"$LOG_FILE"; then
            log "向量数据库备份内容验证通过"
        else
            log "警告: 向量数据库备份文件可能损坏"
        fi
    fi
    
    # 清理临时文件
    if [ "$temp_file" != "$backup_file" ] && [ -f "$temp_file" ]; then
        rm -f "$temp_file"
    fi
    
    return 0
}

# 验证特定文件
verify_specific_file() {
    local backup_file="$1"
    
    log "验证特定备份文件: $backup_file"
    
    # 确定备份类型
    if echo "$backup_file" | grep -q "postgres"; then
        verify_file_integrity "$backup_file"
        verify_compression "$backup_file"
        verify_encryption "$backup_file"
        verify_postgres_backup "$backup_file"
    elif echo "$backup_file" | grep -q "redis"; then
        verify_file_integrity "$backup_file"
        verify_compression "$backup_file"
        verify_encryption "$backup_file"
        verify_redis_backup "$backup_file"
    elif echo "$backup_file" | grep -q "chroma\|weaviate\|vector"; then
        verify_file_integrity "$backup_file"
        verify_compression "$backup_file"
        verify_encryption "$backup_file"
        verify_vector_backup "$backup_file"
    else
        verify_file_integrity "$backup_file"
        verify_compression "$backup_file"
        verify_encryption "$backup_file"
    fi
    
    log "验证完成: $backup_file"
}

# 验证所有备份
verify_all_backups() {
    log "验证所有备份..."
    
    local total=0
    local passed=0
    local failed=0
    
    for service in postgres redis vector; do
        BACKUP_DIR_SERVICE="$BACKUP_DIR/$service"
        
        if [ -d "$BACKUP_DIR_SERVICE" ]; then
            log "验证 $service 备份..."
            
            # 查找最近的备份文件
            local backup_files=$(find "$BACKUP_DIR_SERVICE" -type f \( -name "*.sql*" -o -name "*.rdb*" -o -name "*.tar*" -o -name "*.json*" \) ! -name "*.meta" | sort -r | head -n 5)
            
            for backup_file in $backup_files; do
                total=$((total + 1))
                if verify_specific_file "$backup_file" 2>>"$LOG_FILE"; then
                    passed=$((passed + 1))
                    log "✓ $backup_file - 验证通过"
                else
                    failed=$((failed + 1))
                    log "✗ $backup_file - 验证失败"
                fi
            done
        fi
    done
    
    log "=========================================="
    log "验证统计:"
    log "总计: $total"
    log "通过: $passed"
    log "失败: $failed"
    log "=========================================="
    
    if [ $failed -gt 0 ]; then
        return 1
    fi
    
    return 0
}

# 主函数
main() {
    log "=========================================="
    log "备份验证开始"
    log "验证类型: $VERIFY_TYPE"
    log "=========================================="
    
    case "$VERIFY_TYPE" in
        all)
            verify_all_backups
            ;;
        postgres)
            verify_specific_file "$(find "$BACKUP_DIR/postgres" -type f -name "*.sql*" ! -name "*.meta" | sort -r | head -n 1)"
            ;;
        redis)
            verify_specific_file "$(find "$BACKUP_DIR/redis" -type f -name "*.rdb*" ! -name "*.meta" | sort -r | head -n 1)"
            ;;
        vector)
            verify_specific_file "$(find "$BACKUP_DIR/vector" -type f -name "*.tar*" ! -name "*.meta" | sort -r | head -n 1)"
            ;;
        specific)
            if [ -z "$BACKUP_FILE" ]; then
                error_exit "请指定备份文件路径"
            fi
            verify_specific_file "$BACKUP_FILE"
            ;;
        *)
            error_exit "不支持的验证类型: $VERIFY_TYPE (支持: all, postgres, redis, vector, specific)"
            ;;
    esac
    
    log "=========================================="
    log "备份验证完成"
    log "=========================================="
    
    exit 0
}

# 执行主函数
main "$@"









