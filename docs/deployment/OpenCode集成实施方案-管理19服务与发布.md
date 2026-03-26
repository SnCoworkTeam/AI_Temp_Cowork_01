# OpenCode 集成实施方案：管理 19 服务与发布到服务器

## 一、目标与范围

- **目标**：使用 [OpenCode](https://github.com/anomalyco/opencode) 管理当前 zhgj 分支下已部署的 19 个服务，并支持在 OpenCode 中编写简单功能后，将变更直接发布到服务器上指定应用（如项目管理服务 project-management）。
- **范围**：
  - OpenCode 的部署方式：单独服务器 vs 与 19 服务同机 Docker。
  - 开发→发布闭环：在 OpenCode 中编辑代码 → 构建/部署到目标服务。

---

## 二、方案对比：单独部署 vs 同机 Docker

| 维度 | 方案 A：OpenCode 单独部署（推荐） | 方案 B：与 19 服务同机 Docker |
|------|----------------------------------|-------------------------------|
| **部署位置** | 一台开发/跳板机（或本机） | 与 19 服务同一台服务器，以 Docker 服务形式加入 compose |
| **代码位置** | 开发机上克隆的仓库，或挂载到 OpenCode 工作目录 | 与现有 compose 共享同一套代码挂载（如 `/workspace`） |
| **资源与隔离** | 开发与生产隔离，互不影响 | 共用 CPU/内存，可能影响生产服务稳定性 |
| **权限与安全** | OpenCode 仅需访问代码与部署 API/SSH，权限可控 | 容器需访问 Docker socket 或宿主机部署脚本，权限较大 |
| **发布流程** | 开发机调用部署 API（如 deployment-agent）或 SSH 到目标机执行部署 | 同机直接执行 `docker compose build project-management && docker compose up -d project-management` 或调用 deployment-agent |
| **适用场景** | 多人开发、生产环境需严格隔离 | 单机内网、希望“改完即部署”的快捷闭环 |

**推荐**：优先采用 **方案 A（OpenCode 单独部署）**，仅在仅有一台服务器且希望简化运维时考虑方案 B。

---

## 三、推荐方案 A：OpenCode 单独部署

### 3.1 架构示意

```
┌─────────────────────────────────────────────────────────────────┐
│  开发/跳板机（或开发者本机）                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  OpenCode (opencode serve 或 Desktop/TUI)                  │   │
│  │  - 工作目录：enterprise-ai-platform 仓库（克隆或挂载）       │   │
│  │  - 端口：4096 (serve 时)                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                    开发者用 TUI/Desktop attach                    │
│                    或通过 HTTP API 发 prompt/命令                  │
└─────────────────────────────────────────────────────────────────┘
                               │
                    发布：HTTP 调用 / SSH / 脚本
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  目标服务器（已部署 19 服务的机器）                                 │
│  ┌─────────────────────┐  ┌─────────────────────────────────┐  │
│  │  deployment-agent    │  │  docker compose (19 服务)        │  │
│  │  POST /api/v1/deploy  │→ │  如 project-management 等       │  │
│  └─────────────────────┘  └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 前置条件

- 开发/跳板机与目标服务器之间网络可达（能访问 deployment-agent 的端口，或 SSH）。
- 目标服务器上 19 服务已按现有方式部署（docker-compose），且可选启用 **deployment-agent** 以便按服务列表触发部署。
- 若通过部署脚本发布：开发机或 OpenCode 所在机可 SSH 到目标服务器，或能通过 CI/脚本把代码或镜像同步到目标机后再执行部署。

### 3.3 实施步骤

#### 步骤 1：在开发/跳板机上安装 OpenCode

在用于“管理 19 服务、编写功能”的机器上安装 OpenCode（与目标服务器可分离）：

```bash
# 方式一：官方一键安装（Linux/macOS）
curl -fsSL https://opencode.ai/install | bash

# 方式二：npm（跨平台）
npm i -g opencode-ai@latest

# 方式三：Windows
# scoop install opencode  或  choco install opencode
```

验证：

```bash
opencode --version
```

#### 步骤 2：准备代码仓库（OpenCode 工作目录）

在 OpenCode 将要工作的目录下克隆或拉取 zhgj 分支：

```bash
git clone --branch zhgj https://github.com/your-org/enterprise-ai-platform.git
cd enterprise-ai-platform
```

或使用现有本地仓库，确保分支与服务器部署一致（如 zhgj）。

#### 步骤 3：以 Server 模式运行（可选，便于远程与自动化）

若希望远程连接或通过 API 驱动 OpenCode，在开发机上启动无头服务：

```bash
cd /path/to/enterprise-ai-platform
OPENCODE_SERVER_PASSWORD=你的密码 opencode serve --hostname 0.0.0.0 --port 4096
```

- 本机或同网机器可用 TUI 连接：`opencode attach --hostname <开发机IP> --port 4096`
- API 文档：`http://<开发机IP>:4096/doc`

#### 步骤 4：在 OpenCode 中“管理 19 服务”与编写功能

- **管理**：在 OpenCode 中打开上述仓库，通过自然语言或指令浏览/修改各服务代码（如 `project_management`、`api-gateway` 等）。
- **编写功能**：在对应服务目录下编辑代码（例如在 `project_management/src` 下新增接口或逻辑）。
- **发布前自检**：可在 OpenCode 的 shell 中执行项目已有测试或 lint（若已配置）。

#### 步骤 5：发布到服务器上指定服务（如项目管理服务）

两种常用方式（可二选一或组合）。

**方式 5a：通过 deployment-agent API（推荐）**

目标服务器上已启动 deployment-agent 且开发机可访问其端口时：

```bash
# 在 OpenCode 的 shell 中或本机执行
curl -X POST "http://<目标服务器IP>:8007/api/v1/deploy" \
  -H "Content-Type: application/json" \
  -d '{
    "services": ["project-management"],
    "target_server": "app-server",
    "skip_data_sync": true,
    "skip_migration": false
  }'
```

将 `services` 改为需要发布的服务名（如 `["api-gateway","project-management"]`）。

**方式 5b：SSH + 目标机脚本**

开发机通过 SSH 在目标服务器上执行构建并重启指定服务：

```bash
ssh user@目标服务器 "cd /path/to/enterprise-ai-platform && docker compose build project-management && docker compose up -d project-management"
```

若你们已有 `scripts/zhgj-build-and-up.ps1` 或 `scripts/deployment/complete-sync.ps1`，可改为在目标机上执行对应脚本（或通过 SSH 触发）。

#### 步骤 6：将“发布”固化为 OpenCode 可调用的命令

- 在仓库根目录增加小脚本（如 `scripts/deployment/deploy-one-service.sh`），参数为服务名，内部封装上述 curl 或 SSH 逻辑。
- 在 OpenCode 中需要发布时，直接让 AI 执行该脚本，例如：
  - “请发布项目管理服务：执行 scripts/deployment/deploy-one-service.sh project-management”。

这样即可实现：**在 OpenCode 编写功能 → 执行一条命令 → 发布到服务器上指定应用**。

---

## 四、备选方案 B：OpenCode 与 19 服务同机 Docker

适用于只有一台服务器、希望“改完即部署”且可接受 OpenCode 与业务服务共用资源的情况。

### 4.1 注意点

- OpenCode 官方镜像是面向 CLI/Desktop 的，Docker 内通常以 **无头 serve 模式** 运行；交互需通过另一台机器上的 TUI/Desktop 使用 `opencode attach` 连接。
- 容器内需挂载代码目录，并具备调用部署逻辑的能力（如访问 Docker socket 或调用宿主机上的部署脚本/API）。

### 4.2 在 docker-compose 中增加 OpenCode 服务（示例）

以下为概念示例，需根据实际 OpenCode 镜像与路径调整：

```yaml
# 在 docker-compose.yml 的 services 下追加（与现有 19 服务并列）
  opencode:
    image: node:20-bookworm-slim   # 或社区/自建 opencode 镜像
    container_name: enterprise-ai-opencode
    working_dir: /workspace
    command: sh -c "npm i -g opencode-ai@latest && opencode serve --hostname 0.0.0.0 --port 4096"
    ports:
      - "${OPENCODE_PORT:-4096}:4096"
    environment:
      - OPENCODE_SERVER_PASSWORD=${OPENCODE_SERVER_PASSWORD:-}
      - OPENCODE_SERVER_USERNAME=opencode
    volumes:
      - .:/workspace:cached
      # 若需在容器内触发 docker 构建，可挂载 docker.sock（有安全风险，仅内网考虑）
      # - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - enterprise-ai-network
    restart: unless-stopped
    profiles:
      - optional
```

- 代码通过 `.:/workspace` 与现有 19 服务共享同一套仓库，在 OpenCode 中修改即改的是同一份代码。
- 发布时可在 OpenCode 的 shell 中执行：
  - 调用本机 deployment-agent：`curl -X POST http://deployment-agent:8000/api/v1/deploy -H "Content-Type: application/json" -d '{"services":["project-management"]}'`
  - 或若挂载了 docker.sock，可在容器内执行 `docker compose build project-management && docker compose up -d project-management`（需在挂载的目录下且安装 docker-cli）。

### 4.3 使用方式

- 在任意能访问该服务器 4096 端口的机器上执行：`opencode attach --hostname <服务器IP> --port 4096`，即可在 TUI 中操作 `/workspace` 下的仓库并编写功能。
- 编写完成后，按上面方式在 OpenCode 中触发部署，即可发布到同机上的 project-management 等应用服务。

---

## 五、服务名与 deployment-agent 的对应关系

部署时 `services` 列表需与 docker-compose 中服务名一致。当前与“应用服务”相关的部分服务名如下（供发布时填写）：

| 服务说明       | docker-compose 服务名        |
|----------------|-----------------------------|
| 项目管理       | `project-management`        |
| API 网关       | `api-gateway`               |
| 工作流引擎     | `workflow-engine`           |
| 认证服务       | `auth-service`              |
| 知识库         | `knowledge-base`            |
| 元数据服务     | `metadata-service`          |
| 聊天服务       | `chat-service`              |
| 前端           | `web-ui`                    |
| 部署智能体     | `deployment-agent`          |
| 其他           | 见 docker-compose.yml 中 services 名称 |

---

## 六、安全与运维建议

1. **OpenCode Server 认证**：生产或内网暴露时务必设置 `OPENCODE_SERVER_PASSWORD`（及可选 `OPENCODE_SERVER_USERNAME`）。
2. **网络**：若 OpenCode 与 deployment-agent 跨机，限制仅允许开发/跳板机访问 deployment-agent 端口（如 8007）。
3. **发布权限**：通过 deployment-agent 或 SSH 发布时，使用专用账号与密钥，并限制可执行命令范围。
4. **代码一致性**：发布前建议在 OpenCode 工作目录执行 `git status` / `git diff`，确认要发布的变更；发布流程可加入“仅允许已提交代码部署”的策略（由脚本或 CI 约束）。

---

## 七、总结与下一步

- **推荐路径**：采用 **方案 A**，在单独开发/跳板机上安装 OpenCode，工作目录指向 enterprise-ai-platform（zhgj），通过 **deployment-agent 的 POST /api/v1/deploy** 或 SSH+脚本，将指定服务（如 `project-management`）发布到已部署 19 服务的服务器。
- **快速闭环**：在仓库中新增 `scripts/deployment/deploy-one-service.sh`（或 .ps1），接收服务名参数并调用上述部署逻辑，在 OpenCode 中通过一句自然语言或命令即可完成“发布到某应用服务”。
- 若必须与 19 服务同机，可采用 **方案 B** 在 docker-compose 中增加 opencode 服务，通过 attach 远程开发，并在同机调用 deployment-agent 或 docker compose 完成发布。

**同机部署详细步骤**请参见：[OpenCode同机部署实施方案](./OpenCode同机部署实施方案.md)。
