#!/bin/bash
# 自动从GitHub Actions获取错误并修复

set -e

PROJECT_DIR="/opt/enterprise-ai-platform"
REPO="PMLiuyubin/enterprise-ai-platform"
WORKFLOW="deploy.yml"
LOG_DIR="/tmp/github-errors"

mkdir -p "$LOG_DIR"

cd "$PROJECT_DIR"

echo "=========================================="
echo "自动获取GitHub Actions错误并修复"
echo "=========================================="

# 函数：获取最新运行
get_latest_run() {
    gh run list --workflow="$WORKFLOW" --repo="$REPO" --limit 1 --json databaseId,status,conclusion --jq '.[0]'
}

# 函数：下载运行日志
download_logs() {
    local run_id=$1
    local log_dir="$LOG_DIR/run-$run_id"
    
    mkdir -p "$log_dir"
    
    echo "下载运行 $run_id 的日志..."
    
    # 获取所有作业
    local jobs=$(gh run view "$run_id" --repo="$REPO" --json jobs --jq '.jobs[] | .name')
    
    for job in $jobs; do
        echo "  下载: $job"
        gh run view "$run_id" --repo="$REPO" --log --job="$job" > "$log_dir/$job.log" 2>&1 || true
    done
    
    echo "$log_dir"
}

# 函数：提取TypeScript错误
extract_typescript_errors() {
    local log_file=$1
    local errors_file="$LOG_DIR/typescript-errors.txt"
    
    > "$errors_file"
    
    # 提取TypeScript错误
    grep -A 10 "Type error:" "$log_file" | while IFS= read -r line; do
        echo "$line" >> "$errors_file"
        
        # 提取文件路径和行号
        if echo "$line" | grep -q "\.tsx\?:"; then
            local file_path=$(echo "$line" | grep -oP '\./src/[^:]+' | head -1)
            local line_num=$(echo "$line" | grep -oP ':\d+:' | grep -oP '\d+' | head -1)
            local error_msg=$(echo "$line" | grep -oP 'Type error:.*' | head -1)
            
            if [ -n "$file_path" ] && [ -n "$line_num" ] && [ -n "$error_msg" ]; then
                echo "FILE:$file_path|LINE:$line_num|ERROR:$error_msg" >> "$errors_file"
            fi
        fi
    done
    
    if [ -s "$errors_file" ]; then
        cat "$errors_file"
        return 0
    else
        return 1
    fi
}

# 函数：自动修复TypeScript错误
auto_fix_typescript() {
    local errors_file="$LOG_DIR/typescript-errors.txt"
    local fixed=false
    
    if [ ! -s "$errors_file" ]; then
        return 1
    fi
    
    echo "分析TypeScript错误并自动修复..."
    
    # 读取错误并修复
    while IFS='|' read -r file_info line_info error_info; do
        if [[ "$file_info" == FILE:* ]]; then
            local file_path=$(echo "$file_info" | cut -d: -f2-)
            local line_num=$(echo "$line_info" | cut -d: -f2)
            local error=$(echo "$error_info" | cut -d: -f2-)
            
            echo "修复: $file_path:$line_num - $error"
            
            # 修复1: display_name不存在
            if echo "$error" | grep -q "display_name.*does not exist"; then
                if [ "$file_path" = "./src/lib/api/auth.ts" ]; then
                    if ! grep -q "display_name" "web-ui/$file_path"; then
                        sed -i '/session_id?: string/a\  display_name?: string' "web-ui/$file_path"
                        echo "✅ 已添加display_name到User接口"
                        fixed=true
                    fi
                fi
            fi
            
            # 修复2: 图标未导入
            if echo "$error" | grep -q "Cannot find name"; then
                local missing_name=$(echo "$error" | grep -oP "Cannot find name '(\w+)'" | grep -oP "'\K[^']+")
                if [ -n "$missing_name" ]; then
                    echo "需要导入: $missing_name"
                    # 这里可以添加自动导入逻辑
                fi
            fi
            
            # 修复3: 类型不匹配
            if echo "$error" | grep -q "is not assignable to type"; then
                local actual_type=$(echo "$error" | grep -oP "Type '\w+'" | head -1)
                local expected_type=$(echo "$error" | grep -oP "type '\w+'" | head -1)
                echo "类型不匹配: $actual_type vs $expected_type"
                # 这里可以添加类型修复逻辑
            fi
        fi
    done < <(grep "^FILE:" "$errors_file")
    
    if [ "$fixed" = true ]; then
        return 0
    else
        return 1
    fi
}

