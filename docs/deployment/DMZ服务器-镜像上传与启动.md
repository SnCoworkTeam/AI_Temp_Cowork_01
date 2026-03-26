# DMZ 内网服务器：镜像导出、上传与启动

将本机已构建的 **zhgj 19 个服务** 镜像导出，通过 SCP 上传到内网服务器（10.24.20.56），在服务器上**直接加载并启动，无需重新构建**。

---

## 一、前提与安全说明

- **本机**需能访问内网服务器（如 10.24.20.56），且已安装 OpenSSH（含 `ssh`、`scp`）。
- **请勿在脚本或代码中写入服务器密码**；SCP/SSH 时在提示下输入密码，或配置 SSH 公钥免密。
- 若通过跳板机（如 https://10.24.20.200）登录到 10.24.20.56，请在本机或跳板机上执行下述命令（以实际能连到 10.24.20.56 的那台机器为准）。

---

## 二、本机操作（导出并上传）

### 方式一：一键脚本（推荐）

在**能访问 10.24.20.56** 的本机、项目根目录执行：

```powershell
cd e:\enterprise-ai-platform
.\scripts\deployment\zhgj-export-and-upload-to-dmz.ps1
```

- 会先导出 zhgj 19 个服务镜像到 `docker-images-export\`，再通过 SCP 上传到服务器。
- 执行过程中会提示输入**服务器密码**，输入后回车即可。
- 若已导出过、只需上传，可加 `-SkipExport`：
  ```powershell
  .\scripts\deployment\zhgj-export-and-upload-to-dmz.ps1 -SkipExport
  ```

默认上传到服务器路径：`/opt/enterprise-ai-platform`，用户：`lijingwei`，主机：`10.24.20.56`。  
若需修改，可传参，例如：

```powershell
.\scripts\deployment\zhgj-export-and-upload-to-dmz.ps1 -Server "10.24.20.56" -User "lijingwei" -RemotePath "/home/lijingwei/zhgj"
```

### 方式二：分步执行

**1. 仅导出 19 个服务镜像**

```powershell
cd e:\enterprise-ai-platform
$env:ZHGJ_19="1"; .\scripts\export-docker-images.ps1
```

**2. SCP 上传到服务器（会提示输入密码）**

```powershell
# 上传整个导出目录到服务器目录 /opt/enterprise-ai-platform/
scp -r docker-images-export lijingwei@10.24.20.56:/opt/enterprise-ai-platform/
```

上传后，若保留文件夹名，服务器路径为：`/opt/enterprise-ai-platform/docker-images-export/`；  
若将 **docker-images-export 内的所有文件** 拷到 `/opt/enterprise-ai-platform/` 下，则直接在 `/opt/enterprise-ai-platform/` 执行下面命令。

---

## 三、服务器操作（部署目录 /opt/enterprise-ai-platform）

SSH 登录到 10.24.20.56 后执行：

```bash
# 进入部署目录（导出内容直接放在此目录时）
cd /opt/enterprise-ai-platform

# 若上传的是整个 docker-images-export 文件夹，则进入子目录：
# cd /opt/enterprise-ai-platform/docker-images-export

# 加载所有导出的镜像
for f in *.tar; do [ -f "$f" ] && docker load -i "$f"; done

# 启动 19 个服务（不拉取、不构建）
docker compose up -d --no-build

# 查看状态
docker compose ps
```

或使用脚本（在部署目录下）：
```bash
chmod +x load-and-run.sh && ./load-and-run.sh
```

若服务器为 **Windows**，在对应目录下用 PowerShell：

```powershell
cd E:\opt\enterprise-ai-platform
Get-ChildItem *.tar | ForEach-Object { docker load -i $_.FullName }
docker compose up -d --no-build
```

---

## 四、连通性自检（在本机执行）

若不确定本机能否 SCP 到服务器，可先测试：

```powershell
# 测试 SSH 是否可达（会提示输入密码）
ssh -o ConnectTimeout=10 lijingwei@10.24.20.56 "echo OK"
```

若提示“连接超时”或“无法访问”，说明本机网络到 10.24.20.56 不可达，需要：

- 在能访问该内网的机器上执行导出与 SCP，或  
- 通过跳板机/代理先登录到可访问 10.24.20.56 的机器，再在该机器上执行 SCP。

---

## 五、小结

| 步骤       | 本机（能访问 10.24.20.56） | 服务器 10.24.20.56 |
|------------|----------------------------|---------------------|
| 导出镜像   | `$env:ZHGJ_19="1"; .\scripts\export-docker-images.ps1` | - |
| 上传       | `scp -r docker-images-export lijingwei@10.24.20.56:/opt/enterprise-ai-platform/` | - |
| 加载并启动 | - | `cd /opt/enterprise-ai-platform` → `for f in *.tar; do docker load -i "$f"; done` → `docker compose up -d --no-build` |

**服务器上不需要重新构建**：镜像已在本地构建并导出为 `.tar`，在服务器上仅需 `docker load` 和 `docker compose up -d --no-build` 即可。

**密码**：请勿写在脚本或文档中；SCP/SSH 时在提示下输入，或配置 SSH 公钥登录。
