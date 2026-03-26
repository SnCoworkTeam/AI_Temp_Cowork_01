# 防火墙配置指南

## 问题描述

如果在部署过程中遇到以下错误：
- `Docker Hub连接失败`
- `端口443无法访问`
- `镜像拉取超时`
- `Get "https://registry-1.docker.io/v2/": net/http: request canceled`

这通常是因为防火墙阻止了必要的端口（特别是443端口）。

## 解决方案

### 方法1: 自动配置（推荐）

```bash
# 在项目目录下运行
sudo bash scripts/deployment/configure-firewall.sh
```

这个脚本会自动检测你的防火墙类型（UFW、Firewalld或iptables）并配置必要的端口。

### 方法2: 手动配置

#### Ubuntu/Debian (UFW)

```bash
# 检查UFW状态
sudo ufw status

# 开放端口
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS (GitHub和Docker Hub需要)
sudo ufw allow 3000/tcp  # Web UI
sudo ufw allow 8001/tcp  # MCP Gateway
sudo ufw allow 8002/tcp  # Workflow Engine
sudo ufw allow 8003/tcp  # Auth Service
sudo ufw allow 8004/tcp  # Knowledge Base

# 启用防火墙（如果未启用）
sudo ufw enable

# 查看规则
sudo ufw status numbered
```

#### CentOS/RHEL (Firewalld)

```bash
# 检查firewalld状态
sudo systemctl status firewalld

# 开放端口
sudo firewall-cmd --permanent --add-port=22/tcp
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --permanent --add-port=8001/tcp
sudo firewall-cmd --permanent --add-port=8002/tcp
sudo firewall-cmd --permanent --add-port=8003/tcp
sudo firewall-cmd --permanent --add-port=8004/tcp

# 重新加载配置
sudo firewall-cmd --reload

# 查看规则
sudo firewall-cmd --list-ports
```

#### 其他系统 (iptables)

```bash
# 开放端口
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 3000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8001 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8002 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8003 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8004 -j ACCEPT

# 保存规则（根据系统类型）
# Ubuntu/Debian
sudo iptables-save > /etc/iptables/rules.v4

# CentOS/RHEL
sudo service iptables save
```

### 方法3: 云服务器安全组

如果使用云服务器（阿里云、腾讯云、AWS等），还需要在云控制台配置安全组规则：

1. **登录云控制台**
2. **找到安全组设置**
3. **添加入站规则**：
   - 端口: 22, 协议: TCP, 源: 0.0.0.0/0 (SSH)
   - 端口: 80, 协议: TCP, 源: 0.0.0.0/0 (HTTP)
   - 端口: 443, 协议: TCP, 源: 0.0.0.0/0 (HTTPS)
   - 端口: 3000, 协议: TCP, 源: 0.0.0.0/0 (Web UI)
   - 端口: 8001-8004, 协议: TCP, 源: 0.0.0.0/0 (Services)

## 验证

配置完成后，验证端口是否开放：

```bash
# 检查443端口（GitHub和Docker Hub）
timeout 3 bash -c "echo >/dev/tcp/github.com/443" && echo "✅ 443端口可访问"

# 检查Docker Hub连接
curl -s --connect-timeout 5 https://registry-1.docker.io/v2/ && echo "✅ Docker Hub可访问"
```

## 常见问题

### Q: 配置防火墙后仍然无法连接？

A: 检查以下几点：
1. 是否保存了防火墙规则（特别是iptables）
2. 云服务器安全组是否配置正确
3. 是否有其他防火墙软件（如fail2ban）
4. 网络提供商是否限制了端口

### Q: 如何临时关闭防火墙进行测试？

A: **不推荐**，但如果需要测试：

```bash
# UFW
sudo ufw disable

# Firewalld
sudo systemctl stop firewalld

# 测试后记得重新启用
sudo ufw enable
sudo systemctl start firewalld
```

### Q: 只想开放443端口用于Docker镜像拉取？

A: 可以只开放443端口：

```bash
# UFW
sudo ufw allow 443/tcp

# Firewalld
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

## 相关文档

- [部署脚本 README](README.md)
- [Git Token 配置](GIT_TOKEN_SETUP.md)
- [GitHub 连接检查](check-github-connection.sh)
