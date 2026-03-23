# Windows Docker Desktop 镜像加速器配置指南

## 方法1: 通过Docker Desktop GUI配置（推荐）

1. **打开Docker Desktop**
   - 右键点击系统托盘中的Docker图标
   - 选择 "Settings" 或"设置"

2. **进入Docker Engine配置**
   - 在左侧菜单找到 "Docker Engine"
   - 在右侧的JSON配置编辑器中添加或修改配置

3. **添加镜像加速器配置**
   ```json
   {
     "builder": {
       "gc": {
         "defaultKeepStorage": "20GB",
         "enabled": true
       }
     },
     "experimental": false,
     "registry-mirrors": [
       "https://docker.mirrors.ustc.edu.cn",
       "https://hub-mirror.c.163.com",
       "https://mirror.baidubce.com",
       "https://dockerhub.azk8s.cn"
     ]
   }
   ```

4. **应用并重启**
   - 点击 "Apply & Restart" 按钮
   - 等待Docker Desktop重启完成

## 方法2: 通过配置文件修改

Docker Desktop的配置文件位置：
- Windows: `%USERPROFILE%\.docker\daemon.json`

或者通过PowerShell直接配置：

```powershell
# 创建配置目录
$dockerConfigPath = "$env:USERPROFILE\.docker"
if (-not (Test-Path $dockerConfigPath)) {
    New-Item -ItemType Directory -Path $dockerConfigPath
}

# 配置镜像加速器
$daemonConfig = @{
    registry-mirrors = @(
        "https://docker.mirrors.ustc.edu.cn",
        "https://hub-mirror.c.163.com",
        "https://mirror.baidubce.com",
        "https://dockerhub.azk8s.cn"
    )
} | ConvertTo-Json -Depth 10

$daemonConfig | Out-File -FilePath "$dockerConfigPath\daemon.json" -Encoding UTF8

Write-Host "配置已保存，请重启Docker Desktop" -ForegroundColor Green
```

## 验证配置

配置完成后，运行以下命令验证：

```powershell
# 查看Docker信息
docker info | Select-String -Pattern "Registry"

# 测试拉取镜像
docker pull hello-world
```

## 国内常用镜像加速器

- 中科大镜像: `https://docker.mirrors.ustc.edu.cn`
- 网易镜像: `https://hub-mirror.c.163.com`
- 百度云镜像: `https://mirror.baidubce.com`
- Azure中国镜像: `https://dockerhub.azk8s.cn`
- 阿里云镜像: 需要登录阿里云获取专属加速地址

## 注意事项

1. 配置后需要重启Docker Desktop才能生效
2. 如果使用VPN，可能需要先关闭VPN再拉取镜像
3. 某些企业网络可能有防火墙限制，需要联系网络管理员

