# OpenCode 在本项目中的使用约定

本文档供 OpenCode 在此仓库中执行任务时参考，确保所有操作仅针对**当前项目根目录**，且符合项目结构。

## 工作范围

- **工作目录**：当前实例的根目录即为本仓库根目录（容器内为 `/workspace`，对应宿主机上的项目根目录）。
- **仅在此根目录下操作**：所有读/写/执行、创建文件、运行命令的默认工作目录均为该根目录；不要切换到或操作该目录以外的路径。
- 新建示例应用、小项目或演示代码时，请放在 **`project_management/`** 下或与团队约定的子目录中，并在对话中说明放置位置，便于在项目管理或门户中展示。

## 常用操作示例

### 创建 Hello World 类应用（后端 + 前端页面）

- 在 **`project_management/`** 下创建子目录（例如 `project_management/demos/helloworld/`）。
- 后端与前端页面文件均放在该子目录内，路径相对项目根目录。
- 完成后说明：生成的文件路径、如何在本项目中运行或展示（例如通过现有 web-ui 或 project_management 路由挂载）。

### 查看某个服务的 Docker 日志

- 所有服务均在同一 Docker Compose 中，容器名格式为：`enterprise-ai-<服务名>`。
- 查看日志命令：`docker logs <容器名>`，例如：
  - `docker logs enterprise-ai-api-gateway`
  - `docker logs enterprise-ai-chat-service`
  - `docker logs enterprise-ai-auth-service`
  - `docker logs enterprise-ai-postgres`
  - `docker logs enterprise-ai-redis`
  - `docker logs enterprise-ai-web-ui`
  - `docker logs enterprise-ai-workflow-engine`
  - `docker logs enterprise-ai-opencode`
  - 其他服务：`enterprise-ai-agent-service`、`enterprise-ai-knowledge-base`、`enterprise-ai-metadata-service`、`enterprise-ai-project-management` 等，命名规则一致。
- 在 OpenCode 中使用 **bash** 工具，工作目录保持为项目根目录，执行上述 `docker logs` 命令即可；需要最近行数时可加 `--tail 100` 等参数。

### 其他与项目相关的操作

- 修改代码、添加配置、编写脚本时，路径均相对于项目根目录。
- 涉及 Docker 时，优先使用当前项目下的 `docker-compose.yml` 及已有容器名，不随意在系统其他路径创建或操作容器。

## 服务/容器名速查（19 服务 + OpenCode）

| 服务       | 容器名 |
|------------|--------|
| PostgreSQL | enterprise-ai-postgres |
| Redis      | enterprise-ai-redis |
| API Gateway | enterprise-ai-api-gateway |
| Web UI     | enterprise-ai-web-ui |
| Auth       | enterprise-ai-auth-service |
| Chat       | enterprise-ai-chat-service |
| 知识库     | enterprise-ai-knowledge-base |
| 工作流     | enterprise-ai-workflow-engine |
| 项目管理   | enterprise-ai-project-management |
| OpenCode   | enterprise-ai-opencode |
| 其他       | enterprise-ai-<服务名>，见本仓库 `docker-compose.yml` 中 `container_name` |

## 语言输出约定（固定中文）

- 所有面向用户的自然语言输出（包括普通回复、计划说明、总结）默认使用**简体中文**。
- 触发提问/确认流程时（question 卡片）：问题文本、选项标题、选项说明、提示语必须使用**简体中文**。
- 仅当用户明确要求其他语言时，才可切换语言；任务结束后恢复为简体中文。
- 命令、路径、代码、错误码可保留原文，但解释必须为中文。
- 不要输出 `<think>` 标签或思考过程；只输出对用户可见的最终中文答案。
