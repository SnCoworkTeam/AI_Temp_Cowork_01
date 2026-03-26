#!/bin/bash

# 分类体系迁移部署脚本
# 使用方法: ./scripts/deploy-classification-migration.sh

set -e  # 遇到错误立即退出

echo "=========================================="
echo "分类体系迁移部署脚本"
echo "=========================================="

# 配置变量
PROJECT_ROOT="/path/to/enterprise-ai-platform"
DB_NAME="luminaos"
DB_USER="postgres"
API_URL="http://localhost:8000"
BACKUP_DIR="/backup/database"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数：打印信息
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 函数：检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        error "$1 命令未找到，请先安装"
        exit 1
    fi
}

# 函数：检查服务是否运行
check_service() {
    if curl -s "$API_URL/api/health" > /dev/null; then
        info "Metadata Service 运行正常"
        return 0
    else
        error "Metadata Service 未运行或无法访问"
        return 1
    fi
}

# 函数：备份数据库
backup_database() {
    info "开始备份数据库..."
    
    BACKUP_FILE="$BACKUP_DIR/backup_before_028_$(date +%Y%m%d_%H%M%S).dump"
    
    # 创建备份目录
    mkdir -p "$BACKUP_DIR"
    
    # 执行备份
    if pg_dump -U "$DB_USER" -d "$DB_NAME" -F c -f "$BACKUP_FILE"; then
        info "数据库备份成功: $BACKUP_FILE"
        return 0
    else
        error "数据库备份失败"
        return 1
    fi
}

# 函数：执行数据库迁移
run_migration() {
    info "开始执行数据库迁移..."
    
    cd "$PROJECT_ROOT/database"
    
    # 检查当前版本
    CURRENT_VERSION=$(alembic current | grep -oP '^\w+' || echo "unknown")
    info "当前数据库版本: $CURRENT_VERSION"
    
    # 执行迁移
    if alembic upgrade head; then
        info "数据库迁移成功"
        return 0
    else
        error "数据库迁移失败"
        return 1
    fi
}

# 函数：验证迁移结果
verify_migration() {
    info "验证迁移结果..."
    
    # 检查字段是否存在
    FIELD_CHECK=$(psql -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_name = 'data_assets' 
        AND column_name = 'classification_dimensions';
    " | tr -d ' ')
    
    if [ "$FIELD_CHECK" -gt 0 ]; then
        info "字段验证通过"
        return 0
    else
        error "字段验证失败"
        return 1
    fi
}

# 函数：预览迁移
preview_migration() {
    info "预览迁移结果（试运行）..."
    
    RESPONSE=$(curl -s -X POST "$API_URL/api/classification/migration/preview?limit=10" \
        -H "Content-Type: application/json")
    
    if echo "$RESPONSE" | grep -q '"status":"success"'; then
        info "预览成功"
        echo "$RESPONSE" | python3 -m json.tool
        return 0
    else
        error "预览失败"
        echo "$RESPONSE"
        return 1
    fi
}

# 函数：执行试运行迁移
dry_run_migration() {
    info "执行试运行迁移..."
    
    RESPONSE=$(curl -s -X POST "$API_URL/api/classification/migrate" \
        -H "Content-Type: application/json" \
        -d '{"dry_run": true, "batch_size": 10}')
    
    if echo "$RESPONSE" | grep -q '"status":"success"'; then
        info "试运行成功"
        echo "$RESPONSE" | python3 -m json.tool
        return 0
    else
        error "试运行失败"
        echo "$RESPONSE"
        return 1
    fi
}

# 函数：执行实际迁移
run_actual_migration() {
    warn "即将执行实际数据迁移，这将更新数据库！"
    read -p "确认继续？(yes/no): " CONFIRM
    
    if [ "$CONFIRM" != "yes" ]; then
        info "已取消迁移"
        return 1
    fi
    
    info "执行实际数据迁移..."
    
    RESPONSE=$(curl -s -X POST "$API_URL/api/classification/migrate" \
        -H "Content-Type: application/json" \
        -d '{"dry_run": false, "batch_size": 100}')
    
    if echo "$RESPONSE" | grep -q '"status":"success"'; then
        info "数据迁移成功"
        echo "$RESPONSE" | python3 -m json.tool
        return 0
    else
        error "数据迁移失败"
        echo "$RESPONSE"
        return 1
    fi
}

# 函数：测试API
test_api() {
    info "测试API接口..."
    
    # 测试健康检查
    if curl -s "$API_URL/api/health" > /dev/null; then
        info "健康检查通过"
    else
        error "健康检查失败"
        return 1
    fi
    
    # 测试维度查询
    if curl -s "$API_URL/api/data-assets?business_domain=finance&limit=1" > /dev/null; then
        info "维度查询API测试通过"
    else
        warn "维度查询API测试失败（可能是数据未迁移）"
    fi
    
    return 0
}

# 主函数
main() {
    info "开始部署流程..."
    
    # 检查必要命令
    check_command "alembic"
    check_command "psql"
    check_command "curl"
    check_command "python3"
    
    # 检查服务
    if ! check_service; then
        error "请先启动 Metadata Service"
        exit 1
    fi
    
    # 步骤1: 备份数据库
    if ! backup_database; then
        error "备份失败，终止部署"
        exit 1
    fi
    
    # 步骤2: 执行数据库迁移
    if ! run_migration; then
        error "数据库迁移失败，终止部署"
        exit 1
    fi
    
    # 步骤3: 验证迁移
    if ! verify_migration; then
        error "迁移验证失败"
        exit 1
    fi
    
    # 步骤4: 预览迁移
    if ! preview_migration; then
        warn "预览失败，但继续执行"
    fi
    
    # 步骤5: 试运行迁移
    if ! dry_run_migration; then
        warn "试运行失败，请检查日志"
        read -p "是否继续执行实际迁移？(yes/no): " CONTINUE
        if [ "$CONTINUE" != "yes" ]; then
            info "已取消实际迁移"
            exit 0
        fi
    fi
    
    # 步骤6: 执行实际迁移
    if ! run_actual_migration; then
        error "实际迁移失败"
        exit 1
    fi
    
    # 步骤7: 测试API
    test_api
    
    info "=========================================="
    info "部署完成！"
    info "=========================================="
    info "下一步："
    info "1. 访问前端页面验证: http://your-server:3000/admin/metadata"
    info "2. 检查分类维度是否正确显示"
    info "3. 测试维度查询功能"
}

# 执行主函数
main "$@"








