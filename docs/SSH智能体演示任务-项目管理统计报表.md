# SSH智能体演示任务 - 项目管理统计报表

## 📋 可直接使用的任务描述

请复制以下内容到SSH智能体执行：

---

**任务描述：**

请帮我创建一个项目管理统计报表功能，具体需求如下：

1. **创建Shell统计脚本**
   - 在 `/opt/enterprise-ai-platform/scripts` 目录下创建文件 `project_statistics.sh`
   - 脚本需要通过 `docker compose exec postgres` 连接到 PostgreSQL 数据库
   - 执行 SQL 查询统计以下信息：
     - 总项目数量
     - 各状态项目数量（按 status 字段分组统计：planning, active, completed, cancelled等）
     - 所有项目的平均进度百分比（progress_percent 字段的平均值）
     - 最近7天创建的项目数量（created_at 字段）
     - 各状态项目的平均进度
   - 使用 psql 的格式化选项（-A -t 或 \x）将结果格式化为易读的表格输出
   - 脚本应该包含错误处理，检查数据库连接是否成功

2. **创建Python统计脚本**
   - 在 `/opt/enterprise-ai-platform/scripts` 目录下创建 `project_statistics.py`
   - 使用 Python 的 psycopg2 库连接数据库
   - 从环境变量读取数据库连接信息：
     - DB_HOST=postgres（Docker网络内的服务名）
     - DB_PORT=5432
     - DB_USER=ai_user
     - DB_PASSWORD=ai_password
     - DB_NAME=ai_platform
   - 生成详细的统计报表，包含：
     - 项目状态分布统计（JSON格式，包含每个状态的数量和百分比）
     - 项目进度分布统计（0-25%, 25-50%, 50-75%, 75-100% 四个区间）
     - 按创建时间分组的项目数量（最近30天，每天的项目数，JSON格式）
     - 各状态项目的详细列表（每个状态的前5个项目，包含项目名称、进度、创建时间）
   - 输出格式化的文本报表和 JSON 数据到标准输出

3. **设置执行权限并测试**
   - 给两个脚本添加执行权限：`chmod +x project_statistics.sh project_statistics.py`
   - 测试 shell 脚本：`docker compose exec postgres bash /opt/enterprise-ai-platform/scripts/project_statistics.sh`
   - 测试 Python 脚本：`docker compose exec agent-service python3 /opt/enterprise-ai-platform/scripts/project_statistics.py`
   - 如果 scripts 目录不存在，先创建目录：`mkdir -p /opt/enterprise-ai-platform/scripts`

4. **验证和展示结果**
   - 执行两个脚本并显示完整的统计结果
   - 确认功能正常工作
   - 展示生成的报表内容

**数据库信息：**
- 表名：`pm_projects`
- 关键字段：`id`, `name`, `status`, `progress_percent`, `created_at`
- 数据库容器：`postgres`（docker compose 服务名）
- 数据库名：`ai_platform`
- 数据库用户：`ai_user`
- 数据库密码：`ai_password`

**注意事项：**
- 所有操作必须在 `/opt/enterprise-ai-platform` 目录下
- 使用 `docker compose exec` 命令时，服务名是 `postgres`（不是容器名）
- 脚本应该包含错误处理和连接验证
- Python 脚本需要处理数据库连接失败的情况

---

## 🎯 预期执行流程

智能体应该按以下步骤执行：

1. ✅ 检查并创建 `/opt/enterprise-ai-platform/scripts` 目录
2. ✅ 创建 `project_statistics.sh` 文件，包含 SQL 查询和格式化输出
3. ✅ 创建 `project_statistics.py` 文件，包含详细的统计逻辑
4. ✅ 给脚本添加执行权限
5. ✅ 执行 shell 脚本并显示结果
6. ✅ 执行 Python 脚本并显示结果
7. ✅ 验证两个脚本都正常工作

## 📊 预期输出示例

执行成功后应该看到类似以下输出：

```
=== 项目管理统计报表 (Shell脚本) ===

总项目数: 15
各状态项目数量:
planning: 3
active: 8
completed: 2
cancelled: 2

平均进度: 45.3%
最近7天创建的项目: 5

各状态平均进度:
planning: 10.5%
active: 55.2%
completed: 100.0%
cancelled: 0.0%

=== 项目管理统计报表 (Python脚本) ===

项目状态分布:
{
  "planning": {"count": 3, "percentage": 20.0},
  "active": {"count": 8, "percentage": 53.3},
  "completed": {"count": 2, "percentage": 13.3},
  "cancelled": {"count": 2, "percentage": 13.3}
}

进度分布:
0-25%: 4个项目
25-50%: 5个项目
50-75%: 4个项目
75-100%: 2个项目

最近30天项目创建趋势:
[日期和数量数据...]
```

