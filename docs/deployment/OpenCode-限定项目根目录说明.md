# OpenCode 限定在项目根目录使用说明

本文说明如何让 OpenCode 在服务器上**只针对当前项目**（项目根目录）进行开发、部署等操作，并实现“创建 Hello World、查看某服务 Docker 日志”等能力。

## 一、实现方式概览

1. **工作目录锁定**：通过环境变量 `OPENCODE_LOCK_WORKSPACE=1`，服务端强制使用容器内的工作目录（即挂载的项目根目录），忽略前端或 API 传入的其他目录，从而**认准当前服务器项目根、且仅在该根目录下操作**。
2. **项目级说明**：在项目根目录放置 **AGENTS.md**，OpenCode 会自动读取并作为上下文，约束“只在此根目录操作”、约定新建应用放在 `project_management/` 等、以及如何查看各服务 Docker 日志。

## 二、配置步骤

### 2.1 确保挂载的是项目根目录

在 compose 中，将宿主机上的**项目根目录**挂载到容器的 `/workspace`：

```yaml
volumes:
  - ${OPENCODE_WORKSPACE:-.}:/workspace:cached
```

在 `.env` 中设置：

```bash
OPENCODE_WORKSPACE=/opt/enterprise-ai-platform
```

（路径改为你服务器上本仓库的实际根目录。）

这样容器内 `process.cwd()` 即为 `/workspace`，即项目根。

### 2.2 开启工作目录锁定

在 OpenCode 服务的环境变量中增加：

```yaml
environment:
  - OPENCODE_LOCK_WORKSPACE=1
```

- **本地 Web 镜像**的 compose（`docker-compose.opencode.local-web.yml`）中已默认配置 `OPENCODE_LOCK_WORKSPACE=1`。
- **官方镜像**的 compose（`docker-compose.opencode.yml`）中可通过 `.env` 设置 `OPENCODE_LOCK_WORKSPACE=1`（默认已为 1）。

效果：所有会话的“当前目录”均为 `/workspace`（项目根），不会随 URL 参数或请求头切换到其他路径。

### 2.3 项目根目录下的 AGENTS.md

本仓库根目录已提供 **AGENTS.md**，内容包括：

- 工作范围限定在项目根目录，不操作根目录以外路径。
- 新建示例/演示应用时放在 **`project_management/`** 下（或约定子目录），便于在项目管理或门户中展示。
- 查看某服务 Docker 日志：使用 **bash** 工具执行 `docker logs <容器名>`，并给出 19 服务及 OpenCode 的容器名速查表（如 `enterprise-ai-api-gateway`、`enterprise-ai-chat-service` 等）。

OpenCode 会自动读取项目根目录下的 AGENTS.md，无需额外配置。

## 三、在 OpenCode 中的典型用法

### 3.1 创建 Hello World（后端 + 前端页面）并放到项目管理目录

在 OpenCode 对话中可输入类似：

- “在 project_management 下创建一个 helloworld 示例，包含后端接口和前端页面，并说明如何在本项目中展示。”

OpenCode 会：

- 在 **`project_management/`** 下创建子目录（如 `project_management/demos/helloworld/`）。
- 在该目录内生成后端与前端页面代码。
- 所有路径相对项目根目录，符合“只针对当前项目”的约束。

### 3.2 查看某个服务的 Docker 日志

在 OpenCode 对话中可输入类似：

- “查看 api-gateway 的最近 100 行 Docker 日志。”
- “查看 chat-service 的 Docker 日志。”

OpenCode 会使用 **bash** 工具，在项目根目录下执行例如：

```bash
docker logs --tail 100 enterprise-ai-api-gateway
docker logs enterprise-ai-chat-service
```

容器名与 `docker-compose.yml` 中一致，见 AGENTS.md 中的速查表。

## 四、代码层面的实现说明（供二次修改参考）

- **服务端**（`opencode-src/packages/opencode/src/server/server.ts`）：  
  当 `OPENCODE_LOCK_WORKSPACE=1` 时，请求处理中用于 `Instance.provide` 的 `directory` 固定为 `process.cwd()`（即容器内 `/workspace`），不再使用 query 或 header 中的 directory。  
  因此无论 Web 或 API 传什么路径，实际工作目录都是项目根。

- **项目约定**：通过仓库根目录的 **AGENTS.md** 约定“只在此根目录操作”、新建应用目录和 Docker 容器名，由 OpenCode 的 instruction 机制自动加载，无需改 OpenCode 源码。

## 五、小结

| 目标                     | 做法 |
|--------------------------|------|
| 认准服务器项目根目录     | 设置 `OPENCODE_WORKSPACE` 为项目根，挂载到容器 `/workspace`。 |
| 只针对根目录操作         | 设置 `OPENCODE_LOCK_WORKSPACE=1`；保留项目根下的 AGENTS.md。 |
| 新建应用放到项目管理目录 | AGENTS.md 中约定放在 `project_management/` 下，OpenCode 按此执行。 |
| 查看某服务 Docker 日志  | 在对话中要求查看某服务日志，OpenCode 用 bash 执行 `docker logs <容器名>`，容器名见 AGENTS.md。 |

按上述配置后，OpenCode 在服务器上即会以当前项目根为唯一工作范围，并支持“创建 Hello World 并放到项目管理目录”和“查看某服务 Docker 日志”等操作。
