#!/bin/bash
# 在Docker容器中安装pyrfc的脚本
# 注意：需要先安装SAP NWRFC SDK

set -e

echo "=========================================="
echo "安装 pyrfc 到 Docker 容器"
echo "=========================================="

# 检查是否提供了 SAP NWRFC SDK 路径
if [ -z "$SAPNWRFC_HOME" ]; then
    echo "⚠️  警告: SAPNWRFC_HOME 环境变量未设置"
    echo "   如果 SAP NWRFC SDK 已安装在容器中，请设置:"
    echo "   export SAPNWRFC_HOME=/path/to/nwrfcsdk"
    echo ""
    echo "   或者，如果您有 SAP NWRFC SDK 文件，可以："
    echo "   1. 将 SDK 文件复制到容器中"
    echo "   2. 解压到 /opt/nwrfcsdk"
    echo "   3. 设置环境变量: export SAPNWRFC_HOME=/opt/nwrfcsdk"
    echo ""
    echo "   尝试直接安装 pyrfc（可能需要预编译版本）..."
fi

# 设置环境变量（如果提供了）
if [ -n "$SAPNWRFC_HOME" ]; then
    export LD_LIBRARY_PATH=$SAPNWRFC_HOME/lib:$LD_LIBRARY_PATH
    export PATH=$SAPNWRFC_HOME/lib:$PATH
    echo "✅ 使用 SAP NWRFC SDK: $SAPNWRFC_HOME"
fi

# 尝试安装 pyrfc
echo ""
echo "正在安装 pyrfc..."
pip install --no-cache-dir pyrfc || {
    echo "❌ 安装失败"
    echo ""
    echo "可能的原因："
    echo "1. 需要 SAP NWRFC SDK（从 SAP 官网下载）"
    echo "2. Python 版本不兼容"
    echo "3. 缺少编译工具"
    echo ""
    echo "解决方案："
    echo "1. 下载 SAP NWRFC SDK for Linux"
    echo "2. 解压到容器中的某个目录（如 /opt/nwrfcsdk）"
    echo "3. 设置环境变量: export SAPNWRFC_HOME=/opt/nwrfcsdk"
    echo "4. 重新运行此脚本"
    exit 1
}

# 验证安装
echo ""
echo "验证安装..."
python -c "import pyrfc; print(f'✅ pyrfc 安装成功，版本: {pyrfc.__version__}')" || {
    echo "❌ 验证失败"
    exit 1
}

echo ""
echo "=========================================="
echo "✅ pyrfc 安装完成！"
echo "=========================================="