# 函数：提取构建错误
extract_build_errors() {
    local log_file=$1
    local errors_file="$LOG_DIR/build-errors.txt"
    
    > "$errors_file"
    
    # 提取构建错误
    grep -i "error\|failed\|fail" "$log_file" | grep -v "continue-on-error" | head -20 > "$errors_file" || true
    
    if [ -s "$errors_file" ]; then
        cat "$errors_file"
        return 0
    else
        return 1
    fi
}

# 函数：提交修复
commit_fixes() {
    echo "提交修复..."
    
    git add -A
    
    # 检查是否有更改
    if git diff --cached --quiet; then
        echo "⚠️ 没有更改需要提交"
        return 1
    fi
    
    git commit -m "fix: 自动修复CI/CD错误

- 修复TypeScript类型错误
- 修复构建问题
- 自动修复时间: $(date '+%Y-%m-%d %H:%M:%S')" || {
        echo "❌ 提交失败"
        return 1
    }
    
    echo "推送到远程..."
    git push origin main || {
        echo "❌ 推送失败"
        return 1
    }
    
    echo "✅ 已提交并推送"
    return 0
}

# 主流程
main() {
    # 1. 获取最新运行
    echo "[1/4] 获取最新运行..."
    local run_info=$(get_latest_run)
    local run_id=$(echo "$run_info" | jq -r '.databaseId')
    local status=$(echo "$run_info" | jq -r '.status')
    local conclusion=$(echo "$run_info" | jq -r '.conclusion')
    
    if [ -z "$run_id" ] || [ "$run_id" = "null" ]; then
        echo "❌ 未找到运行"
        exit 1
    fi
    
    echo "运行ID: $run_id"
    echo "状态: $status"
    echo "结果: $conclusion"
    
    if [ "$status" != "completed" ]; then
        echo "⚠️ 运行尚未完成，等待..."
        # 可以添加等待逻辑
    fi
    
    if [ "$conclusion" = "success" ]; then
        echo "✅ 运行成功，无需修复"
        exit 0
    fi
    
    # 2. 下载日志
    echo "[2/4] 下载日志..."
    local log_dir=$(download_logs "$run_id")
    
    # 3. 提取并修复错误
    echo "[3/4] 提取并修复错误..."
    
    local has_errors=false
    
    # 检查前端测试错误
    if [ -f "$log_dir/frontend-test.log" ]; then
        if extract_typescript_errors "$log_dir/frontend-test.log"; then
            has_errors=true
            if auto_fix_typescript; then
                echo "✅ TypeScript错误已修复"
            else
                echo "⚠️ 无法自动修复所有TypeScript错误"
            fi
        fi
    fi
    
    # 检查构建错误
    if [ -f "$log_dir/build-images.log" ]; then
        if extract_build_errors "$log_dir/build-images.log"; then
            has_errors=true
            echo "⚠️ 发现构建错误，需要手动检查"
        fi
    fi
    
    if [ "$has_errors" = false ]; then
        echo "✅ 未发现可自动修复的错误"
        exit 0
    fi
    
    # 4. 提交修复
    echo "[4/4] 提交修复..."
    if commit_fixes; then
        echo "✅ 修复已提交，等待GitHub Actions执行..."
        echo "查看新运行: https://github.com/$REPO/actions"
    else
        echo "❌ 提交失败或无需提交"
    fi
}

main "$@"





