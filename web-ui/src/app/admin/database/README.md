# 数据库管理前端界面

## 功能概述

数据库管理前端界面提供了完整的数据库管理功能，包括：

### 1. 数据库概览 (`/admin/database/overview`)

- 数据库连接状态监控
- 表空间使用情况
- 数据库健康状态
- 关键指标统计

### 2. 数据表管理 (`/admin/database/tables`)

- 数据浏览器：浏览所有数据表
- SQL查询执行器：执行SQL查询
- 敏感数据脱敏显示

### 3. 备份管理 (`/admin/database/backups`)

- 备份列表查看
- 手动创建备份
- 自动备份配置
- 备份下载和删除

### 4. 性能监控 (`/admin/database/performance`)

- 实时性能指标
- 查询性能分析
- 连接数监控
- 性能趋势图表

## 安全特性

1. **权限控制**
   - 仅管理员可访问（`requireRoles: ["admin"]`）
   - 使用 `AuthGuard` 组件进行路由保护

2. **敏感数据保护**
   - 自动识别敏感字段（password, token, email等）
   - 默认隐藏敏感数据，可手动切换显示
   - 查询结果自动脱敏处理

3. **危险操作确认**
   - DROP、DELETE、TRUNCATE等操作需要二次确认
   - 使用模态框进行确认

4. **操作审计**
   - 所有数据库操作记录到审计日志
   - 通过后端API记录操作历史

## API端点

所有API端点都需要管理员权限（Bearer Token）：

- `GET /api/admin/database/stats` - 获取数据库统计
- `GET /api/admin/database/tables` - 获取数据表列表
- `POST /api/admin/database/query` - 执行SQL查询
- `GET /api/admin/database/backups` - 获取备份列表
- `POST /api/admin/database/backups/create` - 创建备份
- `GET /api/admin/database/backups/configs` - 获取备份配置
- `POST /api/admin/database/backups/configs` - 创建备份配置
- `GET /api/admin/database/performance` - 获取性能指标
- `GET /api/admin/database/performance/charts` - 获取性能图表数据

## 组件说明

### DataBrowser

数据表浏览器组件，支持：

- 搜索和过滤数据表
- 展开查看列信息
- 敏感字段标记
- 数据表详情查看

### QueryExecutor

SQL查询执行器，支持：

- SQL查询编辑
- 查询结果展示
- 结果导出（CSV）
- 危险操作确认
- 敏感数据脱敏

### BackupManager

备份管理组件，支持：

- 自动备份配置
- 备份计划设置
- 保留策略配置

### PerformanceCharts

性能图表组件，支持：

- 查询时间趋势
- 连接数趋势
- 实时数据更新

## 注意事项

1. 所有敏感操作都需要管理员权限
2. 危险SQL操作（DROP、DELETE等）需要二次确认
3. 查询结果默认脱敏敏感字段
4. 性能监控数据每30秒自动刷新
5. 建议定期备份数据库
