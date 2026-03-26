#!/bin/bash
# 导出Docker镜像为离线部署包
# 使用方法: bash export-images.sh [输出目录]

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 输出目录
OUTPUT_DIR="${1:-./docker-images-export}"
EXPORT_DIR="$OUTPUT_DIR/images"
MANIFEST_FILE="$OUTPUT_DIR/images-manifest.txt"
LOAD_SCRIPT="$OUTPUT_DIR/load-images.sh"

echo -e "${BLUE}=========================================="
echo "Docker镜像导出工具"
echo "==========================================${NC}"
echo ""

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker未安装${NC}"
    exit 1
fi

# 创建输出目录
mkdir -p "$EXPORT_DIR"
echo "输出目录: $OUTPUT_DIR"

# 从docker-compose文件读取镜像列表
get_images_from_compose() {
    local compose_file=$1
    if [ -f "$compose_file" ]; then
        grep -E "^\s+image:" "$compose_file" | sed 's/.*image:\s*//' | sed 's/#.*$//' | tr -d ' ' | grep -v '^$'
    fi
}

# 收集所有需要的镜像
echo "收集镜像列表..."
IMAGES=()

# 从docker-compose文件收集
for compose_file in docker-compose.yml docker-compose.db.yml docker-compose.prod.yml; do
    if [ -f "$compose_file" ]; then
        echo "从 $compose_file 读取镜像..."
        while IFS= read -r image; do
            if [ -n "$image" ]; then
                IMAGES+=("$image")
                echo "  - $image"
            fi
        done < <(get_images_from_compose "$compose_file")
    fi
done

# 去重
UNIQUE_IMAGES=($(printf "%s\n" "${IMAGES[@]}" | sort -u))

