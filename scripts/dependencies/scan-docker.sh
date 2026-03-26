#!/bin/bash
# 扫描Docker镜像和Dockerfile的安全漏洞

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "Docker安全扫描"
echo "=========================================="

# 检查Trivy是否安装
if ! command -v trivy &> /dev/null; then
    echo "错误: Trivy未安装"
    echo "安装方法: https://aquasecurity.github.io/trivy/latest/getting-started/installation/"
    exit 1
fi

# 检查Hadolint是否安装
if ! command -v hadolint &> /dev/null; then
    echo "警告: Hadolint未安装，跳过Dockerfile linting"
    echo "安装方法: https://github.com/hadolint/hadolint"
fi

# 扫描Dockerfile
echo ""
echo "扫描Dockerfile..."
DOCKERFILES=(
    "mcp-gateway/Dockerfile"
    "workflow-engine/Dockerfile"
    "auth-service/Dockerfile"
    "knowledge-base/Dockerfile"
    "web-ui/Dockerfile"
)

for dockerfile in "${DOCKERFILES[@]}"; do
    if [ -f "$dockerfile" ]; then
        echo ""
        echo "扫描 $dockerfile..."
        echo "----------------------------------------"
        
        # Trivy扫描配置文件
        trivy config "$dockerfile" || true
        
        # Hadolint扫描（如果可用）
        if command -v hadolint &> /dev/null; then
            hadolint "$dockerfile" || true
        fi
    fi
done

# 扫描docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    echo ""
    echo "扫描 docker-compose.yml..."
    trivy config docker-compose.yml || true
fi

# 扫描已构建的镜像
echo ""
echo "扫描Docker镜像..."
IMAGES=(
    "mcp-gateway:latest"
    "workflow-engine:latest"
    "auth-service:latest"
    "knowledge-base:latest"
    "web-ui:latest"
)

for image in "${IMAGES[@]}"; do
    if docker images | grep -q "$image"; then
        echo ""
        echo "扫描镜像 $image..."
        echo "----------------------------------------"
        trivy image "$image" || true
    else
        echo "镜像 $image 未找到，跳过"
    fi
done

echo ""
echo "=========================================="
echo "Docker扫描完成"
echo "=========================================="









