#!/bin/bash
# 自动修复和部署脚本
# 在服务器上执行，自动检测错误，修复，提交，推送，重新测试

set -e

PROJECT_DIR="/opt/enterprise-ai-platform"
LOG_DIR="/tmp/cicd-logs"
GIT_REPO="origin"
GIT_BRANCH="main"

cd "$PROJECT_DIR"

echo "=========================================="
echo "自动修复和部署"
echo "=========================================="

# 函数：运行测试并捕获错误
run_tests() {
    local log_file="$LOG_DIR/test-$(date +%Y%m%d_%H%M%S).log"
    
    echo "运行测试..."
    
    # 前端构建测试
    cd web-ui
    npm run build > "$log_file" 2>&1
    local frontend_status=$?
    cd ..
    
    if [ $frontend_status -ne 0 ]; then
        echo "❌ 前端构建失败"
        extract_typescript_errors "$log_file"
        return 1
    fi
    
    echo "✅ 前端构建成功"
    return 0
}

# 函数：提取TypeScript错误
extract_typescript_errors() {
    local log_file=$1
    
    echo "提取TypeScript错误..."
    
    # 提取错误行
    grep -A 5 "Type error:" "$log_file" | while IFS= read -r line; do
        echo "$line"
        
        # 提取文件路径和行号
        if echo "$line" | grep -q "\.tsx\?:"; then
            file_path=$(echo "$line" | grep -oP '\./src/[^:]+' | head -1)
            line_num=$(echo "$line" | grep -oP ':\d+:' | grep -oP '\d+' | head -1)
            
            if [ -n "$file_path" ] && [ -n "$line_num" ]; then
                echo "文件: $file_path"
                echo "行号: $line_num"
                echo "内容:"
                sed -n "${line_num}p" "$PROJECT_DIR/web-ui/$file_path" || true
            fi
        fi
    done
}

# 函数：自动修复常见错误
auto_fix_errors() {
    local fixed=false
    
    echo "尝试自动修复..."
    
    # 修复1: display_name缺失
    if grep -q "display_name.*does not exist" "$LOG_DIR"/*.log 2>/dev/null; then
        echo "修复: 添加display_name到User接口"
        if ! grep -q "display_name" "$PROJECT_DIR/web-ui/src/lib/api/auth.ts"; then
            sed -i '/session_id?: string/a\  display_name?: string' "$PROJECT_DIR/web-ui/src/lib/api/auth.ts"
            fixed=true
        fi
    fi
    
    # 修复2: 图标导入缺失
    if grep -q "Cannot find name.*Icon" "$LOG_DIR"/*.log 2>/dev/null; then
        echo "修复: 检查图标导入..."
        # 这里可以添加更多自动修复逻辑
    fi
    
    if [ "$fixed" = true ]; then
        echo "✅ 已自动修复部分错误"
        return 0
    else
        echo "⚠️ 无法自动修复，需要手动修复"
        return 1
    fi
}

# 函数：提交和推送
commit_and_push() {
    echo "提交更改..."
    
    git add -A
    git commit -m "fix: 自动修复CI/CD错误

- 修复TypeScript类型错误
- 修复构建问题" || {
        echo "⚠️ 没有更改需要提交"
        return 0
    }
    
    echo "推送到远程..."
    git push "$GIT_REPO" "$GIT_BRANCH" || {
        echo "❌ 推送失败"
        return 1
    }
    
    echo "✅ 已提交并推送"
    return 0
}

# 主流程
main() {
    # 1. 拉取最新代码
    echo "[1/4] 拉取最新代码..."
    git pull "$GIT_REPO" "$GIT_BRANCH" || {
        echo "❌ Git pull 失败"
        exit 1
    }
    
    # 2. 运行测试
    echo "[2/4] 运行测试..."
    if ! run_tests; then
        # 3. 尝试自动修复
        echo "[3/4] 尝试自动修复..."
        if auto_fix_errors; then
            # 4. 提交和推送
            echo "[4/4] 提交和推送..."
            if commit_and_push; then
                echo "✅ 已自动修复并推送，等待GitHub Actions执行..."
                return 0
            fi
        fi
        
        echo "❌ 需要手动修复"
        return 1
    fi
    
    echo "✅ 所有测试通过，无需修复"
    return 0
}

main "$@"





