#!/bin/bash
# 智能自动修复：获取GitHub Actions错误，使用AI分析，自动修复

set -e

PROJECT_DIR="/opt/enterprise-ai-platform"
REPO="PMLiuyubin/enterprise-ai-platform"
WORKFLOW="deploy.yml"
LOG_DIR="/tmp/github-errors"

cd "$PROJECT_DIR"

echo "=========================================="
echo "智能自动修复系统"
echo "=========================================="

# 函数：获取最新失败运行
get_latest_failed_run() {
    gh run list --workflow="$WORKFLOW" --repo="$REPO" --limit 10 --json databaseId,status,conclusion --jq '.[] | select(.conclusion == "failure") | .databaseId' | head -1
}

# 函数：下载并分析日志
download_and_analyze() {
    local run_id=$1
    local log_dir="$LOG_DIR/run-$run_id"
    
    mkdir -p "$log_dir"
    
    echo "下载运行 $run_id 的日志..."
    
    # 下载所有作业日志
    local jobs=$(gh run view "$run_id" --repo="$REPO" --json jobs --jq '.jobs[] | .name')
    for job in $jobs; do
        gh run view "$run_id" --repo="$REPO" --log --job="$job" > "$log_dir/$job.log" 2>&1 || true
    done
    
    # 使用Python分析错误
    if command -v python3 &> /dev/null; then
        echo "使用AI分析错误..."
        python3 "$PROJECT_DIR/scripts/cicd/ai-fix-helper.py" "$log_dir" > "$log_dir/analysis.txt" 2>&1 || true
    fi
    
    echo "$log_dir"
}

# 函数：应用修复
apply_fixes() {
    local analysis_file="$1/error-analysis.json"
    
    if [ ! -f "$analysis_file" ]; then
        echo "⚠️ 未找到分析结果"
        return 1
    fi
    
    echo "应用自动修复..."
    
    # 读取分析结果
    local suggestions=$(python3 -c "
import json
import sys
try:
    with open('$analysis_file', 'r') as f:
        data = json.load(f)
        for suggestion in data.get('suggestions', []):
            print(suggestion)
except:
    pass
" 2>/dev/null)
    
    local fixed=false
    
    # 修复1: 添加缺失的属性
    if echo "$suggestions" | grep -q "添加缺失的属性: display_name"; then
        if ! grep -q "display_name" "web-ui/src/lib/api/auth.ts"; then
            sed -i '/session_id?: string/a\  display_name?: string' "web-ui/src/lib/api/auth.ts"
            echo "✅ 已添加display_name"
            fixed=true
        fi
    fi
    
    # 修复2: 添加缺失的导入
    while IFS= read -r suggestion; do
        if echo "$suggestion" | grep -q "导入:"; then
            local import_name=$(echo "$suggestion" | grep -oP "导入: (\w+)" | cut -d' ' -f2)
            local file_path=$(echo "$suggestion" | grep -oP "在 ([^ ]+) 中" | cut -d' ' -f2)
            
            if [ -n "$import_name" ] && [ -n "$file_path" ] && [ -f "web-ui/$file_path" ]; then
                # 检查是否已导入
                if ! grep -q "$import_name" "web-ui/$file_path"; then
                    # 查找lucide-react导入行
                    if grep -q "from \"lucide-react\"" "web-ui/$file_path"; then
                        sed -i "s/from \"lucide-react\"/&,\n  $import_name/" "web-ui/$file_path"
                        echo "✅ 已添加导入: $import_name"
                        fixed=true
                    fi
                fi
            fi
        fi
    done <<< "$suggestions"
    
    # 修复3: 修复类型错误（移除错误的else分支）
    if echo "$suggestions" | grep -q "类型不匹配"; then
        # 查找常见的类型错误模式并修复
        find web-ui/src -name "*.tsx" -o -name "*.ts" | while read file; do
            # 修复LucideIcon作为字符串渲染的问题
            if grep -q 'stat\.icon.*span' "$file"; then
                sed -i '/IconComponent ?/,/else/,/}/d' "$file" 2>/dev/null || true
                sed -i 's/{IconComponent ?/& \&\&/' "$file" 2>/dev/null || true
                echo "✅ 修复了 $file 中的类型错误"
                fixed=true
            fi
        done
    fi
    
    if [ "$fixed" = true ]; then
        return 0
    else
        return 1
    fi
}

# 函数：验证修复
verify_fixes() {
    echo "验证修复..."
    
    cd web-ui
    
    # 类型检查
    if npx tsc --noEmit 2>&1 | grep -q "error"; then
        echo "❌ 类型检查仍有错误"
        return 1
    fi
    
    echo "✅ 类型检查通过"
    return 0
}

# 主流程
main() {
    # 1. 获取最新失败运行
    echo "[1/5] 查找最新失败运行..."
    local run_id=$(get_latest_failed_run)
    
    if [ -z "$run_id" ]; then
        echo "✅ 没有失败的运行"
        exit 0
    fi
    
    echo "找到失败运行: $run_id"
    
    # 2. 下载并分析
    echo "[2/5] 下载并分析日志..."
    local log_dir=$(download_and_analyze "$run_id")
    
    # 3. 应用修复
    echo "[3/5] 应用自动修复..."
    if ! apply_fixes "$log_dir"; then
        echo "⚠️ 无法自动修复，请查看分析结果: $log_dir/analysis.txt"
        exit 1
    fi
    
    # 4. 验证修复
    echo "[4/5] 验证修复..."
    if ! verify_fixes; then
        echo "❌ 修复验证失败"
        exit 1
    fi
    
    # 5. 提交并推送
    echo "[5/5] 提交并推送..."
    git add -A
    
    if git diff --cached --quiet; then
        echo "⚠️ 没有更改需要提交"
        exit 0
    fi
    
    git commit -m "fix: 自动修复CI/CD错误

- 从GitHub Actions运行 $run_id 提取错误
- 自动应用修复
- 修复时间: $(date '+%Y-%m-%d %H:%M:%S')"
    
    git push origin main
    
    echo "✅ 修复已提交并推送"
    echo "查看新运行: https://github.com/$REPO/actions"
}

main "$@"





