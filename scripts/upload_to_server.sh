#!/bin/bash
# 统一意图识别LLM增强 - 服务器上传脚本
# 适用于Linux/Mac

set -e

echo "========================================"
echo "  统一意图识别LLM增强 - 服务器上传"
echo "========================================"
echo ""

# 配置
read -p "请输入服务器地址 (例如: user@192.168.1.100): " SERVER_HOST
read -p "请输入服务器路径 (例如: /opt/enterprise-ai-platform): " SERVER_PATH

# 检查SSH连接
echo "[检查] SSH连接..."
if ssh -o ConnectTimeout=5 $SERVER_HOST "echo 'SSH连接成功'" > /dev/null 2>&1; then
    echo "[OK] SSH连接成功"
else
    echo "[错误] SSH连接失败，请检查:"
    echo "  1. SSH密钥是否配置"
    echo "  2. 服务器地址是否正确"
    echo "  3. 网络连接是否正常"
    exit 1
fi

# 需要上传的文件列表
FILES=(
    "services/llm_client.py"
    "services/semantic_engine_adapter.py"
    "services/unified_intent_service.py"
    "api/unified_intent_api.py"
    "api/collaborative_interface_api.py"
    "tests/test_unified_intent_llm_enhancement.py"
    "docs/UNIFIED_INTENT_LLM_ENHANCEMENT_PLAN_V2.md"
    "DEPLOYMENT_GUIDE.md"
    "DEPLOYMENT_CHECKLIST.md"
    "LLM_ENHANCEMENT_DEPLOYMENT_SUMMARY.md"
)

# 创建临时目录
TEMP_DIR=$(mktemp -d)
echo "[准备] 创建临时目录: $TEMP_DIR"

# 复制文件到临时目录
echo "[准备] 复制文件..."
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        dest_dir="$TEMP_DIR/$(dirname $file)"
        mkdir -p "$dest_dir"
        cp "$file" "$dest_dir/"
        echo "  [OK] $file"
    else
        echo "  [WARN] 文件不存在: $file"
    fi
done

# 创建部署说明文件
cat > "$TEMP_DIR/DEPLOY_NOTE.md" << 'EOF'
# 统一意图识别LLM增强 - 部署说明

## 部署步骤

1. 设置环境变量:
   export DEEPSEEK_API_KEY=your-api-key
   export LLM_BASE_URL=https://api.deepseek.com
   export LLM_MODEL=deepseek-chat
   export UNIFIED_INTENT_USE_LLM=true

2. 安装依赖:
   pip install httpx langchain-openai

3. 重启服务:
   docker-compose restart unified-intent-service
   # 或
   systemctl restart unified-intent-service

4. 验证部署:
   curl http://localhost:8002/health
   curl -X POST http://localhost:8002/api/v1/intent/understand \
     -H "Content-Type: application/json" \
     -d '{"user_input": "创建采购订单"}'

## 回滚方法

如果出现问题，可以快速回滚:
   export UNIFIED_INTENT_USE_LLM=false
   docker-compose restart unified-intent-service
EOF

echo "[OK] 文件准备完成"
echo ""

# 上传到服务器
echo "[上传] 开始上传文件到服务器..."
echo "  目标: $SERVER_HOST:$SERVER_PATH"

scp -r "$TEMP_DIR"/* "$SERVER_HOST:$SERVER_PATH/"

if [ $? -eq 0 ]; then
    echo "[OK] 文件上传成功"
else
    echo "[错误] 文件上传失败"
    exit 1
fi

# 清理临时目录
echo "[清理] 删除临时目录..."
rm -rf "$TEMP_DIR"

echo ""
echo "========================================"
echo "  上传完成！"
echo "========================================"
echo ""
echo "下一步操作:"
echo "  1. SSH登录服务器: ssh $SERVER_HOST"
echo "  2. 进入项目目录: cd $SERVER_PATH"
echo "  3. 设置环境变量（参考 DEPLOY_NOTE.md）"
echo "  4. 重启服务"
echo "  5. 验证部署"
echo ""

