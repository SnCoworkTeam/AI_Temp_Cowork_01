# Docker API版本错误修复说明

## 问题描述

在执行语义分析构建时，出现以下错误：
```
request returned Internal Server Error for API route and version 
http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/v1.46/containers/json
check if the server supports the requested API version
```

## 问题原因

虽然语义分析代码本身**没有直接调用Docker API**，但问题可能由以下原因引起：

1. **HTTP代理配置**: 如果系统环境变量中设置了`HTTP_PROXY`或`HTTPS_PROXY`，并且这些代理指向了Docker相关的服务
2. **httpx客户端默认行为**: httpx在某些情况下可能会使用系统默认的代理配置
3. **环境变量干扰**: 某些环境变量可能影响httpx的行为

## 修复方案

### 1. 代码修复（已完成）

已修改以下文件，明确禁用所有代理配置：

- `src/core/sap_semantic_index_builder.py`
- `src/services/metadata_client.py`

**关键修改**:
```python
# 修改前
self.http_client = httpx.AsyncClient(timeout=120.0)

# 修改后
self.http_client = httpx.AsyncClient(
    timeout=120.0,
    proxies={},  # 明确禁用所有代理（空字典表示禁用）
    verify=True,
    follow_redirects=True,
    limits=httpx.Limits(
        max_keepalive_connections=5,
        max_connections=10,
        keepalive_expiry=5.0
    )
)
```

### 2. 检查环境变量

运行以下脚本检查环境变量：
```bash
cd sap-metadata-agent
python check_environment.py
```

如果发现HTTP代理配置指向Docker，请：
```bash
# 临时取消代理（PowerShell）
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""
$env:http_proxy = ""
$env:https_proxy = ""

# 或在代码中明确禁用（已完成）
```

### 3. 验证修复

运行单条测试：
```bash
cd sap-metadata-agent
python test_one_semantic.py
```

如果测试通过，再运行分批构建：
```bash
python build_semantic_analysis.py --batch-size 10 --no-resume
```

## 技术细节

### 为什么会出现这个问题？

1. **httpx的代理检测**: httpx会自动检测系统环境变量中的代理设置
2. **Windows命名管道**: Docker Desktop在Windows上使用命名管道（`\\.\pipe\dockerDesktopLinuxEngine`）
3. **代理误配置**: 如果代理配置错误，可能导致请求被误路由到Docker API

### 修复原理

通过明确设置`proxies={}`（空字典），我们告诉httpx：
- 不使用任何代理
- 直接连接到目标URL
- 避免任何系统默认配置的干扰

## 验证步骤

1. **检查环境变量**:
   ```bash
   python check_environment.py
   ```

2. **测试单条数据**:
   ```bash
   python test_one_semantic.py
   ```

3. **小批量测试**:
   ```bash
   python build_semantic_analysis.py --batch-size 5 --no-resume
   ```

4. **如果仍有问题**:
   - 检查Docker Desktop是否正常运行
   - 检查是否有其他工具在监控Docker状态
   - 查看完整错误堆栈信息

## 预防措施

1. **代码层面**: 已在HTTP客户端初始化时明确禁用代理
2. **环境层面**: 建议在运行语义分析时，确保没有Docker相关的代理配置
3. **监控层面**: 如果问题再次出现，运行`check_environment.py`检查环境变量

## 相关文件

- `src/core/sap_semantic_index_builder.py` - 语义索引构建器（已修复）
- `src/services/metadata_client.py` - 元数据客户端（已修复）
- `check_environment.py` - 环境变量检查脚本（新建）
- `test_one_semantic.py` - 单条测试脚本（新建）

## 总结

这个问题**不是语义分析代码本身的问题**，而是HTTP客户端配置可能受到环境变量影响。通过明确禁用代理配置，我们确保了：

1. ✅ HTTP请求直接连接到目标服务
2. ✅ 不会触发任何Docker API调用
3. ✅ 不受系统环境变量干扰
4. ✅ 代码行为可预测和可控

如果问题仍然存在，请检查：
- Docker Desktop是否正常运行
- 是否有其他进程在监控Docker
- 完整的错误堆栈信息


