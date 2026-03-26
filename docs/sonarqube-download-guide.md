# SonarQube 10.8 LTS 手动下载和升级指南

## 下载地址

### 官方下载页面（推荐）
访问 SonarQube 官方下载页面：
**https://www.sonarsource.com/products/sonarqube/downloads/**

选择：
- **版本**: SonarQube 10.8 LTS (Community Edition)
- **完整版本号**: 10.8.1.93247

### 直接下载链接（如果可用）

**Community Edition (免费版)**:
```
https://binaries.sonarsource.com/Distribution/sonarqube/sonarqube-10.8.1.93247.zip
```

**注意**: 如果直接链接无法访问，请从官方下载页面下载。

## 下载步骤

1. **访问下载页面**
   - 打开浏览器，访问：https://www.sonarsource.com/products/sonarqube/downloads/
   - 找到 "SonarQube 10.8 LTS" 或 "10.8.1.93247" 版本

2. **选择版本**
   - 选择 **Community Edition** (免费版)
   - 下载 ZIP 格式文件

3. **保存文件**
   - 文件名应为：`sonarqube-10.8.1.93247.zip`
   - 文件大小约：400-500 MB

## 上传到服务器

### 使用 SCP 上传

在本地 PowerShell 中执行：

```powershell
# 上传到服务器
scp -i E:\enterprise-ai-platform\SonarQube1.pem `
    sonarqube-10.8.1.93247.zip `
    ubuntu@124.220.181.231:/tmp/
```

### 使用 WinSCP 或其他工具

1. 使用 WinSCP、FileZilla 等工具
2. 连接到服务器：`124.220.181.231`
3. 用户名：`ubuntu`
4. 使用密钥文件：`E:\enterprise-ai-platform\SonarQube1.pem`
5. 上传文件到：`/tmp/sonarqube-10.8.1.93247.zip`

## 执行升级

上传完成后，执行升级脚本：

```powershell
# SSH连接到服务器
ssh -i E:\enterprise-ai-platform\SonarQube1.pem ubuntu@124.220.181.231

# 执行升级
sudo bash /tmp/upgrade-10.8.sh
```

或者直接执行：

```powershell
ssh -i E:\enterprise-ai-platform\SonarQube1.pem ubuntu@124.220.181.231 "sudo bash /tmp/upgrade-10.8.sh"
```

## 验证升级

升级完成后，检查版本：

```powershell
ssh -i E:\enterprise-ai-platform\SonarQube1.pem ubuntu@124.220.181.231 "curl -s http://localhost:9000/api/system/status"
```

应该显示版本为 `10.8.1.93247`。

## 备用下载源

如果官方下载页面无法访问，可以尝试：

1. **GitHub Releases** (如果可用)
   - https://github.com/SonarSource/sonarqube/releases

2. **镜像站点**
   - 某些地区可能有镜像站点

3. **使用代理**
   - 如果网络受限，可以使用代理下载

## 文件完整性验证

下载后可以验证文件：

```powershell
# 检查文件大小（应该约400-500MB）
Get-Item sonarqube-10.8.1.93247.zip | Select-Object Length

# 检查是否为有效的ZIP文件
Expand-Archive -Path sonarqube-10.8.1.93247.zip -DestinationPath test -Force
Remove-Item -Recurse -Force test
```

## 注意事项

1. **文件大小**: 确保下载的文件大小合理（约400-500MB），如果只有几KB说明下载失败
2. **网络稳定**: 上传大文件时确保网络连接稳定
3. **磁盘空间**: 确保服务器有足够空间（至少2GB可用空间）
4. **备份**: 虽然您选择不备份，但建议至少知道如何回滚

## 快速命令总结

```powershell
# 1. 上传文件（在本地执行）
scp -i E:\enterprise-ai-platform\SonarQube1.pem sonarqube-10.8.1.93247.zip ubuntu@124.220.181.231:/tmp/

# 2. 执行升级（在本地执行）
ssh -i E:\enterprise-ai-platform\SonarQube1.pem ubuntu@124.220.181.231 "sudo bash /tmp/upgrade-10.8.sh"

# 3. 验证升级（在本地执行）
ssh -i E:\enterprise-ai-platform\SonarQube1.pem ubuntu@124.220.181.231 "curl -s http://localhost:9000/api/system/status"
```

