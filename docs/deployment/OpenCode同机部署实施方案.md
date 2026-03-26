# OpenCode 同机部署实施方案（与 19 服务同一台服务器）

本文档描述在**已部署 19 个服务的同一台服务器**上部署 OpenCode，实现“改代码 → 同机发布到指定应用服务”的完整流程。

---

## 一、目标与前提

| 项目 | 说明 |
|------|------|
| **目标** | 在同一台服务器上运行 OpenCode，管理并编辑 19 服务代码，编写完成后直接发布到本机某个应用（如 project-management） |
| **前提** | 该服务器已用 docker-compose 跑起 19 服务，且项目根目录可挂载给 OpenCode 使用 |
| **交互方式** | OpenCode 以无头 HTTP 服务（`opencode serve`）运行；用户从本机或其它机器用 `opencode attach` 或浏览器（`opencode web`）连接 |

---

## 二、架构示意

```
                    同一台服务器
┌─────────────────────────────────────────────────────────────────────────┐
│  docker-compose (enterprise-ai-network)                                  │
│                                                                         │
│  ┌──────────────┐   ┌─────────────────────┐   ┌─────────────────────┐ │
│  │  opencode    │   │  deployment-agent   │   │  19 业务服务          │ │
│  │  :4096       │──▶│  :8000 (内网)       │──▶│  api-gateway,        │ │
│  │  工作目录     │   │  POST /api/v1/deploy │   │  project-management  │ │
│  │  /workspace  │   └─────────────────────┘   │  等                   │ │
│  │  = 仓库根    │           或                 └─────────────────────┘ │
│  └──────┬───────┘    同机 docker compose                               │
│         │             build/up 指定服务                                  │
│         │                                                                 │
│  volumes: .:/workspace（与宿主机同一份代码）                              │
└─────────┼───────────────────────────────────────────────────────────────┘
          │
          │  attach / web (端口 4096)
          ▼
┌─────────────────────┐
│  开发者本机/其他机器  │
│  opencode attach    │
│  或 opencode web    │
└─────────────────────┘
```

---

## 三、实施步骤

### 步骤 1：准备 OpenCode 镜像与 Compose 配置

#### 1.1 使用项目内 Dockerfile（推荐）

仓库中已提供 `opencode/Dockerfile`，基于 Node 安装 `opencode-ai` 并以 `opencode serve` 启动：

```bash
# 在项目根目录
docker compose build opencode
```

#### 1.2 将 OpenCode 服务加入 docker-compose

在 `docker-compose.yml` 的 `services` 下（紧挨在 `deployment-agent` 之后、`volumes` 之前）加入以下片段（若已通过“步骤 2”的合并方式添加则可跳过）：

```yaml
  # OpenCode - 与 19 服务同机，用于管理与发布（可选）
  opencode:
    profiles:
      - optional
    build:
      context: ./opencode
      dockerfile: Dockerfile
    image: enterprise-ai-opencode:latest
    container_name: enterprise-ai-opencode
    working_dir: /workspace
    command: opencode serve --hostname 0.0.0.0 --port 4096
    ports:
      - "${OPENCODE_PORT:-4096}:4096"
    environment:
      - OPENCODE_SERVER_USERNAME=${OPENCODE_SERVER_USERNAME:-opencode}
      - OPENCODE_SERVER_PASSWORD=${OPENCODE_SERVER_PASSWORD:-}
    volumes:
      - .:/workspace:cached
    networks:
      - enterprise-ai-network
    restart: unless-stopped
```

说明：

- `profiles: optional`：默认 `docker compose up -d` 不会启动 OpenCode，需要时用 `docker compose --profile optional up -d opencode`。
- `.:/workspace`：仓库根目录挂载到容器内 `/workspace`，在 OpenCode 里改的就是宿主机上的代码，与 19 服务挂载一致。
- 端口 4096 可通过 `OPENCODE_PORT` 修改。

---

### 步骤 2：配置环境变量（可选但建议）

在项目根目录的 `.env` 或 `.env.example` 中增加：

```bash
# OpenCode 同机服务（可选）
OPENCODE_PORT=4096
OPENCODE_SERVER_USERNAME=opencode
OPENCODE_SERVER_PASSWORD=你的强密码
```

设置 `OPENCODE_SERVER_PASSWORD` 后，连接 OpenCode 时需使用该密码，避免未授权访问。

---

### 步骤 3：启动 OpenCode 服务

在**同一台服务器**上，进入项目根目录执行：

```bash
# 仅构建并启动 OpenCode（不启动其他 optional 服务）
docker compose --profile optional build opencode
docker compose --profile optional up -d opencode

# 查看日志确认已监听 4096
docker compose logs -f opencode
```

