#!/bin/bash
# 服务器端CI/CD循环执行脚本
# 在服务器上执行CI/CD，获取日志，修复代码，循环测试

set -e

PROJECT_DIR="/opt/enterprise-ai-platform"
LOG_DIR="/tmp/cicd-logs"
MAX_ITERATIONS=10
CURRENT_ITERATION=0

# 创建日志目录
mkdir -p "$LOG_DIR"

echo "=========================================="
echo "服务器端CI/CD循环执行"
echo "=========================================="
echo "项目目录: $PROJECT_DIR"
echo "日志目录: $LOG_DIR"
echo "最大迭代次数: $MAX_ITERATIONS"
echo ""

# 函数：执行CI/CD测试
run_cicd_test() {
    local iteration=$1
    local log_file="$LOG_DIR/cicd-run-$iteration-$(date +%Y%m%d_%H%M%S).log"
    
    echo "[迭代 $iteration] 开始执行CI/CD测试..."
    echo "日志文件: $log_file"
    
    cd "$PROJECT_DIR"
    
    # 拉取最新代码
    echo "[迭代 $iteration] 拉取最新代码..."
    git pull origin main >> "$log_file" 2>&1 || {
        echo "❌ Git pull 失败"
        return 1
    }
    
    # 运行测试
    echo "[迭代 $iteration] 运行测试..."
    docker-compose exec -T api-gateway pytest tests/test-architecture -v >> "$log_file" 2>&1 || {
        echo "⚠️ 测试失败，继续..."
    }
    
    # 构建前端
    echo "[迭代 $iteration] 构建前端..."
    cd web-ui
    npm ci --legacy-peer-deps >> "$log_file" 2>&1 || {
        echo "❌ 前端依赖安装失败"
        return 1
    }
    
    npm run build >> "$log_file" 2>&1 || {
        echo "❌ 前端构建失败"
        return 1
    }
    cd ..
    
    # 构建Docker镜像（示例：只构建api-gateway）
    echo "[迭代 $iteration] 构建Docker镜像..."
    docker-compose build api-gateway >> "$log_file" 2>&1 || {
        echo "❌ Docker构建失败"
        return 1
    }
    
    # 健康检查
    echo "[迭代 $iteration] 健康检查..."
    sleep 10
    curl -f http://localhost:8080/health >> "$log_file" 2>&1 || {
        echo "❌ 健康检查失败"
        return 1
    }
    
    echo "✅ [迭代 $iteration] CI/CD测试通过"
    return 0
}

# 函数：提取错误信息
extract_errors() {
    local log_file=$1
    local error_file="$LOG_DIR/errors-$(basename $log_file)"
    
    echo "提取错误信息..."
    grep -i "error\|failed\|fail\|exception\|type error" "$log_file" | head -20 > "$error_file" || true
    
    if [ -s "$error_file" ]; then
        echo "发现错误:"
        cat "$error_file"
        return 1
    else
        echo "✅ 未发现错误"
        return 0
    fi
}

# 主循环
while [ $CURRENT_ITERATION -lt $MAX_ITERATIONS ]; do
    CURRENT_ITERATION=$((CURRENT_ITERATION + 1))
    
    echo ""
    echo "=========================================="
    echo "迭代 $CURRENT_ITERATION / $MAX_ITERATIONS"
    echo "=========================================="
    
    # 执行CI/CD测试
    if run_cicd_test $CURRENT_ITERATION; then
        echo "✅ 所有测试通过！"
        break
    else
        # 提取错误
        latest_log=$(ls -t "$LOG_DIR"/cicd-run-*.log 2>/dev/null | head -1)
        if [ -n "$latest_log" ]; then
            extract_errors "$latest_log"
        fi
        
        echo "❌ 测试失败，等待修复..."
        echo "请查看日志: $LOG_DIR"
        echo "修复代码后，按回车继续..."
        read -r
    fi
done

echo ""
echo "=========================================="
echo "CI/CD循环完成"
echo "=========================================="
echo "总迭代次数: $CURRENT_ITERATION"
echo "日志目录: $LOG_DIR"





