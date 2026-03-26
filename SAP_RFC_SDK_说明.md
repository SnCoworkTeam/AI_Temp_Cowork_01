# SAP RFC SDK 和 pyrfc 关系说明

## 📦 你提供的包是什么？

**`nwrfc750P_18-70002752.zip`** = **SAP NetWeaver RFC SDK 7.50.18**

这是 SAP 官方提供的**底层 C/C++ 库**，用于与 SAP 系统进行 RFC（Remote Function Call）通信。

### 包内容结构：
```
nwrfcsdk/
├── lib/              # 核心库文件
│   ├── libsapnwrfc.so    # Linux 共享库（你的是 Linux 版本）
│   └── ...
├── include/          # C/C++ 头文件
│   ├── sapnwrfc.h
│   └── ...
├── bin/              # 命令行工具
└── doc/              # 文档
```

## 🐍 pyrfc 是什么？

**`pyrfc`** = **Python 对 NWRFC SDK 的绑定（Python Wrapper）**

- 让 Python 代码可以调用 SAP RFC 函数
- **必须依赖 NWRFC SDK** 才能工作
- 提供 Python 接口，底层调用 SDK 的 C 库

## 🔗 两者的关系

```
你的 Python 代码
    ↓ (import pyrfc)
pyrfc (Python 绑定层)
    ↓ (调用 C API)
SAP NWRFC SDK (C/C++ 库)
    ↓ (RFC 协议)
SAP ERP 系统
```

**关键点**：
- `pyrfc` **不能独立工作**，必须安装 NWRFC SDK
- 安装 `pyrfc` 时，需要先设置 `SAPNWRFC_HOME` 环境变量指向 SDK 目录
- SDK 的**平台版本**必须匹配你的操作系统（Linux/Windows）

## ⚠️ 当前问题

你提供的 `nwrfc750P_18-70002752.zip` 是 **Linux 版本**（包含 `.so` 文件），而你在 **Windows 上测试**，所以无法直接使用。

### 验证方法：
```powershell
# 查看 SDK 库文件类型
cd E:\nwrfcsdk\nwrfcsdk\lib
Get-ChildItem *.so  # 看到 .so 文件 = Linux 版本
```

## ✅ 解决方案

### 方案 1：在 Linux 服务器上使用（推荐）⭐

这个 Linux 版本的 SDK **正好适合服务器上的 Docker 容器**！

**步骤**：
1. 将 SDK 上传到服务器 `/opt/nwrfcsdk`
2. 在 `docker-compose.yml` 中挂载 SDK 到 `mcp-gateway` 容器
3. 在容器内安装 `pyrfc`（会自动使用 SDK）
4. 配置 SAP 连接参数（环境变量）

**优势**：
- ✅ 你的 SDK 包可以直接使用
- ✅ 服务器环境更稳定
- ✅ 代码已经准备好了（`mcp-gateway/src/tools/sap_erp_table_tool.py`）

### 方案 2：获取 Windows 版本的 SDK（仅用于本地测试）

如果你需要在 Windows 上本地测试，需要：
1. 从 SAP Support Portal 下载 **Windows 版本的 NWRFC SDK**
2. 解压到本地（如 `C:\nwrfcsdk`）
3. 设置环境变量：
   ```powershell
   $env:SAPNWRFC_HOME = "C:\nwrfcsdk"
   $env:PATH = "C:\nwrfcsdk\lib;$env:PATH"
   ```
4. 安装 `pyrfc`：
   ```powershell
   pip install pyrfc
   ```

**注意**：Windows 版本的 SDK 需要 SAP S-user 账号从官方下载。

## 📥 pyrfc 从哪里下载？

### 方式 1：从 PyPI 安装（推荐）
```bash
pip install pyrfc
```

**前提**：
- 必须先安装 NWRFC SDK
- 设置 `SAPNWRFC_HOME` 环境变量
- SDK 版本必须匹配你的操作系统

### 方式 2：从 SAP 官方获取
- 访问 SAP Support Portal
- 搜索 "SAP NW RFC SDK" 或 "pyrfc"
- 下载对应平台的版本

### 方式 3：从公司内部获取
- 如果公司有内部软件仓库，可能已经有配置好的版本

## 🎯 推荐操作流程

### 在服务器上部署（使用你现有的 Linux SDK）：

1. **上传 SDK 到服务器**：
   ```bash
   scp -i .\enterprise_ai_platform.pem nwrfc750P_18-70002752.zip ubuntu@43.143.139.197:/opt/
   ```

2. **在服务器上解压**：
   ```bash
   ssh -i .\enterprise_ai_platform.pem ubuntu@43.143.139.197
   cd /opt
   unzip nwrfc750P_18-70002752.zip -d nwrfcsdk
   ```

3. **修改 docker-compose.yml**（在服务器上）：
   ```yaml
   mcp-gateway:
     environment:
       - SAPNWRFC_HOME=/opt/nwrfcsdk/nwrfcsdk
       - SAP_USER=你的SAP用户名
       - SAP_PASSWORD=你的SAP密码
       - SAP_HOST=你的SAP服务器IP
       - SAP_SYSNR=00
       - SAP_CLIENT=100
     volumes:
       - /opt/nwrfcsdk:/opt/nwrfcsdk:ro
   ```

4. **在容器内安装 pyrfc**：
   ```bash
   docker exec -it enterprise-ai-mcp-gateway bash
   export SAPNWRFC_HOME=/opt/nwrfcsdk/nwrfcsdk
   export LD_LIBRARY_PATH=$SAPNWRFC_HOME/lib:$LD_LIBRARY_PATH
   pip install pyrfc
   ```

5. **测试连接**：
   ```bash
   # 使用现有的工具测试
   curl -X POST http://localhost:8001/api/tools/sap_erp_table_query/execute \
     -H "Content-Type: application/json" \
     -d '{"table_name": "BKPF", "max_rows": 5}'
   ```

## 📚 相关文件

- **RFC 工具代码**：`mcp-gateway/src/tools/sap_erp_table_tool.py`
- **安装脚本**：`mcp-gateway/install_pyrfc_in_docker.sh`
- **测试脚本**：`mcp-gateway/test_sap_erp_table_tool.py`

## 🔍 总结

| 组件 | 作用 | 从哪里来 |
|------|------|----------|
| **SAP NWRFC SDK** | 底层 C/C++ 库，与 SAP 通信 | SAP 官方（你已有 Linux 版本） |
| **pyrfc** | Python 绑定，让 Python 调用 SDK | PyPI 或 SAP 官方 |
| **你的代码** | 使用 pyrfc 连接 SAP | 已准备好（`sap_erp_table_tool.py`） |

**关键理解**：
- SDK 是**基础**，pyrfc 是**桥梁**，你的代码是**应用**
- SDK 必须匹配操作系统（Linux/Windows）
- 你的 Linux SDK 包**正好适合服务器部署**！



















