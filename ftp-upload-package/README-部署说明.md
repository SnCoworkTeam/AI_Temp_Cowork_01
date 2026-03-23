# OpenCode 服务器部署包

## 📦 包含文件

- `enterprise-ai-opencode-local-web.tar` - OpenCode Docker 镜像（构建完成后生成）
- `docker-compose.opencode.local-web.yml` - Docker Compose 配置文件
- `deploy-on-server.sh` - 服务器端自动部署脚本
- `diagnose-opencode.sh` - 问题诊断脚本
- `README-部署说明.md` - 本文件

## 🚀 部署步骤

### 1. 上传文件到服务器

通过 FTP 将整个文件夹上传到服务器，例如：

```
/tmp/opencode-deploy/
```

### 2. 在服务器上执行部署

```bash
# SSH 登录服务器
ssh root@服务器IP

# 进入上传目录
cd /tmp/opencode-deploy

# 给脚本添加执行权限
chmod +x deploy-on-server.sh diagnose-opencode.sh

# 执行部署
bash deploy-on-server.sh
```

### 3. 配置密码（首次部署）

如果是首次部署，脚本会创建 `.env` 示例文件，需要编辑密码：

```bash
cd /opt/enterprise-ai-platform/opencode-server-export
vi .env
```

修改这一行：
```
OPENCODE_SERVER_PASSWORD=请修改为强密码
```

然后重启容器：
```bash
docker restart enterprise-ai-opencode
```

### 4. 验证部署

```bash
# 测试端点（应返回 "local-web-ok"）
curl http://127.0.0.1:4096/local-web-root

# 测试根路径（应返回 200）
curl -I http://127.0.0.1:4096/
```

### 5. 访问 OpenCode

在浏览器访问：
```
http://服务器IP:4096
```

使用配置的用户名和密码登录。

## 🔧 问题排查

如果部署后无法访问，运行诊断脚本：

```bash
cd /opt/enterprise-ai-platform/opencode-server-export
bash diagnose-opencode.sh > diagnose-result.txt 2>&1
cat diagnose-result.txt
```

查看容器日志：
```bash
docker logs enterprise-ai-opencode
```

## 📋 常用命令

```bash
# 查看容器状态
docker ps | grep opencode

# 查看实时日志
docker logs -f enterprise-ai-opencode

# 重启容器
docker restart enterprise-ai-opencode

# 停止容器
docker stop enterprise-ai-opencode

# 启动容器
docker start enterprise-ai-opencode

# 完全重新部署
cd /opt/enterprise-ai-platform/opencode-server-export
docker compose -f docker-compose.opencode.local-web.yml --env-file .env up -d --force-recreate
```

## ⚠️ 注意事项

1. **端口 4096**：确保服务器防火墙开放 4096 端口
2. **Docker 网络**：脚本会自动创建 `enterprise-ai-platform_enterprise-ai-network` 网络
3. **工作目录**：默认锁定在 `/opt/enterprise-ai-platform`，仅对该项目操作
4. **Docker Socket**：容器可以访问宿主机 Docker，用于管理其他服务

## 🆘 快速修复

### 问题1：容器启动但无法访问（返回 000）

**可能原因**：早处理中间件未生效（旧镜像）

**解决方案**：
```bash
# 1. 确认构建标记
docker run --rm enterprise-ai-opencode-local-web:latest cat /app-web/build.txt
# 应该显示：local-web-YYYYMMDD-HHMM-verified

# 2. 如果没有 "verified"，重新上传镜像并部署
```

### 问题2：带认证也超时

**可能原因**：容器内服务未真正启动

**解决方案**：
```bash
# 查看日志找出错误
docker logs enterprise-ai-opencode

# 检查容器状态
docker inspect -f '{{.State.Status}}' enterprise-ai-opencode

# 尝试进入容器手动启动
docker exec -it enterprise-ai-opencode bash
opencode serve --hostname 0.0.0.0 --port 4096
```

### 问题3：健康检查失败

**可能原因**：认证配置问题或服务未启动

**解决方案**：
```bash
# 测试健康检查端点
curl -u opencode:密码 http://127.0.0.1:4096/global/health
# 应返回：{"healthy":true,"version":"..."}

# 如果返回 401，检查 .env 文件密码配置
# 如果超时，服务未启动，查看日志
```

## 📞 获取帮助

如果遇到问题，收集以下信息：

1. 诊断脚本输出：`diagnose-result.txt`
2. 容器日志：`docker logs enterprise-ai-opencode`
3. 构建标记：`docker run --rm enterprise-ai-opencode-local-web:latest cat /app-web/build.txt`
4. 环境配置：`.env` 文件内容（密码可脱敏）

## 🎯 本次修复说明

本次构建修复了**根路径超时**问题：

**问题**：早处理中间件代码未被编译到二进制中，导致根路径请求被 basicAuth 阻塞挂起。

**修复**：
1. 在 Dockerfile 中强制清理所有构建缓存
2. 添加构建后验证：检查编译后的二进制包含 `local-web-ok` 字符串
3. 只有验证通过的镜像才会被标记为 `verified`

**验证方法**：
- 构建标记包含 `verified`
- `/local-web-root` **不需要认证**直接返回 `local-web-ok`
- 根路径 `/` **不需要认证**直接返回 HTML

这样 OpenCode 的 Web 界面就能正常访问了，不会再被 basicAuth 卡住。
