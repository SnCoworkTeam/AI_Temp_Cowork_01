# Jenkins快速修复Git认证问题

## 问题

```
无法连接仓库：Command "git ls-remote -h -- https://github.com/PMLiuyubin/enterprise-ai-platform.git HEAD" returned status code 128:
remote: Invalid username or token. Password authentication is not supported for Git operations.
fatal: Authentication failed for 'https://github.com/PMLiuyubin/enterprise-ai-platform.git/'
```

## 快速解决步骤（5分钟）

### 步骤1: 创建GitHub Personal Access Token（2分钟）

1. 访问: https://github.com/settings/tokens
2. 点击: **Generate new token** → **Generate new token (classic)**
3. 配置:
   - **Note**: `Jenkins CI/CD`
   - **Expiration**: `90 days`（或更长）
   - **Scopes**: ✅ 勾选 `repo`
4. 点击: **Generate token**
5. **立即复制Token**（只显示一次！）

### 步骤2: 在Jenkins中添加凭据（2分钟）

1. 访问Jenkins: `http://1.117.62.202:8080`
2. 进入: **Manage Jenkins** → **Manage Credentials**
3. 点击: **(global)** → **Add Credentials**
4. 填写:
   ```
   Kind: Username with password
   Scope: Global
   Username: PMLiuyubin（你的GitHub用户名）
   Password: [粘贴刚才复制的Token]
   ID: github-credentials
   Description: GitHub Personal Access Token
   ```
5. 点击: **OK**

### 步骤3: 更新Pipeline配置（1分钟）

1. 进入Pipeline任务: `enterprise-ai-platform-deploy`
2. 点击: **Configure**
3. 在 **Pipeline** 标签中:
   - **Repository URL**: `https://github.com/PMLiuyubin/enterprise-ai-platform.git`
   - **Credentials**: 选择 `github-credentials`
4. 点击: **Save**

### 步骤4: 测试

1. 点击: **Build Now**
2. 查看构建日志，应该能成功检出代码

## 验证

如果配置成功，构建日志中会显示：
```
📥 检出代码...
> git rev-parse --is-inside-work-tree # timeout=10
Fetching changes from the remote Git repository
> git config remote.origin.url https://github.com/PMLiuyubin/enterprise-ai-platform.git # timeout=10
Fetching upstream changes from https://github.com/PMLiuyubin/enterprise-ai-platform.git
> git --version # timeout=10
> git fetch --tags --force --progress -- https://github.com/PMLiuyubin/enterprise-ai-platform.git +refs/heads/*:refs/remotes/origin/* # timeout=10
```

## 如果仍然失败

1. **检查Token权限**: 确保Token有 `repo` 权限
2. **检查凭据ID**: 确保Pipeline中使用的凭据ID是 `github-credentials`
3. **检查仓库访问**: 确保Token有权限访问该仓库
4. **清除缓存**:
   ```bash
   ssh -i Jenkins.pem ubuntu@1.117.62.202
   sudo rm -rf /var/lib/jenkins/.git*
   ```

## 替代方案：使用SSH密钥

如果不想使用Token，可以使用SSH密钥：

1. **生成SSH密钥**:
   ```bash
   ssh -i Jenkins.pem ubuntu@1.117.62.202
   sudo -u jenkins ssh-keygen -t ed25519 -C "jenkins@1.117.62.202" -f /var/lib/jenkins/.ssh/id_ed25519 -N ""
   sudo cat /var/lib/jenkins/.ssh/id_ed25519.pub
   ```

2. **添加到GitHub**: https://github.com/settings/keys

3. **在Jenkins中配置SSH凭据**

4. **更新Repository URL**: 改为 `git@github.com:PMLiuyubin/enterprise-ai-platform.git`

## 总结

✅ **推荐使用Personal Access Token**，配置简单快速
✅ Token需要 `repo` 权限
✅ 在Jenkins Pipeline配置中选择正确的凭据
✅ 如果仓库是公开的，可能不需要凭据（但建议配置）


