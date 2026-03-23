#!/bin/bash

# 定时备份调度脚本
# 根据备份策略自动执行备份任务

set -euo pipefail

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/logs/backup}"

# 时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATE=$(date +"%Y%m%d")
WEEKDAY=$(date +"%u")  # 1=Monday, 7=Sunday
HOUR=$(date +"%H")

# 创建目录
mkdir -p "$LOG_DIR"

# 日志文件
LOG_FILE="$LOG_DIR/schedule_${TIMESTAMP}.log"

# 日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

# 发送告警
send_alert() {
    local service="$1"
    local status="$2"
    local message="$3"
    
    log "告警: $service - $status - $message"
    
    # 发送邮件
    if [ -n "${ALERT_EMAIL:-}" ] && command -v mail > /dev/null 2>&1; then
        echo "$message" | mail -s "[备份告警] $service - $status" "$ALERT_EMAIL" 2>/dev/null || true
    fi
    
    # 发送Webhook
    if [ -n "${ALERT_WEBHOOK:-}" ]; then
        curl -X POST "$ALERT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"service\":\"$service\",\"status\":\"$status\",\"message\":\"$message\",\"timestamp\":\"$TIMESTAMP\"}" \
            2>/dev/null || true
    fi
}

# 执行备份并检查结果
execute_backup() {
    local service="$1"
    local backup_type="$2"
    local script_path="$SCRIPT_DIR/backup-${service}.sh"
    
    if [ ! -f "$script_path" ]; then
        error_exit "备份脚本不存在: $script_path"
    fi
    
    log "执行 $service $backup_type 备份..."
    
    if bash "$script_path" "$backup_type" >> "$LOG_FILE" 2>&1; then
        log "$service $backup_type 备份成功"
        return 0
    else
        log "$service $backup_type 备份失败"
        send_alert "$service" "failure" "$service $backup_type 备份失败"
        return 1
    fi
}

# PostgreSQL备份策略
backup_postgres() {
    local success=0
    
    # 全量备份：每周日 02:00
    if [ "$WEEKDAY" = "7" ] && [ "$HOUR" = "02" ]; then
        log "执行PostgreSQL全量备份（每周日）..."
        if execute_backup "postgres" "full"; then
            success=1
        fi
    fi
    
    # 增量备份：每天 02:00（除了周日）
    if [ "$WEEKDAY" != "7" ] && [ "$HOUR" = "02" ]; then
        log "执行PostgreSQL增量备份（每天）..."
        if execute_backup "postgres" "incremental"; then
            success=1
        fi
    fi
    
    # 日志备份：每6小时（02:00, 08:00, 14:00, 20:00）
    if [ "$HOUR" = "02" ] || [ "$HOUR" = "08" ] || [ "$HOUR" = "14" ] || [ "$HOUR" = "20" ]; then
        log "执行PostgreSQL日志备份（每6小时）..."
        if execute_backup "postgres" "log"; then
            success=1
        fi
    fi
    
    return $success
}

# Redis备份策略
backup_redis() {
    local success=0
    
    # 全量备份：每周日 02:30
    if [ "$WEEKDAY" = "7" ] && [ "$HOUR" = "02" ]; then
        sleep 1800  # 等待30分钟，避免与PostgreSQL备份冲突
        log "执行Redis全量备份（每周日）..."
        if execute_backup "redis" "rdb"; then
            success=1
        fi
    fi
    
    # 增量备份：每天 03:00
    if [ "$HOUR" = "03" ]; then
        log "执行Redis增量备份（每天）..."
        if execute_backup "redis" "rdb"; then
            success=1
        fi
    fi
    
    return $success
}

# 向量数据库备份策略
backup_vector() {
    local success=0
    
    # 全量备份：每周日 04:00
    if [ "$WEEKDAY" = "7" ] && [ "$HOUR" = "04" ]; then
        log "执行向量数据库全量备份（每周日）..."
        if execute_backup "vector" "full"; then
            success=1
        fi
    fi
    
    # 增量备份：每天 05:00
    if [ "$HOUR" = "05" ]; then
        log "执行向量数据库增量备份（每天）..."
        if execute_backup "vector" "full"; then
            success=1
        fi
    fi
    
    return $success
}

# 检查存储空间
check_storage_space() {
    log "检查存储空间..."
    
    BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
    THRESHOLD_PERCENT="${STORAGE_THRESHOLD:-80}"
    
    if [ -d "$BACKUP_DIR" ]; then
        # 获取磁盘使用率
        USAGE=$(df "$BACKUP_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
        
        if [ "$USAGE" -gt "$THRESHOLD_PERCENT" ]; then
            log "警告: 存储空间使用率 ${USAGE}% 超过阈值 ${THRESHOLD_PERCENT}%"
            send_alert "storage" "warning" "存储空间使用率 ${USAGE}% 超过阈值 ${THRESHOLD_PERCENT}%"
        else
            log "存储空间正常: ${USAGE}%"
        fi
    fi
}

# 生成备份报告
generate_report() {
    log "生成备份报告..."
    
    REPORT_FILE="$LOG_DIR/backup_report_${DATE}.txt"
    
    cat > "$REPORT_FILE" <<EOF
========================================
备份报告
日期: $DATE
生成时间: $(date +"%Y-%m-%d %H:%M:%S")
========================================

备份策略:
- PostgreSQL全量备份: 每周日 02:00
- PostgreSQL增量备份: 每天 02:00
- PostgreSQL日志备份: 每6小时
- Redis全量备份: 每周日 02:30
- Redis增量备份: 每天 03:00
- 向量数据库全量备份: 每周日 04:00
- 向量数据库增量备份: 每天 05:00

存储配置:
- 本地保留: ${RETENTION_DAYS:-7} 天
- 云存储: ${CLOUD_STORAGE_TYPE:-未配置}

EOF
    
    # 统计备份文件
    for service in postgres redis vector; do
        BACKUP_DIR_SERVICE="$PROJECT_ROOT/backups/$service"
        if [ -d "$BACKUP_DIR_SERVICE" ]; then
            BACKUP_COUNT=$(find "$BACKUP_DIR_SERVICE" -type f -name "*.sql*" -o -name "*.rdb*" -o -name "*.tar*" | wc -l)
            BACKUP_SIZE=$(du -sh "$BACKUP_DIR_SERVICE" | cut -f1)
            echo "$service 备份数量: $BACKUP_COUNT" >> "$REPORT_FILE"
            echo "$service 备份大小: $BACKUP_SIZE" >> "$REPORT_FILE"
        fi
    done
    
    log "备份报告已生成: $REPORT_FILE"
}

# 主函数
main() {
    log "=========================================="
    log "定时备份调度开始"
    log "日期: $DATE"
    log "星期: $WEEKDAY"
    log "小时: $HOUR"
    log "=========================================="
    
    # 执行备份
    BACKUP_SUCCESS=true
    
    backup_postgres || BACKUP_SUCCESS=false
    backup_redis || BACKUP_SUCCESS=false
    backup_vector || BACKUP_SUCCESS=false
    
    # 检查存储空间
    check_storage_space
    
    # 生成报告
    if [ "$HOUR" = "06" ]; then
        generate_report
    fi
    
    if [ "$BACKUP_SUCCESS" = "true" ]; then
        log "=========================================="
        log "定时备份调度完成"
        log "=========================================="
        exit 0
    else
        log "=========================================="
        log "定时备份调度完成（部分失败）"
        log "=========================================="
        exit 1
    fi
}

# 执行主函数
main









