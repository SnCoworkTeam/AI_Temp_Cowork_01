# 修复工作流文件问题

## 问题诊断

工作流失败提示 "workflow file issue"，可能的原因：

1. **缺少必需的Secrets**
   - `SSH_PRIVATE_KEY` - SSH私钥
   - `SERVER_HOST` - 服务器地址
   - `SERVER_USER` - 服务器用户
   - `SERVER_URL` - 服务器URL

2. **环境配置问题**
   - GitHub环境（production/staging/development）未配置

3. **工作流语法问题**
   - YAML格式错误
   - 使用了不支持的语法

## 解决方案

### 步骤1: 检查Secrets配置

```powershell
# 检查已配置的secrets
gh secret list
```

确保以下secrets已配置：
- ✅ SSH_PRIVATE_KEY
- ✅ SERVER_HOST
- ✅ SERVER_USER
- ✅ SERVER_URL

### 步骤2: 配置环境（如果需要）

如果使用GitHub Environments，需要在仓库设置中配置：
1. 访问：`https://github.com/PMLiuyubin/enterprise-ai-platform/settings/environments`
2. 创建或配置以下环境：
   - `production`
   - `staging`
   - `development`

### 步骤3: 简化工作流（临时方案）

如果问题持续，可以先使用简化版本的工作流，移除蓝绿部署的复杂逻辑：

```yaml
# 简化版部署步骤
- name: Deploy to server
  env:
    SERVER_HOST: ${{ secrets.SERVER_HOST }}
    SERVER_USER: ${{ secrets.SERVER_USER }}
    DEPLOY_ENV: ${{ github.event.inputs.environment || 'production' }}
  run: |
    ssh $SERVER_USER@$SERVER_HOST << 'EOF'
      cd /opt/enterprise-ai-platform
      git pull origin main
      docker-compose up -d --build
      sleep 30
      curl -f http://localhost:8080/health || exit 1
    EOF
```

### 步骤4: 查看详细错误

在GitHub Web界面查看详细错误：
```
https://github.com/PMLiuyubin/enterprise-ai-platform/actions/runs/19900612059
```

## 快速修复命令

```powershell
# 1. 检查secrets
gh secret list

# 2. 如果缺少secrets，配置它们
gh secret set SERVER_HOST --body "43.143.139.197"
gh secret set SERVER_USER --body "ubuntu"
gh secret set SERVER_URL --body "http://43.143.139.197:8080"

# 3. 重新触发工作流
gh workflow run deploy.yml --field environment=staging
```

## 临时解决方案

如果问题无法快速解决，可以：

1. **使用简化的工作流** - 移除复杂功能，先确保基本部署工作
2. **手动部署** - 暂时使用SSH手动部署
3. **检查日志** - 在GitHub Web界面查看详细错误信息

---

**下一步**: 访问GitHub Actions页面查看详细错误信息，然后根据具体错误进行修复。





