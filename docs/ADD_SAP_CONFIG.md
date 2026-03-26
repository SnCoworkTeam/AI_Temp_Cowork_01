# 添加SAP配置到配置中心

## 方法1：使用PowerShell脚本（推荐）

### 步骤1：设置环境变量

在PowerShell中设置SAP配置：

```powershell
# 必需配置
$env:SAP_BASE_URL = "https://your-sap-system.com"  # 替换为您的SAP系统URL
$env:SAP_USERNAME = "your_username"                # 替换为您的SAP用户名
$env:SAP_PASSWORD = "your_password"                # 替换为您的SAP密码

# 可选配置（有默认值）
$env:SAP_CLIENT = "100"                            # SAP客户端编号，默认100
$env:SAP_LANGUAGE = "EN"                           # SAP系统语言，默认EN
```

### 步骤2：运行脚本

```powershell
.\scripts\add_sap_config.ps1
```

## 方法2：使用curl命令（手动添加）

### 添加必需配置

```powershell
# SAP基础URL
curl -X POST http://localhost:8090/api/config `
  -H "Content-Type: application/json" `
  -d '{"key":"sap.base_url","value":"https://your-sap-system.com","description":"SAP系统的基础URL","environment":"default"}'

# SAP用户名
curl -X POST http://localhost:8090/api/config `
  -H "Content-Type: application/json" `
  -d '{"key":"sap.username","value":"your_username","description":"SAP用户名","environment":"default"}'

# SAP密码
curl -X POST http://localhost:8090/api/config `
  -H "Content-Type: application/json" `
  -d '{"key":"sap.password","value":"your_password","description":"SAP密码","environment":"default"}'
```

### 添加可选配置

```powershell
# SAP客户端
curl -X POST http://localhost:8090/api/config `
  -H "Content-Type: application/json" `
  -d '{"key":"sap.client","value":"100","description":"SAP客户端编号","environment":"default"}'

# SAP语言
curl -X POST http://localhost:8090/api/config `
  -H "Content-Type: application/json" `
  -d '{"key":"sap.language","value":"EN","description":"SAP系统语言","environment":"default"}'

# SAP超时时间（毫秒）
curl -X POST http://localhost:8090/api/config `
  -H "Content-Type: application/json" `
  -d '{"key":"sap.timeout","value":"300000","description":"SAP请求超时时间（毫秒）","environment":"default"}'

# SAP最大重试次数
curl -X POST http://localhost:8090/api/config `
  -H "Content-Type: application/json" `
  -d '{"key":"sap.max_retries","value":"3","description":"SAP请求最大重试次数","environment":"default"}'

# SAP分页大小
curl -X POST http://localhost:8090/api/config `
  -H "Content-Type: application/json" `
  -d '{"key":"sap.page_size","value":"1000","description":"SAP查询分页大小","environment":"default"}'

# SAP最大记录数
curl -X POST http://localhost:8090/api/config `
  -H "Content-Type: application/json" `
  -d '{"key":"sap.max_records","value":"10000","description":"SAP查询最大记录数","environment":"default"}'
```

## 方法3：使用Python脚本

```bash
# 安装依赖
pip install httpx

# 修改脚本中的配置值
# 编辑 scripts/add_sap_config.py，填写SAP配置值

# 运行脚本
python scripts/add_sap_config.py
```

或者通过命令行参数传递：

```bash
python scripts/add_sap_config.py base_url=https://your-sap-system.com username=your_username password=your_password
```

## 配置项说明

### 必需配置

| 配置键 | 说明 | 示例值 |
|--------|------|--------|
| `sap.base_url` | SAP系统的基础URL | `https://your-sap-system.com` |
| `sap.username` | SAP用户名 | `your_username` |
| `sap.password` | SAP密码 | `your_password` |

### 可选配置（有默认值）

| 配置键 | 说明 | 默认值 |
|--------|------|--------|
| `sap.client` | SAP客户端编号 | `100` |
| `sap.language` | SAP系统语言 | `EN` |
| `sap.timeout` | SAP请求超时时间（毫秒） | `300000` (5分钟) |
| `sap.max_retries` | SAP请求最大重试次数 | `3` |
| `sap.page_size` | SAP查询分页大小 | `1000` |
| `sap.max_records` | SAP查询最大记录数 | `10000` |

## 验证配置

添加配置后，可以验证：

```powershell
# 获取单个配置
curl http://localhost:8090/api/config/sap.base_url?environment=default

# 获取所有配置
curl http://localhost:8090/api/configs/all?environment=default
```

## 使配置生效

配置添加后，需要重启 `sap-mcp-server` 服务：

```bash
docker-compose restart sap-mcp-server
```

## 注意事项

1. **安全性**：SAP密码等敏感信息存储在配置中心，请确保配置中心的安全性
2. **环境隔离**：可以使用不同的 `environment` 参数（如 `dev`, `test`, `prod`）来隔离不同环境的配置
3. **配置更新**：如果需要更新配置，使用相同的API，配置中心会自动增加版本号
