见到类似 “Listening on 0.0.0.0:4096” 即可。

若希望与 deployment-agent 一起启动（用于通过 API 发布）：

```bash
docker compose --profile optional up -d opencode deployment-agent
```

---

### 步骤 3.1：内网服务器无法构建时（本地构建 → 打包镜像 → 上传）

服务器在内网、无法访问外网构建时，在**能构建的本地环境**完成构建与打包，将**单个文件夹**上传到服务器即可。

#### 本地执行（一次）

在项目根目录执行：

```bash
# Windows PowerShell
.\scripts\export-opencode-for-server.ps1

# Linux/macOS
./scripts/export-opencode-for-server.sh
```

脚本会：1）在本地 Docker 中构建 `enterprise-ai-opencode:latest`；2）将镜像导出为 `.tar`；3）将镜像与部署所需文件放入 **`opencode-server-export/`** 文件夹。

#### 导出文件夹内容（需上传到服务器的全部文件）

| 文件/目录 | 说明 |
|----------|------|
| `enterprise-ai-opencode.tar` | 构建好的镜像包（由脚本生成） |
| `docker-compose.opencode.yml` | 仅含 OpenCode 的 compose，使用外部网络 `enterprise-ai-network` |
| `.env.example` | 环境变量示例，复制为 `.env` 后填写 `OPENCODE_WORKSPACE` |
| `服务器启动说明.txt` | 服务器上的操作步骤 |
| `load-and-run.sh` / `load-and-run.ps1` | 加载镜像并启动的脚本 |

将 **整个 `opencode-server-export` 文件夹** 上传到内网服务器（例如放到项目根目录下），在服务器上按该文件夹内的 **服务器启动说明.txt** 执行：加载镜像、配置 `.env`、启动服务。

---

### 步骤 4：从本机或其它机器连接 OpenCode

在**你的开发机**（可与服务器不同）上安装 OpenCode 后连接：

```bash
# 安装（若未安装）
npm i -g opencode-ai@latest

# 连接同机服务器上的 OpenCode（替换为实际服务器 IP 或主机名）
opencode attach --hostname <服务器IP> --port 4096
```

若设置了 `OPENCODE_SERVER_PASSWORD`，连接时会提示输入用户名/密码（默认用户名 `opencode`）。

**或使用 Web 界面**（在服务器上执行，或本机做 SSH 端口转发后访问）：

```bash
# 在服务器上（或本机转发 4096 后）
opencode web --hostname 0.0.0.0 --port 4096
```

本机转发示例：

```bash
ssh -L 4096:127.0.0.1:4096 user@<服务器IP>
# 然后浏览器访问 http://localhost:4096
```

连接成功后，当前项目即为服务器上的 `/workspace`，即本仓库根目录，可直接浏览和编辑 19 个服务的代码。

---

### 步骤 5：在 OpenCode 中编写功能并发布到本机某服务

#### 5.1 编辑代码

在 OpenCode 中打开对应服务目录进行修改，例如：

- 项目管理：`/workspace/project_management/src/`
- API 网关：`/workspace/api-gateway/src/`
- 其他服务：见 `docker-compose.yml` 中各服务的 `context` 与挂载路径。

保存后，宿主机上文件已更新；若该服务使用了源码卷挂载（如 `./project_management/src:/app/src`），部分服务可能已热重载，否则需按 5.2 发布一次。

#### 5.2 发布到本机指定服务

**方式 A：通过 deployment-agent API（推荐，同机网络）**

若已启动 `deployment-agent`，在 OpenCode 的 Shell 中执行：

```bash
# 发布项目管理服务
curl -X POST "http://deployment-agent:8000/api/v1/deploy" \
  -H "Content-Type: application/json" \
  -d '{"services":["project-management"],"skip_data_sync":true,"skip_migration":false}'
```

或使用仓库内脚本（脚本内需指向同机 deployment-agent）：

```bash
export DEPLOYMENT_AGENT_URL=http://deployment-agent:8000
./scripts/deployment/deploy-one-service.sh project-management
```

注意：在 OpenCode 容器内，`deployment-agent` 为同一 docker 网络中的服务名，端口为 8000（容器内端口）。

**方式 B：在宿主机上执行 docker compose（不依赖 deployment-agent）**

若未使用 deployment-agent，可在**服务器本机** SSH 登录后执行：

```bash
cd /path/to/enterprise-ai-platform
docker compose build project-management
docker compose up -d project-management
```

也可在 OpenCode 的 Shell 中通过“在宿主机执行命令”的脚本封装上述两条（例如通过 SSH localhost 或宿主机提供的轻量 API），按你们现有运维习惯即可。

---

