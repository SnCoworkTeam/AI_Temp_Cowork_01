# 快速测试 pyrfc 安装

## 当前状态

✅ **Dockerfile.dev 已更新**：添加了编译工具（gcc, g++, make）
✅ **安装脚本已创建**：`install_pyrfc_in_docker.sh`
✅ **测试脚本已创建**：`test_sap_in_docker.sh`
⚠️ **需要 SAP NWRFC SDK**：pyrfc 无法直接安装，需要先安装 SAP NWRFC SDK

## 快速测试步骤

### 1. 检查容器状态

```bash
docker-compose ps mcp-gateway
```

### 2. 尝试安装 pyrfc（需要 SAP NWRFC SDK）

如果您有 SAP NWRFC SDK：

```bash
# 方式1：使用安装脚本
docker exec -it enterprise-ai-mcp-gateway bash -c "SAPNWRFC_HOME=/opt/nwrfcsdk bash /app/install_pyrfc_in_docker.sh"

# 方式2：手动安装
docker exec -it enterprise-ai-mcp-gateway bash
# 在容器内：
export SAPNWRFC_HOME=/opt/nwrfcsdk
export LD_LIBRARY_PATH=$SAPNWRFC_HOME/lib:$LD_LIBRARY_PATH
pip install pyrfc
```

### 3. 验证安装

```bash
docker exec enterprise-ai-mcp-gateway python -c "import pyrfc; print('✅ pyrfc 已安装')"
```

### 4. 运行测试

```bash
# 在容器内运行测试
docker exec -it enterprise-ai-mcp-gateway bash -c "cd /app && python test_sap_erp_table_tool.py"
```

## 如果没有 SAP NWRFC SDK

如果您没有 SAP NWRFC SDK，可以考虑：

1. **联系 SAP 系统管理员**获取 SDK
2. **从 SAP Support Portal 下载**（需要 SAP 账号）
3. **使用替代方案**：
   - 通过 HANA 数据库直连
   - 通过 OData 服务
   - 使用其他 RFC 中间件

## 下一步

1. 获取 SAP NWRFC SDK
2. 按照 `DOCKER_PYRFC_INSTALLATION.md` 中的步骤安装
3. 运行测试脚本验证功能

