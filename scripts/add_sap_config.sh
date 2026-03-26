#!/bin/bash
# 添加SAP配置到配置中心

CONFIG_CENTER_URL="${CONFIG_CENTER_URL:-http://localhost:8090}"
ENVIRONMENT="${ENVIRONMENT:-default}"

echo "正在添加SAP配置到配置中心..."
echo "配置中心URL: $CONFIG_CENTER_URL"
echo "环境: $ENVIRONMENT"
echo ""

# 检查必需参数
if [ -z "$SAP_BASE_URL" ] || [ -z "$SAP_USERNAME" ] || [ -z "$SAP_PASSWORD" ]; then
    echo "错误: 请设置以下环境变量:"
    echo "  SAP_BASE_URL - SAP系统的基础URL"
    echo "  SAP_USERNAME - SAP用户名"
    echo "  SAP_PASSWORD - SAP密码"
    echo ""
    echo "可选参数:"
    echo "  SAP_CLIENT - SAP客户端编号 (默认: 100)"
    echo "  SAP_LANGUAGE - SAP系统语言 (默认: EN)"
    echo ""
    echo "示例:"
    echo "  export SAP_BASE_URL='https://your-sap-system.com'"
    echo "  export SAP_USERNAME='your_username'"
    echo "  export SAP_PASSWORD='your_password'"
    echo "  ./scripts/add_sap_config.sh"
    exit 1
fi

# 设置默认值
SAP_CLIENT="${SAP_CLIENT:-100}"
SAP_LANGUAGE="${SAP_LANGUAGE:-EN}"
SAP_TIMEOUT="${SAP_TIMEOUT:-300000}"
SAP_MAX_RETRIES="${SAP_MAX_RETRIES:-3}"
SAP_PAGE_SIZE="${SAP_PAGE_SIZE:-1000}"
SAP_MAX_RECORDS="${SAP_MAX_RECORDS:-10000}"

# 添加配置的函数
add_config() {
    local key=$1
    local value=$2
    local description=$3
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$CONFIG_CENTER_URL/api/config" \
        -H "Content-Type: application/json" \
        -d "{
            \"key\": \"$key\",
            \"value\": \"$value\",
            \"description\": \"$description\",
            \"environment\": \"$ENVIRONMENT\"
        }")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        echo "✅ 配置已添加: $key"
        return 0
    else
        echo "❌ 添加配置失败 $key: HTTP $http_code"
        echo "   响应: $body"
        return 1
    fi
}

# 添加所有SAP配置
success_count=0
fail_count=0

echo "开始添加配置..."
echo ""

add_config "sap.base_url" "$SAP_BASE_URL" "SAP系统的基础URL" && ((success_count++)) || ((fail_count++))
add_config "sap.username" "$SAP_USERNAME" "SAP用户名" && ((success_count++)) || ((fail_count++))
add_config "sap.password" "$SAP_PASSWORD" "SAP密码" && ((success_count++)) || ((fail_count++))
add_config "sap.client" "$SAP_CLIENT" "SAP客户端编号" && ((success_count++)) || ((fail_count++))
add_config "sap.language" "$SAP_LANGUAGE" "SAP系统语言" && ((success_count++)) || ((fail_count++))
add_config "sap.timeout" "$SAP_TIMEOUT" "SAP请求超时时间（毫秒）" && ((success_count++)) || ((fail_count++))
add_config "sap.max_retries" "$SAP_MAX_RETRIES" "SAP请求最大重试次数" && ((success_count++)) || ((fail_count++))
add_config "sap.page_size" "$SAP_PAGE_SIZE" "SAP查询分页大小" && ((success_count++)) || ((fail_count++))
add_config "sap.max_records" "$SAP_MAX_RECORDS" "SAP查询最大记录数" && ((success_count++)) || ((fail_count++))

echo ""
echo "完成: 成功 $success_count 个, 失败 $fail_count 个"

if [ $success_count -gt 0 ]; then
    echo ""
    echo "✅ SAP配置已添加到配置中心"
    echo "   请重启 sap-mcp-server 服务以使配置生效:"
    echo "   docker-compose restart sap-mcp-server"
fi
































