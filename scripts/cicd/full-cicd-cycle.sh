#!/bin/bash
# 完整的CI/CD循环：在服务器上执行，获取GitHub Actions日志，修复，提交，循环

set -e

PROJECT_DIR="/opt/enterprise-ai-platform"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAX_ITERATIONS=5

cd "$PROJECT_DIR"

echo "=========================================="
echo "完整CI/CD循环"
echo "=========================================="
echo "项目目录: $PROJECT_DIR"
echo ""

# 函数：触发GitHub Actions
trigger_workflow() {
    echo "触发GitHub Actions工作流..."
    gh workflow run deploy.yml --field environment=staging --repo PMLiuyubin/enterprise-ai-platform || {
        echo "❌ 触发失败"
        return 1
    }
    echo "✅ 已触发"
    sleep 5  # 等待工作流启动
}

# 函数：监控并获取日志
monitor_and_get_logs() {
    echo "监控GitHub Actions..."
    bash "$SCRIPT_DIR/monitor-github-actions.sh" || {
        echo "❌ 监控失败"
        return 1
    }
}

# 函数：分析错误并修复
analyze_and_fix() {
    local log_dir=$(ls -td /tmp/github-actions-logs/run-* 2>/dev/null | head -1)
    
    if [ -z "$log_dir" ]; then
        echo "⚠️ 未找到日志目录"
        return 1
    fi
    
    echo "分析错误..."
    
    # 检查前端构建错误
    if grep -q "Type error" "$log_dir"/frontend-test.log 2>/dev/null; then
        echo "发现TypeScript错误，尝试修复..."
        bash "$SCRIPT_DIR/auto-fix-and-deploy.sh" || {
            echo "❌ 自动修复失败，需要手动修复"
            return 1
        }
        return 0
    fi
    
    # 检查测试错误
    if grep -q "FAILED\|ERROR" "$log_dir"/test.log 2>/dev/null; then
        echo "发现测试错误，需要手动修复"
        return 1
    fi
    
    echo "✅ 未发现需要修复的错误"
    return 0
}

# 主循环
iteration=0
while [ $iteration -lt $MAX_ITERATIONS ]; do
    iteration=$((iteration + 1))
    
    echo ""
    echo "=========================================="
    echo "迭代 $iteration / $MAX_ITERATIONS"
    echo "=========================================="
    
    # 1. 触发工作流
    if ! trigger_workflow; then
        echo "跳过本次迭代"
        continue
    fi
    
    # 2. 监控并获取日志
    if ! monitor_and_get_logs; then
        echo "跳过本次迭代"
        continue
    fi
    
    # 3. 分析并修复
    if analyze_and_fix; then
        echo "✅ 修复完成，等待下一轮测试..."
        sleep 30
    else
        echo "❌ 需要手动修复"
        echo "查看日志: /tmp/github-actions-logs"
        break
    fi
done

echo ""
echo "=========================================="
echo "循环完成"
echo "=========================================="