### 步骤 6：同机发布脚本封装（可选）

为在 OpenCode 内“一句话发布”，可在仓库中增加一个**仅同机使用**的脚本，供 OpenCode 调用。例如 `scripts/deployment/deploy-one-service-same-host.sh`：

```bash
#!/usr/bin/env bash
# 同机部署：在 OpenCode 容器内调用 deployment-agent 发布指定服务
SERVICE_NAME="${1:?用法: $0 <服务名>}"
DEPLOYMENT_AGENT_URL="${DEPLOYMENT_AGENT_URL:-http://deployment-agent:8000}"
curl -s -X POST "$DEPLOYMENT_AGENT_URL/api/v1/deploy" \
  -H "Content-Type: application/json" \
  -d "{\"services\":[\"$SERVICE_NAME\"],\"skip_data_sync\":true,\"skip_migration\":false}"
```

在 OpenCode 中即可说：“请发布项目管理服务：执行 `./scripts/deployment/deploy-one-service-same-host.sh project-management`”。

---

## 四、服务名与端口速查

| 用途           | 服务/端口说明 |
|----------------|----------------|
| OpenCode 连接  | 宿主机 `OPENCODE_PORT`（默认 4096） |
| deployment-agent（容器内） | `http://deployment-agent:8000` |
| 常用应用服务名 | `project-management`、`api-gateway`、`workflow-engine`、`auth-service`、`web-ui` 等（与 docker-compose 中 `services` 名一致） |

---

## 五、安全与运维建议

1. **务必设置密码**：同机暴露 4096 端口时，必须设置 `OPENCODE_SERVER_PASSWORD`，避免未授权使用。
2. **端口暴露范围**：若仅允许本机或内网访问，可在 `ports` 中写为 `127.0.0.1:4096:4096`，再通过 SSH 转发从外网连接。
3. **资源**：OpenCode 与 19 服务共享 CPU/内存，若服务器资源紧张，可仅在需要时 `docker compose --profile optional up -d opencode`，用完可 `stop`。
4. **代码与发布**：发布前建议在 OpenCode 内执行 `git status` / `git diff` 确认变更；若需“仅允许已提交代码部署”，可在部署脚本或 CI 中加校验。

---

## 六、从 Git 拉取 OpenCode 到本地

若需在本地保留 OpenCode 源码（二次开发、或不用 Docker 时从源码运行），可从官方仓库克隆到本地。

### 6.1 克隆仓库

```bash
# 克隆到当前目录下的 opencode-src（与 enterprise-ai-platform 同级或任意目录均可）
git clone https://github.com/anomalyco/opencode.git opencode-src
cd opencode-src

# 使用 dev 分支（与官方最新开发一致）
git checkout dev

# 后续更新
git pull origin dev
```

也可使用项目内提供的脚本（会克隆到脚本所在目录的上级的 `opencode-src`）：

```bash
# Linux/macOS
./scripts/clone-opencode.sh

# Windows PowerShell
.\scripts\clone-opencode.ps1
```

### 6.2 克隆后从源码运行（可选）

OpenCode 使用 Node/Bun，克隆后可在本地安装依赖并启动 serve：

```bash
cd opencode-src
bun install   # 或 npm install
bun run cli serve --hostname 0.0.0.0 --port 4096   # 或 npx opencode-ai serve ...
```

详见 [OpenCode 官方仓库](https://github.com/anomalyco/opencode) 的 README 与文档。

---

## 七、故障排查

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| attach 连不上 | 防火墙/安全组未放行 4096 | 放行端口或改用 127.0.0.1 + SSH 转发 |
| 容器内 curl deployment-agent 超时 | deployment-agent 未启动或未用 optional profile | `docker compose --profile optional up -d deployment-agent` |
| 修改代码后服务未更新 | 该服务未做卷挂载或未触发重建 | 按 5.2 执行 build/up 或通过 deployment-agent 部署 |
| OpenCode 容器启动失败 | 镜像构建失败或端口占用 | `docker compose build opencode --no-cache`，检查 4096 是否被占用 |

---

## 八、总结

- **同机部署**：在同一台服务器上以 Docker 服务形式运行 OpenCode（`opencode serve`），与 19 服务共用同一份代码挂载（`.:/workspace`）。
- **连接方式**：从本机或其它机器使用 `opencode attach` 或 `opencode web` + 端口 4096 连接。
- **发布方式**：在 OpenCode 内通过调用同机 `deployment-agent` 的 `/api/v1/deploy`，或在本机执行 `docker compose build/up` 指定服务，实现“编写完成后直接发布到本机某应用服务”。

按上述步骤即可完成 OpenCode 与 19 服务的同机部署与发布闭环。
