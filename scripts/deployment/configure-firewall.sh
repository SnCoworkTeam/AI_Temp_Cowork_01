#!/bin/bash
# 配置防火墙，开放必要端口
# 使用方法: sudo bash configure-firewall.sh

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "防火墙配置脚本"
echo "==========================================${NC}"
echo ""

# 检查是否为root或有sudo权限
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo -e "${RED}❌ 需要root权限或sudo权限${NC}"
    exit 1
fi

# 需要开放的端口
PORTS=(
    "22:SSH"
    "80:HTTP"
    "443:HTTPS"
    "8001:MCP Gateway"
    "8002:Workflow Engine"
    "8003:Auth Service"
    "8004:Knowledge Base"
    "3000:Web UI"
)

# 检测防火墙类型并配置
configure_ufw() {
    echo -e "${BLUE}检测到UFW防火墙，配置中...${NC}"
    
    # 检查UFW状态
    if sudo ufw status | grep -q "Status: active"; then
        echo "UFW已启用"
    else
        echo "启用UFW..."
        sudo ufw --force enable
    fi
    
    # 开放端口
    for port_info in "${PORTS[@]}"; do
        port=$(echo $port_info | cut -d: -f1)
        name=$(echo $port_info | cut -d: -f2)
        
        if sudo ufw status | grep -q "${port}/tcp"; then
            echo -e "${GREEN}✅ 端口 $port ($name) 已开放${NC}"
        else
            echo "开放端口 $port ($name)..."
            sudo ufw allow ${port}/tcp
            echo -e "${GREEN}✅ 端口 $port 已开放${NC}"
        fi
    done
    
    # 显示状态
    echo ""
    echo "当前防火墙规则:"
    sudo ufw status numbered
}

configure_firewalld() {
    echo -e "${BLUE}检测到Firewalld防火墙，配置中...${NC}"
    
    # 检查firewalld状态
    if sudo systemctl is-active --quiet firewalld; then
        echo "Firewalld运行中"
    else
        echo "启动Firewalld..."
        sudo systemctl start firewalld
        sudo systemctl enable firewalld
    fi
    
    # 开放端口
    for port_info in "${PORTS[@]}"; do
        port=$(echo $port_info | cut -d: -f1)
        name=$(echo $port_info | cut -d: -f2)
        
        if sudo firewall-cmd --list-ports | grep -q "${port}/tcp"; then
            echo -e "${GREEN}✅ 端口 $port ($name) 已开放${NC}"
        else
            echo "开放端口 $port ($name)..."
            sudo firewall-cmd --permanent --add-port=${port}/tcp
            echo -e "${GREEN}✅ 端口 $port 已开放${NC}"
        fi
    done
    
    # 重新加载配置
    sudo firewall-cmd --reload
    
    # 显示状态
    echo ""
    echo "当前防火墙规则:"
    sudo firewall-cmd --list-ports
}

configure_iptables() {
    echo -e "${BLUE}检测到iptables，配置中...${NC}"
    
    # 开放端口
    for port_info in "${PORTS[@]}"; do
        port=$(echo $port_info | cut -d: -f1)
        name=$(echo $port_info | cut -d: -f2)
        
        # 检查规则是否存在
        if sudo iptables -C INPUT -p tcp --dport $port -j ACCEPT 2>/dev/null; then
            echo -e "${GREEN}✅ 端口 $port ($name) 规则已存在${NC}"
        else
            echo "添加端口 $port ($name) 规则..."
            sudo iptables -A INPUT -p tcp --dport $port -j ACCEPT
            echo -e "${GREEN}✅ 端口 $port 规则已添加${NC}"
        fi
    done
    
    # 保存规则（根据系统类型）
    if command -v iptables-save &> /dev/null; then
        if [ -f /etc/redhat-release ]; then
            sudo service iptables save 2>/dev/null || true
        else
            sudo iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
        fi
    fi
    
    echo ""
    echo "当前iptables规则:"
    sudo iptables -L INPUT -n --line-numbers | grep -E "tcp|udp" | head -20
}

# 检测防火墙类型
detect_firewall() {
    if command -v ufw &> /dev/null; then
        configure_ufw
    elif command -v firewall-cmd &> /dev/null; then
        configure_firewalld
    elif command -v iptables &> /dev/null; then
        configure_iptables
    else
        echo -e "${YELLOW}⚠️  未检测到防火墙工具${NC}"
        echo "可能原因:"
        echo "  - 未安装防火墙"
        echo "  - 使用云服务商的安全组"
        echo ""
        echo "如果使用云服务器（如阿里云、腾讯云），需要在云控制台配置安全组规则"
        exit 1
    fi
}

# 主函数
main() {
    echo "检测防火墙类型..."
    detect_firewall
    
    echo ""
    echo -e "${GREEN}=========================================="
    echo "✅ 防火墙配置完成"
    echo "==========================================${NC}"
    echo ""
    echo "已开放的端口:"
    for port_info in "${PORTS[@]}"; do
        port=$(echo $port_info | cut -d: -f1)
        name=$(echo $port_info | cut -d: -f2)
        echo "  - 端口 $port: $name"
    done
    echo ""
    echo -e "${YELLOW}⚠️  如果使用云服务器，还需要在云控制台配置安全组规则${NC}"
}

main
