# Docker 容器中安装 pyrfc 指南

## 问题说明

`pyrfc` 库需要 SAP NWRFC SDK 才能安装和运行。在 Docker 容器中安装需要特殊配置。

## 安装步骤

### 方法1：在 Dockerfile 中安装（推荐用于生产环境）

1. **准备 SAP NWRFC SDK**
   - 从 SAP 官网或 SAP Support Portal 下载 SAP NWRFC SDK for Linux
   - 解压 SDK 文件

2. **修改 Dockerfile.dev**

   在 `deps` 阶段添加安装步骤：

   ```dockerfile
   # 安装 SAP NWRFC SDK（假设 SDK 文件在构建上下文中）
   # 方式1：从本地文件复制
   COPY nwrfcsdk /opt/nwrfcsdk
   
   # 方式2：从 URL 下载（需要认证）
   # RUN wget -q --user=USER --password=PASS https://.../nwrfcsdk.tar.gz && \
   #     tar -xzf nwrfcsdk.tar.gz -C /opt && \
   #     rm nwrfcsdk.tar.gz
   
   # 设置环境变量
   ENV SAPNWRFC_HOME=/opt/nwrfcsdk
   ENV LD_LIBRARY_PATH=$SAPNWRFC_HOME/lib:$LD_LIBRARY_PATH
   ENV PATH=$SAPNWRFC_HOME/lib:$PATH
   
   # 安装 pyrfc
   RUN pip install --no-cache-dir pyrfc
   ```

3. **重新构建镜像**

   ```bash
   docker-compose build mcp-gateway
   ```

### 方法2：在运行的容器中安装（用于测试）

1. **将 SAP NWRFC SDK 复制到容器**

   ```bash
   # 假设 SDK 在本地 /path/to/nwrfcsdk
   docker cp /path/to/nwrfcsdk enterprise-ai-mcp-gateway:/opt/nwrfcsdk
   ```

2. **进入容器并安装**

   ```bash
   docker exec -it enterprise-ai-mcp-gateway bash
   
   # 在容器内
   export SAPNWRFC_HOME=/opt/nwrfcsdk
   export LD_LIBRARY_PATH=$SAPNWRFC_HOME/lib:$LD_LIBRARY_PATH
   export PATH=$SAPNWRFC_HOME/lib:$PATH
   
   pip install pyrfc
   ```

3. **验证安装**

   ```bash
   python -c "import pyrfc; print(pyrfc.__version__)"
   ```

### 方法3：使用安装脚本

使用提供的安装脚本：

```bash
# 在容器内运行
docker exec -it enterprise-ai-mcp-gateway bash -c "SAPNWRFC_HOME=/opt/nwrfcsdk bash /app/install_pyrfc_in_docker.sh"
```

## 获取 SAP NWRFC SDK

SAP NWRFC SDK 可以从以下位置获取：

1. **SAP Support Portal** (需要 SAP 账号)
   - 访问：https://support.sap.com/
   - 搜索 "SAP NW RFC SDK"
   - 下载对应 Linux 版本的 SDK

2. **SAP 官网**
   - 某些版本可能提供公开下载

3. **从 SAP 系统管理员获取**
   - 如果您的组织有 SAP 系统，可以联系管理员获取 SDK

## 验证安装

安装完成后，运行测试脚本：

```bash
# 在容器内
cd /app
python test_sap_erp_table_tool.py
```

## 常见问题

### 1. 找不到 pyrfc 包

**原因**：pip 源可能没有预编译的 pyrfc 包

**解决**：确保已安装 SAP NWRFC SDK，pyrfc 需要从源码编译

### 2. 编译错误

**原因**：缺少编译工具或 SAP NWRFC SDK 路径不正确

**解决**：
- 确保 Dockerfile 中安装了 `gcc`, `g++`, `make`
- 检查 `SAPNWRFC_HOME` 环境变量是否正确
- 检查 `LD_LIBRARY_PATH` 是否包含 SDK 的 lib 目录

### 3. 运行时错误：找不到 libsapnwrfc.so

**原因**：SAP NWRFC SDK 库文件路径未正确设置

**解决**：
```bash
export LD_LIBRARY_PATH=$SAPNWRFC_HOME/lib:$LD_LIBRARY_PATH
```

## 替代方案

如果无法安装 pyrfc，可以考虑：

1. **通过 HANA 数据库直连**：直接连接 SAP HANA 数据库查询表
2. **通过 OData 服务**：如果 SAP 系统启用了 OData，使用 REST API
3. **通过 SAP RFC 中间件**：使用其他支持 RFC 的中间件

## 当前状态

- ✅ Dockerfile.dev 已添加编译工具（gcc, g++）
- ✅ 安装脚本已创建
- ⚠️ 需要 SAP NWRFC SDK 才能完成安装

