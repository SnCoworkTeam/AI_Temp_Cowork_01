#!/bin/bash
# 配置Nginx反向代理 for SonarQube
# 可选配置，用于通过域名访问SonarQube

set -e

SONARQUBE_PORT="9000"
NGINX_CONF="/etc/nginx/sites-available/sonarqube"
NGINX_ENABLED="/etc/nginx/sites-enabled/sonarqube"

echo "=========================================="
echo "配置Nginx反向代理 for SonarQube"
echo "=========================================="
echo ""

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "错误: 请使用sudo运行此脚本"
    exit 1
fi

# 安装Nginx（如果未安装）
if ! command -v nginx &> /dev/null; then
    echo "[1/4] 安装Nginx..."
    apt-get update
    apt-get install -y nginx
    echo "Nginx 已安装"
else
    echo "[1/4] Nginx 已安装"
fi

# 创建Nginx配置
echo "[2/4] 创建Nginx配置..."
cat > $NGINX_CONF <<'EOF'
# SonarQube Nginx配置
# 请将 sonarqube.yourdomain.com 替换为您的域名

upstream sonarqube {
    server 127.0.0.1:9000;
    keepalive 64;
}

server {
    listen 80;
    server_name sonarqube.yourdomain.com;  # 修改为您的域名或IP

    # 日志
    access_log /var/log/nginx/sonarqube_access.log;
    error_log /var/log/nginx/sonarqube_error.log;

    # 客户端最大上传大小
    client_max_body_size 100M;

    location / {
        proxy_pass http://sonarqube;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # 缓冲设置
        proxy_buffering off;
    }
}
EOF

# 启用配置
if [ -L $NGINX_ENABLED ]; then
    rm $NGINX_ENABLED
fi
ln -s $NGINX_CONF $NGINX_ENABLED

echo "Nginx 配置已创建"

# 测试配置
echo "[3/4] 测试Nginx配置..."
nginx -t

# 重启Nginx
echo "[4/4] 重启Nginx..."
systemctl restart nginx
systemctl enable nginx

echo ""
echo "=========================================="
echo "Nginx配置完成！"
echo "=========================================="
echo ""
echo "配置文件: $NGINX_CONF"
echo ""
echo "重要提示:"
echo "1. 请编辑 $NGINX_CONF 将 'sonarqube.yourdomain.com' 替换为您的域名或IP"
echo "2. 如果使用域名，请确保DNS已正确配置"
echo "3. 建议配置SSL证书（Let's Encrypt）"
echo "4. 配置完成后运行: sudo nginx -t && sudo systemctl reload nginx"
echo ""

