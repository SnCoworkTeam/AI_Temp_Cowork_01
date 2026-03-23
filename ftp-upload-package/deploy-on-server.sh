#!/bin/bash
# OpenCode 服务器端部署脚本
# 执行：bash deploy-on-server.sh

set -e  # 遇到错误立即退出

echo "=========================================="
echo "OpenCode 服务器端部署"
echo "执行时间: $(date)"
echo "=========================================="
echo ""

# 当前目录应该是上传文件所在目录
UPLOAD_DIR=$(pwd)
DEPLOY_DIR="/opt/enterprise-ai-platform/opencode-server-export"

echo "[1] 检查上传文件..."
if [ ! -f "enterprise-ai-opencode-local-web.tar" ]; then
    echo "错误：找不到 enterprise-ai-opencode-local-web.tar"
    exit 1
fi
echo "✓ 镜像文件存在"

if [ ! -f "docker-compose.opencode.local-web.yml" ]; then
    echo "错误：找不到 docker-compose.opencode.local-web.yml"
    exit 1
fi
echo "✓ docker-compose 文件存在"
echo ""

echo "[2] 停止旧容器..."
docker stop enterprise-ai-opencode 2>/dev/null || true
docker rm enterprise-ai-opencode 2>/dev/null || true
echo "✓ 已停止旧容器"
echo ""

echo "[3] 备份旧镜像（如果存在）..."
OLD_IMAGE=$(docker images -q enterprise-ai-opencode-local-web:latest 2>/dev/null)
if [ -n "$OLD_IMAGE" ]; then
    BACKUP_TAG="enterprise-ai-opencode-local-web:backup-$(date +%Y%m%d-%H%M%S)"
    docker tag enterprise-ai-opencode-local-web:latest "$BACKUP_TAG"
    echo "✓ 旧镜像已标记为: $BACKUP_TAG"
else
    echo "ℹ 没有旧镜像需要备份"
fi
echo ""

echo "[4] 加载新镜像..."
docker load -i enterprise-ai-opencode-local-web.tar
if [ $? -ne 0 ]; then
    echo "错误：镜像加载失败"
    exit 1
fi
echo "✓ 新镜像已加载"
echo ""

echo "[5] 验证新镜像构建标记..."
BUILD_TAG=$(docker run --rm enterprise-ai-opencode-local-web:latest cat /app-web/build.txt 2>/dev/null)
echo "构建标记: $BUILD_TAG"
if [[ "$BUILD_TAG" == *"verified"* ]]; then
    echo "✓ 镜像包含验证标记"
else
    echo "⚠ 警告：镜像不包含 'verified' 标记"
fi
echo ""

echo "[6] 复制配置文件到部署目录..."
mkdir -p "$DEPLOY_DIR"
cp -f docker-compose.opencode.local-web.yml "$DEPLOY_DIR/"
echo "✓ docker-compose.yml 已复制"

# 如果有诊断脚本，也复制过去
if [ -f "diagnose-opencode.sh" ]; then
    cp -f diagnose-opencode.sh "$DEPLOY_DIR/"
    chmod +x "$DEPLOY_DIR/diagnose-opencode.sh"
    echo "✓ 诊断脚本已复制"
fi

# 如果没有 .env 文件，创建示例
if [ ! -f "$DEPLOY_DIR/.env" ]; then
    echo "ℹ 创建 .env 示例文件..."
    cat > "$DEPLOY_DIR/.env" <<EOF
# OpenCode 配置
OPENCODE_WORKSPACE=/opt/enterprise-ai-platform
OPENCODE_PORT=4096
OPENCODE_SERVER_USERNAME=opencode
OPENCODE_SERVER_PASSWORD=请修改为强密码

# 外部网络名称（如果已存在）
EXTERNAL_NETWORK_NAME=enterprise-ai-platform_enterprise-ai-network
EOF
    echo "⚠ 请编辑 $DEPLOY_DIR/.env 配置密码"
    echo "  vi $DEPLOY_DIR/.env"
else
    echo "✓ 使用现有 .env 文件"
fi
echo ""

echo "[7] 检查并创建 Docker 网络..."
NETWORK_NAME=$(grep EXTERNAL_NETWORK_NAME "$DEPLOY_DIR/.env" | cut -d'=' -f2 || echo "enterprise-ai-platform_enterprise-ai-network")
if ! docker network ls | grep -q "$NETWORK_NAME"; then
    echo "创建网络: $NETWORK_NAME"
    docker network create "$NETWORK_NAME"
else
    echo "✓ 网络已存在: $NETWORK_NAME"
fi
echo ""

echo "[8] 启动新容器..."
cd "$DEPLOY_DIR"
docker compose -f docker-compose.opencode.local-web.yml --env-file .env up -d --force-recreate
if [ $? -ne 0 ]; then
    echo "错误：容器启动失败"
    exit 1
fi
echo "✓ 容器已启动"
echo ""

echo "[9] 等待服务启动（最多30秒）..."
for i in {1..30}; do
    sleep 1
    if docker logs enterprise-ai-opencode 2>&1 | grep -q "listening on"; then
        echo "✓ 服务已启动（等待了 $i 秒）"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠ 超时，但继续验证"
    fi
done
echo ""

echo "[10] 查看容器日志..."
docker logs --tail 10 enterprise-ai-opencode
echo ""

echo "[11] 验证部署..."
echo "测试 /local-web-root（不带认证）..."
RESPONSE=$(curl -s -m 5 http://127.0.0.1:4096/local-web-root 2>&1)
if [ "$RESPONSE" = "local-web-ok" ]; then
    echo "✓ /local-web-root 正常返回（不需要认证）"
    echo ""
    echo "=========================================="
    echo "✓✓✓ 部署成功！✓✓✓"
    echo "=========================================="
    echo ""
    echo "OpenCode 已成功部署并验证"
    echo "访问地址: http://服务器IP:4096"
    echo "用户名: $(grep OPENCODE_SERVER_USERNAME .env | cut -d'=' -f2)"
    echo "密码: 见 .env 文件"
else
    echo "✗ /local-web-root 响应异常: $RESPONSE"
    echo ""
    echo "测试根路径..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 5 http://127.0.0.1:4096/ 2>&1)
    echo "根路径状态码: $HTTP_CODE"
    echo ""
    echo "⚠ 部署可能有问题，请检查："
    echo "1. 容器日志: docker logs enterprise-ai-opencode"
    echo "2. 环境变量: docker exec enterprise-ai-opencode env | grep OPENCODE"
    echo "3. 运行诊断: bash diagnose-opencode.sh"
fi
echo ""

echo "=========================================="
echo "常用命令："
echo "查看日志:   docker logs -f enterprise-ai-opencode"
echo "重启容器:   docker restart enterprise-ai-opencode"
echo "停止容器:   docker stop enterprise-ai-opencode"
echo "运行诊断:   bash diagnose-opencode.sh > diagnose.txt 2>&1"
echo "=========================================="
