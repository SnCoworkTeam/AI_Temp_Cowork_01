#!/bin/bash
# 监控GitHub Actions工作流并获取日志

set -e

REPO="PMLiuyubin/enterprise-ai-platform"
WORKFLOW="deploy.yml"
LOG_DIR="/tmp/github-actions-logs"
MAX_WAIT=1800  # 30分钟

mkdir -p "$LOG_DIR"

echo "=========================================="
echo "监控GitHub Actions工作流"
echo "=========================================="
echo "仓库: $REPO"
echo "工作流: $WORKFLOW"
echo ""

# 检查gh CLI是否安装
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) 未安装"
    echo "安装: https://cli.github.com/"
    exit 1
fi

# 检查是否已登录
if ! gh auth status &> /dev/null; then
    echo "❌ GitHub CLI 未登录"
    echo "请运行: gh auth login"
    exit 1
fi

# 函数：获取最新运行
get_latest_run() {
    gh run list --workflow="$WORKFLOW" --repo="$REPO" --limit 1 --json databaseId,status,conclusion --jq '.[0]'
}

# 函数：下载运行日志
download_run_logs() {
    local run_id=$1
    local output_dir="$LOG_DIR/run-$run_id"
    
    mkdir -p "$output_dir"
    
    echo "下载运行 $run_id 的日志..."
    
    # 获取所有作业
    local jobs=$(gh run view "$run_id" --repo="$REPO" --json jobs --jq '.jobs[] | .name')
    
    for job in $jobs; do
        echo "  下载作业: $job"
        gh run view "$run_id" --repo="$REPO" --log --job="$job" > "$output_dir/$job.log" 2>&1 || true
    done
    
    echo "✅ 日志已保存到: $output_dir"
}

# 函数：提取错误
extract_errors() {
    local log_dir=$1
    local error_file="$log_dir/errors.txt"
    
    echo "提取错误信息..."
    
    grep -r -i "error\|failed\|fail\|exception\|type error" "$log_dir"/*.log > "$error_file" 2>/dev/null || true
    
    if [ -s "$error_file" ]; then
        echo "发现错误:"
        head -30 "$error_file"
        return 1
    else
        echo "✅ 未发现错误"
        return 0
    fi
}

# 函数：等待运行完成
wait_for_run() {
    local run_id=$1
    local elapsed=0
    
    echo "等待运行 $run_id 完成..."
    
    while [ $elapsed -lt $MAX_WAIT ]; do
        local status=$(gh run view "$run_id" --repo="$REPO" --json status --jq '.status')
        
        if [ "$status" = "completed" ]; then
            local conclusion=$(gh run view "$run_id" --repo="$REPO" --json conclusion --jq '.conclusion')
            echo "运行完成，结果: $conclusion"
            return 0
        fi
        
        echo "  状态: $status (已等待 ${elapsed}s)"
        sleep 10
        elapsed=$((elapsed + 10))
    done
    
    echo "❌ 超时"
    return 1
}

# 主流程
main() {
    # 获取最新运行
    echo "获取最新运行..."
    local run_info=$(get_latest_run)
    local run_id=$(echo "$run_info" | jq -r '.databaseId')
    local status=$(echo "$run_info" | jq -r '.status')
    
    if [ -z "$run_id" ] || [ "$run_id" = "null" ]; then
        echo "❌ 未找到运行"
        exit 1
    fi
    
    echo "运行ID: $run_id"
    echo "状态: $status"
    echo ""
    
    # 如果还在运行，等待完成
    if [ "$status" != "completed" ]; then
        wait_for_run "$run_id"
    fi
    
    # 下载日志
    download_run_logs "$run_id"
    
    # 提取错误
    extract_errors "$LOG_DIR/run-$run_id"
    
    echo ""
    echo "=========================================="
    echo "完成"
    echo "=========================================="
    echo "日志目录: $LOG_DIR/run-$run_id"
    echo "查看运行: https://github.com/$REPO/actions/runs/$run_id"
}

main "$@"





