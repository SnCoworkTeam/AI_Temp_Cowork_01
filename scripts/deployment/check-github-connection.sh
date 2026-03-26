#!/bin/bash
# 检查服务器到GitHub的连接性
# 使用方法: bash check-github-connection.sh

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "GitHub连接性检查"
echo "==========================================${NC}"
echo ""

# 检查项计数
PASSED=0
FAILED=0

# 1. 检查DNS解析
echo -e "${BLUE}[1/5] 检查DNS解析...${NC}"
if host github.com &> /dev/null || nslookup github.com &> /dev/null || getent hosts github.com &> /dev/null; then
    echo -e "${GREEN}✅ DNS解析正常${NC}"
    GITHUB_IP=$(getent hosts github.com | awk '{print $1}' | head -1)
    echo "   GitHub IP: $GITHUB_IP"
    ((PASSED++))
else
    echo -e "${RED}❌ DNS解析失败${NC}"
    echo "   请检查DNS配置或网络连接"
    ((FAILED++))
fi
echo ""

# 2. 检查HTTP连接
echo -e "${BLUE}[2/5] 检查HTTPS连接...${NC}"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 15 https://github.com 2>&1)
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "301" ] || [ "$HTTP_STATUS" = "302" ]; then
    echo -e "${GREEN}✅ HTTPS连接正常 (状态码: $HTTP_STATUS)${NC}"
    ((PASSED++))
elif [ "$HTTP_STATUS" = "000" ]; then
    echo -e "${RED}❌ HTTPS连接失败 (状态码: 000 - 连接超时或无法连接)${NC}"
    echo "   可能原因:"
    echo "   - 端口443被防火墙阻止"
    echo "   - 网络连接问题"
    echo "   - 需要配置代理"
    echo "   建议: 尝试使用SSH方式或GitHub镜像"
    ((FAILED++))
else
    echo -e "${YELLOW}⚠️  HTTPS连接异常 (状态码: $HTTP_STATUS)${NC}"
    ((FAILED++))
fi
echo ""

# 3. 检查Git协议连接
echo -e "${BLUE}[3/5] 检查Git协议连接...${NC}"
# 先测试公开仓库
if timeout 10 git ls-remote https://github.com/github/gitignore &> /dev/null; then
    echo -e "${GREEN}✅ Git协议连接正常（公开仓库测试）${NC}"
    ((PASSED++))
    
    # 再测试目标仓库（可能需要认证）
    echo "测试目标仓库..."
    if timeout 10 git ls-remote https://github.com/PMLiuyubin/enterprise-ai-platform.git &> /dev/null; then
        echo -e "${GREEN}✅ 目标仓库可访问${NC}"
    else
        echo -e "${YELLOW}⚠️  目标仓库访问失败（可能需要认证或为私有仓库）${NC}"
        echo "   建议: 使用Token进行认证"
    fi
else
    echo -e "${RED}❌ Git协议连接失败${NC}"
    echo "   可能原因:"
    echo "   - HTTPS端口443无法访问"
    echo "   - 网络连接问题"
    echo "   建议: 尝试使用SSH方式或配置代理"
    ((FAILED++))
fi
echo ""

# 4. 检查API连接
echo -e "${BLUE}[4/5] 检查GitHub API连接...${NC}"
API_RESPONSE=$(curl -s --connect-timeout 5 --max-time 10 https://api.github.com 2>&1)
if echo "$API_RESPONSE" | grep -q "current_user_url" || echo "$API_RESPONSE" | grep -q "rate_limit_url"; then
    echo -e "${GREEN}✅ GitHub API连接正常${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ GitHub API连接失败${NC}"
    echo "   响应: ${API_RESPONSE:0:100}..."
    ((FAILED++))
fi
echo ""

# 5. 检查端口连通性
echo -e "${BLUE}[5/5] 检查端口连通性...${NC}"
if command -v nc &> /dev/null || command -v nmap &> /dev/null; then
    if nc -z -w 3 github.com 443 2>/dev/null || timeout 3 bash -c "echo >/dev/tcp/github.com/443" 2>/dev/null; then
        echo -e "${GREEN}✅ 端口443 (HTTPS) 可访问${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ 端口443无法访问${NC}"
        ((FAILED++))
    fi
    
    if nc -z -w 3 github.com 22 2>/dev/null || timeout 3 bash -c "echo >/dev/tcp/github.com/22" 2>/dev/null; then
        echo -e "${GREEN}✅ 端口22 (SSH) 可访问${NC}"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠️  端口22无法访问（如果使用HTTPS则不影响）${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  未安装nc或nmap，跳过端口检查${NC}"
    echo "   安装: sudo apt-get install netcat-openbsd 或 sudo yum install nc"
fi
echo ""

# 6. 检查代理设置（如果有）
echo -e "${BLUE}[6/6] 检查代理设置...${NC}"
if [ -n "$HTTP_PROXY" ] || [ -n "$HTTPS_PROXY" ]; then
    echo "检测到代理设置:"
    [ -n "$HTTP_PROXY" ] && echo "  HTTP_PROXY: $HTTP_PROXY"
    [ -n "$HTTPS_PROXY" ] && echo "  HTTPS_PROXY: $HTTPS_PROXY"
    echo -e "${YELLOW}⚠️  如果连接失败，请检查代理配置${NC}"
else
    echo "未检测到代理设置"
fi
echo ""

# 总结
echo -e "${BLUE}=========================================="
echo "检查结果汇总"
echo "==========================================${NC}"
echo -e "${GREEN}通过: $PASSED${NC}"
echo -e "${RED}失败: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 所有检查通过，服务器可以正常连接GitHub！${NC}"
    exit 0
else
    echo -e "${RED}❌ 部分检查失败，请检查网络连接${NC}"
    echo ""
    echo "故障排查建议:"
    echo "1. 检查网络连接: ping github.com"
    echo "2. 检查防火墙设置"
    echo "3. 检查是否需要配置代理"
    echo "4. 检查DNS配置: cat /etc/resolv.conf"
    echo "5. 尝试使用GitHub镜像（如果在中国）"
    exit 1
fi

