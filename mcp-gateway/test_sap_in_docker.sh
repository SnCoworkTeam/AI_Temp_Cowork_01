#!/bin/bash
# 在Docker容器中测试SAP ERP表查询工具

echo "=========================================="
echo "测试 SAP ERP 表查询工具（Docker容器）"
echo "=========================================="

# 检查 pyrfc 是否安装
echo ""
echo "检查 pyrfc 安装状态..."
python -c "import pyrfc; print(f'✅ pyrfc 已安装，版本: {pyrfc.__version__}')" 2>/dev/null || {
    echo "❌ pyrfc 未安装"
    echo ""
    echo "请先安装 pyrfc："
    echo "1. 确保 SAP NWRFC SDK 已安装到容器中"
    echo "2. 设置环境变量 SAPNWRFC_HOME"
    echo "3. 运行: pip install pyrfc"
    exit 1
}

# 设置 SAP 连接参数（从环境变量或使用默认值）
export SAP_USER=${SAP_USER:-admin}
export SAP_PASSWORD=${SAP_PASSWORD:-ad@kf29!()G}
export SAP_HOST=${SAP_HOST:-10.24.49.128}
export SAP_SYSNR=${SAP_SYSNR:-00}
export SAP_CLIENT=${SAP_CLIENT:-100}

echo ""
echo "SAP 连接信息:"
echo "  主机: $SAP_HOST"
echo "  客户端: $SAP_CLIENT"
echo "  用户: $SAP_USER"
echo ""

# 运行测试脚本
cd /app
python test_sap_erp_table_tool.py