if [ ${#UNIQUE_IMAGES[@]} -eq 0 ]; then
    echo -e "${RED}❌ 未找到任何镜像${NC}"
    exit 1
fi

echo ""
echo "共找到 ${#UNIQUE_IMAGES[@]} 个镜像:"
for img in "${UNIQUE_IMAGES[@]}"; do
    echo "  - $img"
done
echo ""

# 导出镜像
echo "开始导出镜像..."
EXPORTED=0
FAILED=0

for image in "${UNIQUE_IMAGES[@]}"; do
    # 生成文件名（将/替换为_，:替换为-）
    IMAGE_FILE=$(echo "$image" | sed 's|/|_|g' | sed 's|:|_|g')
    IMAGE_FILE="${IMAGE_FILE}.tar"
    IMAGE_PATH="$EXPORT_DIR/$IMAGE_FILE"
    
    echo -n "导出 $image ... "
    
    # 先拉取镜像（如果不存在）
    if ! docker images "$image" | grep -q "$(echo $image | cut -d: -f1)"; then
        echo -n "(拉取中...) "
        if ! docker pull "$image" > /dev/null 2>&1; then
            echo -e "${RED}❌ 拉取失败${NC}"
            ((FAILED++))
            continue
        fi
    fi
    
    # 导出镜像
    if docker save "$image" -o "$IMAGE_PATH" 2>/dev/null; then
        # 压缩镜像文件
        echo -n "(压缩中...) "
        if gzip -f "$IMAGE_PATH" 2>/dev/null; then
            echo -e "${GREEN}✅ 成功${NC}"
            echo "$image|$IMAGE_FILE.gz" >> "$MANIFEST_FILE"
            ((EXPORTED++))
        else
            echo -e "${YELLOW}⚠️  导出成功但压缩失败${NC}"
            echo "$image|$IMAGE_FILE" >> "$MANIFEST_FILE"
            ((EXPORTED++))
        fi
    else
        echo -e "${RED}❌ 导出失败${NC}"
        ((FAILED++))
    fi
done

# 创建导入脚本
echo ""
echo "创建导入脚本..."
cat > "$LOAD_SCRIPT" <<'EOF'
#!/bin/bash
# Docker镜像导入脚本
# 使用方法: bash load-images.sh

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGES_DIR="$SCRIPT_DIR/images"
MANIFEST_FILE="$SCRIPT_DIR/images-manifest.txt"

echo -e "${BLUE}=========================================="
echo "Docker镜像导入工具"
echo "==========================================${NC}"
echo ""

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker未安装${NC}"
    exit 1
fi

# 检查镜像目录
if [ ! -d "$IMAGES_DIR" ]; then
    echo -e "${RED}❌ 镜像目录不存在: $IMAGES_DIR${NC}"
    exit 1
fi

# 检查manifest文件
if [ ! -f "$MANIFEST_FILE" ]; then
    echo -e "${RED}❌ 镜像清单文件不存在: $MANIFEST_FILE${NC}"
    exit 1
fi

# 导入镜像
echo "开始导入镜像..."
LOADED=0
FAILED=0

while IFS='|' read -r image file; do
    if [ -z "$image" ] || [ -z "$file" ]; then
        continue
    fi
    
    IMAGE_PATH="$IMAGES_DIR/$file"
    
    if [ ! -f "$IMAGE_PATH" ]; then
        echo -e "${YELLOW}⚠️  镜像文件不存在: $file，跳过${NC}"
        ((FAILED++))
        continue
    fi
    
    echo -n "导入 $image ... "
    
    # 检查文件是否压缩
    if [[ "$file" == *.gz ]]; then
        # 解压并导入
        if gunzip -c "$IMAGE_PATH" | docker load > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 成功${NC}"
            ((LOADED++))
        else
            echo -e "${RED}❌ 失败${NC}"
            ((FAILED++))
        fi
    else
        # 直接导入
        if docker load -i "$IMAGE_PATH" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 成功${NC}"
            ((LOADED++))
        else
            echo -e "${RED}❌ 失败${NC}"
            ((FAILED++))
        fi
    fi
done < "$MANIFEST_FILE"

echo ""
echo "导入完成: 成功 $LOADED, 失败 $FAILED"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 所有镜像导入成功！${NC}"
    echo ""
    echo "现在可以运行部署脚本:"
    echo "  bash deploy-server.sh --offline"
    exit 0
else
    echo -e "${YELLOW}⚠️  部分镜像导入失败${NC}"
    exit 1
fi
EOF

chmod +x "$LOAD_SCRIPT"

# 创建README
cat > "$OUTPUT_DIR/README.md" <<EOF
# Docker镜像离线部署包

## 说明

此目录包含项目的所有Docker镜像，用于离线部署。

## 使用方法

### 1. 上传到服务器

将整个 \`docker-images-export\` 目录上传到服务器：

\`\`\`bash
# 方式1: 使用scp
scp -r docker-images-export user@server:/tmp/

# 方式2: 使用Git LFS（如果镜像文件已通过Git LFS管理）
git lfs pull
\`\`\`

### 2. 在服务器上导入镜像

\`\`\`bash
cd /tmp/docker-images-export
bash load-images.sh
\`\`\`

### 3. 部署项目

\`\`\`bash
cd /opt/enterprise-ai-platform
bash scripts/deployment/deploy-server.sh --offline
\`\`\`

## 镜像列表

EOF

while IFS='|' read -r image file; do
    if [ -n "$image" ]; then
        echo "- $image ($file)" >> "$OUTPUT_DIR/README.md"
    fi
done < "$MANIFEST_FILE"

# 创建压缩包
echo ""
echo "创建压缩包..."
cd "$(dirname "$OUTPUT_DIR")"
TARBALL="$(basename "$OUTPUT_DIR").tar.gz"
tar -czf "$TARBALL" "$(basename "$OUTPUT_DIR")" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  压缩失败，请手动压缩${NC}"
}

echo ""
echo -e "${GREEN}=========================================="
echo "✅ 镜像导出完成"
echo "==========================================${NC}"
echo ""
echo "导出统计:"
echo "  成功: $EXPORTED"
echo "  失败: $FAILED"
echo ""
echo "输出目录: $OUTPUT_DIR"
if [ -f "$TARBALL" ]; then
    echo "压缩包: $TARBALL ($(du -h "$TARBALL" | cut -f1))"
fi
echo ""
echo "下一步:"
echo "  1. 将 $OUTPUT_DIR 目录上传到服务器"
echo "  2. 在服务器上运行: bash $OUTPUT_DIR/load-images.sh"
echo "  3. 运行部署脚本: bash deploy-server.sh --offline"
echo ""

