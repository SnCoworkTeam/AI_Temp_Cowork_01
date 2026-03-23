# SSH智能体 - 项目管理统计报表功能演示

## 演示任务描述

请帮我创建一个项目管理统计报表功能，具体需求如下：

1. **在服务器上创建统计脚本**
   - 在 `/opt/enterprise-ai-platform/scripts` 目录下创建文件 `project_statistics.sh`
   - 脚本需要连接到 PostgreSQL 数据库容器（通过 docker compose exec database）
   - 执行 SQL 查询统计以下信息：
     - 总项目数量
     - 各状态项目数量（planning, active, completed, cancelled等）
     - 平均进度百分比
     - 最近7天创建的项目数量
     - 各状态项目的平均进度
   - 将统计结果格式化为易读的表格输出，使用 psql 的格式化选项

2. **生成 Python 统计脚本**
   - 在 `/opt/enterprise-ai-platform/scripts` 目录下创建 `project_statistics.py`
   - 使用 Python 连接数据库（通过环境变量或配置文件读取数据库连接信息）
   - 生成详细的统计报表，包含：
     - 项目状态分布统计（JSON格式，可用于图表）
     - 项目进度分布统计（0-25%, 25-50%, 50-75%, 75-100%）
     - 按创建时间分组的项目数量（最近30天，每天的项目数）
     - 各状态项目的详细列表（前10个）
   - 输出格式化的文本报表和 JSON 数据

3. **在 Docker 容器中执行和测试**
   - 给脚本添加执行权限（chmod +x）
   - 使用 `docker compose exec database` 执行 shell 脚本
   - 使用 `docker compose exec agent-service` 或 `web-ui` 执行 Python 脚本
   - 确保数据库连接信息正确（从环境变量或 docker-compose.yml 获取）

4. **验证和展示结果**
   - 执行两个脚本并显示统计结果
   - 确认功能正常工作
   - 展示生成的报表内容

## 预期执行步骤

智能体应该：
1. 创建 shell 脚本文件
2. 创建 Python 脚本文件
3. 给脚本添加执行权限
4. 在适当的容器中执行脚本
5. 展示执行结果

## 数据库表结构参考

项目表结构（根据实际数据库迁移文件）：
- 表名：`pm_projects`
- 主要字段：
  - `id`: 项目ID (UUID)
  - `project_code`: 项目编码
  - `name`: 项目名称
  - `description`: 项目描述
  - `status`: 项目状态（planning, active, completed, cancelled等）
  - `progress_percent`: 进度百分比（0-100，Float类型）
  - `priority`: 优先级
  - `start_date`: 计划开始日期
  - `end_date`: 计划结束日期
  - `created_at`: 创建时间
  - `updated_at`: 更新时间

## 数据库连接信息

从 docker-compose.yml 获取：
- 数据库容器名：`enterprise-ai-postgres`（docker compose 服务名：`postgres`）
- 数据库名：`ai_platform`（从环境变量 `DB_NAME` 获取，默认值）
- 数据库用户：`ai_user`（从环境变量 `DB_USER` 获取，默认值）
- 数据库密码：`ai_password`（从环境变量 `DB_PASSWORD` 获取，默认值）
- 数据库端口：`5432`（容器内）
- 连接方式：`docker compose exec postgres psql -U ai_user -d ai_platform`

## 注意事项

- 所有操作必须在 `/opt/enterprise-ai-platform` 目录下
- 使用 `docker compose exec` 命令时注意容器名称（可能是 `postgres` 或 `enterprise-ai-postgres`）
- 确保数据库连接信息正确（可以从环境变量或 docker-compose.yml 获取）
- 脚本应该包含错误处理和连接验证
- Python 脚本需要安装 psycopg2 或 psycopg2-binary（agent-service 容器中应该已安装）

## 执行示例

智能体执行后应该生成类似以下的结果：

```
=== 项目管理统计报表 ===

总项目数: 15
各状态项目数量:
  - planning: 3
  - active: 8
  - completed: 2
  - cancelled: 2

平均进度: 45.3%
最近7天创建的项目: 5

各状态平均进度:
  - planning: 10%
  - active: 55%
  - completed: 100%
  - cancelled: 0%
```

