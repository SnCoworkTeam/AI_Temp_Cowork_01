# SAP RFC连接安装指南

## pyRFC安装问题

pyRFC库在Windows上安装需要先安装SAP NWRFC SDK。

## 安装步骤

### 1. 下载SAP NWRFC SDK

1. 访问SAP官网或SAP Support Portal
2. 下载SAP NWRFC SDK for Windows
3. 解压到本地目录（如：`C:\nwrfcsdk`）

### 2. 配置环境变量

```powershell
# 设置NWRFC SDK路径
$env:SAPNWRFC_HOME = "C:\nwrfcsdk"
$env:PATH = "$env:SAPNWRFC_HOME\lib;$env:PATH"
```

### 3. 安装pyRFC

```bash
pip install pyrfc
```

## 替代方案：使用数据库直连

如果无法安装pyRFC，可以使用数据库直连方式查询SAP表。

### 方案1：通过HANA数据库连接

S4 HANA系统使用HANA数据库，可以直接连接HANA数据库查询表。

### 方案2：通过OData服务

如果SAP系统启用了OData服务，可以通过OData API查询数据。

## 当前状态

测试脚本已创建，但需要先安装pyRFC才能运行。

**下一步**：
1. 安装SAP NWRFC SDK
2. 安装pyRFC
3. 重新运行测试脚本

