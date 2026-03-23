# SSH智能体 - 项目管理功能演示

## 演示场景：创建一个项目统计脚本

通过SSH智能体创建一个简单的项目管理功能脚本，用于统计项目信息。

## 推荐演示任务

### 任务1：创建项目统计脚本（推荐）

```
请在 /opt/enterprise-ai-platform 目录下创建一个项目统计脚本 project_stats.sh，
脚本功能如下：
1. 显示当前项目总数
2. 按状态统计项目数量（planning, active, completed, cancelled）
3. 显示最近创建的5个项目名称
4. 显示项目总进度平均值

脚本应该：
- 通过 docker-compose exec 连接到数据库容器执行SQL查询
- 输出格式化的统计信息
- 包含错误处理
```

### 任务2：创建项目备份脚本（实用）

```
请在 /opt/enterprise-ai-platform 目录下创建一个项目数据备份脚本 backup_projects.sh，
功能包括：
1. 创建备份目录 /opt/enterprise-ai-platform/backups/projects/$(date +%Y%m%d_%H%M%S)
2. 使用 docker-compose exec 导出项目表数据到SQL文件
3. 压缩备份文件
4. 显示备份文件大小和位置
5. 保留最近7天的备份，删除更早的备份
```

### 任务3：创建项目健康检查脚本（展示能力）

```
请在 /opt/enterprise-ai-platform 目录下创建一个项目健康检查脚本 check_project_health.sh，
脚本功能：
1. 检查 project-management 服务是否运行
2. 测试项目管理API端点 /api/v1/projects 是否可访问
3. 检查数据库连接是否正常
4. 显示最近24小时创建的项目数量
5. 输出格式化的健康检查报告
```

## 最佳演示任务（推荐使用）

**任务描述：**
```
请在 /opt/enterprise-ai-platform/scripts 目录下创建一个项目统计脚本 project_stats.sh，
脚本需要：
1. 通过 docker-compose exec 连接到 database 容器
2. 执行SQL查询统计项目信息：
   - 总项目数
   - 各状态项目数量（planning, active, completed, cancelled）
   - 平均进度百分比
3. 格式化输出统计结果
4. 添加执行权限
5. 测试执行脚本显示结果
```

**预期效果：**
- 创建了一个可执行的脚本文件
- 脚本能够连接数据库并查询项目统计信息
- 输出格式化的统计结果
- 展示SSH智能体的文件创建、权限设置、命令执行能力

## 使用步骤

1. 打开SSH智能体详情页
2. 在"任务描述"输入框中粘贴上述任务
3. 点击"执行"按钮
4. 等待执行完成
5. 在"执行结果"区域查看：
   - 脚本创建过程
   - 脚本内容
   - 执行结果输出

## 预期输出示例

执行成功后，您应该看到类似以下输出：

```
脚本创建成功
文件位置: /opt/enterprise-ai-platform/scripts/project_stats.sh

执行结果:
========================================
项目统计报告
========================================
总项目数: 15
状态分布:
  - Planning: 3
  - Active: 8
  - Completed: 3
  - Cancelled: 1
平均进度: 45.2%
========================================
```

## 注意事项

- 所有操作都限制在 /opt/enterprise-ai-platform 目录下
- 脚本会通过 docker-compose 执行，确保服务正常运行
- 脚本包含错误处理，不会破坏系统
- 可以重复执行查看最新统计

