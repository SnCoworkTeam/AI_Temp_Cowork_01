# Jenkins服务器检查报告

## 服务器信息

- **服务器地址**: 1.117.62.202
- **用户名**: ubuntu
- **SSH密钥**: `Jenkins.pem`
- **操作系统**: Ubuntu 24.04 LTS
- **内核版本**: 6.8.0-49-generic

## 系统资源

- **CPU**: 2核心
- **内存**: 1.6GB (可用1.3GB)
- **磁盘**: 50GB (已用6.2GB, 可用41GB)
- **交换空间**: 1.9GB

## 已安装的应用

### ✅ 已安装

1. **Docker 27.5.1**
   - 位置: `/usr/bin/docker`
   - 状态: 服务运行中
   - 相关文件:
     - `/usr/bin/docker` (40MB)
     - `/usr/bin/dockerd` (105MB)
     - `/usr/bin/docker-proxy` (2.3MB)
     - `/usr/bin/dockerd-rootless-setuptool.sh`
     - `/usr/bin/dockerd-rootless.sh`

2. **Docker Compose v2.32.4**
   - 已安装为Docker插件

3. **Git 2.43.0**
   - 位置: `/usr/bin/git`

4. **Python3**
   - 版本: 3.12.3
   - 位置: `/usr/bin/python3`

### ❌ 未安装

1. **Jenkins**
   - 状态: 未安装
   - 需要安装

2. **Java**
   - 状态: 未安装
   - Jenkins需要Java 11或17

## 网络配置

- **开放端口**: 22 (SSH)
- **需要开放**: 8080 (Jenkins)
- **公网IP**: 1.117.62.202

## 检查结论

✅ **服务器配置可以安装Jenkins**

- 系统资源充足（2核CPU，1.6GB内存，41GB可用磁盘）
- Docker已安装，可以用于部署
- Git已安装，可以拉取代码
- 只需要安装Java和Jenkins

## 安装步骤

### 1. 安装Jenkins

已创建安装脚本：`install-jenkins-on-server.sh`

执行命令：
```bash
# 方式1: 直接执行
ssh -i Jenkins.pem ubuntu@1.117.62.202 'bash /tmp/install-jenkins.sh'

# 方式2: 手动执行
ssh -i Jenkins.pem ubuntu@1.117.62.202
bash /tmp/install-jenkins.sh
```

安装脚本将：
1. 更新系统包
2. 安装Java 17
3. 安装Jenkins
4. 启动Jenkins服务
5. 配置防火墙
6. 显示初始密码和访问地址

### 2. 访问Jenkins

安装完成后，访问：
- **URL**: `http://1.117.62.202:8080`
- **初始密码**: 安装脚本会显示，或执行：
  ```bash
  sudo cat /var/lib/jenkins/secrets/initialAdminPassword
  ```

### 3. 配置Jenkins

1. 使用初始密码登录
2. 安装推荐插件
3. 创建管理员账户
4. 配置SSH密钥用于部署到43.143.139.197

### 4. 配置自动化部署

参考文档：`docs/Jenkins自动化部署配置指南.md`

主要步骤：
1. 安装Jenkins插件（SSH Pipeline Steps, SSH Agent Plugin等）
2. 配置SSH凭据（部署服务器密钥）
3. 创建Pipeline任务
4. 配置自动触发（GitHub Webhook或定时检查）

## 部署目标服务器

- **服务器地址**: 43.143.139.197
- **用户名**: ubuntu
- **项目目录**: `/opt/enterprise-ai-platform`
- **部署方式**: Docker Compose

## 下一步操作

1. ✅ 服务器检查完成
2. ⏳ 安装Jenkins（执行安装脚本）
3. ⏳ 配置Jenkins Web界面
4. ⏳ 配置SSH密钥和凭据
5. ⏳ 创建Pipeline任务
6. ⏳ 测试自动化部署

## 注意事项

1. **内存限制**: 服务器只有1.6GB内存，Jenkins和Docker会占用一定内存，建议：
   - 关闭不必要的服务
   - 限制Jenkins并发构建数量
   - 定期清理Docker镜像和容器

2. **防火墙**: 确保8080端口已开放，可以通过以下命令检查：
   ```bash
   sudo ufw status
   sudo ufw allow 8080/tcp
   ```

3. **SSH密钥**: 需要将部署服务器的SSH密钥配置到Jenkins，以便自动部署

4. **备份**: 建议定期备份Jenkins配置：
   ```bash
   sudo tar -czf jenkins-backup-$(date +%Y%m%d).tar.gz /var/lib/jenkins
   ```

## 相关文件

- `check-jenkins-server.sh` - 服务器检查脚本
- `install-jenkins-on-server.sh` - Jenkins安装脚本
- `docs/Jenkins自动化部署配置指南.md` - 完整配置指南
- `Jenkinsfile` - Pipeline配置示例（如果已创建）


