# OpenCode 本地 Web 构建与通过堡垒机上传指南

本文说明：① 在仓库内如何构建“不依赖 app.opencode.ai”的 OpenCode 镜像并部署；② 内网服务器只能通过堡垒机上传文件时，应上传哪些内容、如何上传。

---

## 一、下一步要做的事（概览）

1. **在能访问外网的机器上**（本机或 CI）：用修改过的 `opencode-src` 构建前端（`packages/app`）和 CLI，打成 **本地 Web 镜像**，导出为 tar。
2. **通过堡垒机**：把镜像 tar、compose、.env 等上传到内网服务器。
3. **在内网服务器上**：加载镜像、用新 compose 启动，访问 `http://服务器:4096/` 即可使用 Web 页面，无需访问 app.opencode.ai。

---

## 二、构建步骤（在开发机/构建机上执行）

### 2.1 环境要求

- **Docker**（用于构建 Linux 镜像；若本机是 Windows，Docker 会使用 Linux 容器）。
- 能访问外网（`bun install`、opencode build 会拉取依赖与 models snapshot）。

### 2.2 确认已包含的代码修改

仓库内 `opencode-src/packages/opencode/src/server/server.ts` 已修改为：当 `OPENCODE_SERVE_WEB_LOCAL=1` 且 `OPENCODE_WEB_ROOT` 存在时，从本机目录提供静态文件，不再代理到 app.opencode.ai。无需再改代码。

### 2.3 构建镜像

在**仓库根目录**（即 `enterprise-ai-platform`）下执行：

```bash
docker build -f opencode-src/Dockerfile.local-web -t enterprise-ai-opencode-local-web:latest opencode-src
```

- 构建过程会：在容器内安装依赖、构建 `packages/app`（前端）、构建 `packages/opencode`（CLI），并把前端产物放到镜像内 `/app-web`。
- 若失败，请检查：网络是否可访问 npm/外网、磁盘空间、Docker 是否在 Linux 模式（Windows 下默认即 Linux 容器）。
- **CPU 架构**：构建出的镜像是当前 Docker 使用的架构（多为 linux/x64）。若内网服务器是 **ARM**，需在 ARM 环境（如 ARM 机器或 ARM Docker 构建）下重新构建，或使用 x64 服务器。

### 2.4 导出镜像为 tar（便于上传）

```bash
mkdir -p opencode-server-export
docker save -o opencode-server-export/enterprise-ai-opencode-local-web.tar enterprise-ai-opencode-local-web:latest
```

之后 **opencode-server-export** 目录下会多出 `enterprise-ai-opencode-local-web.tar`，用于上传到内网。

---

## 三、需要上传到服务器的内容（通过堡垒机）

以下文件/目录需要出现在**内网服务器**上，建议统一放在 **opencode-server-export** 目录下（与现有部署方式一致）。

| 内容 | 说明 |
|------|------|
| **enterprise-ai-opencode-local-web.tar** | 上一步导出的镜像包。 |
| **docker-compose.opencode.local-web.yml** | 使用“本地 Web”镜像的 compose 文件（已在 `opencode-server-export` 内）。 |
| **.env** | 由 `.env.example` 复制并修改，至少设置 `OPENCODE_WORKSPACE`、`EXTERNAL_NETWORK_NAME`、`OPENCODE_SERVER_PASSWORD` 等。 |
| **.env.example** | 可选，便于他人复制。 |

即：把整个 **opencode-server-export** 文件夹（含上述 tar、compose、.env）上传到内网服务器，例如放到代码根目录下：`/opt/enterprise-ai-platform/opencode-server-export/`。

**之前改过的源码**（如 `opencode-src/packages/opencode/src/server/server.ts`）已经打进镜像，**不需要**再单独上传源码到服务器；只需上传镜像 tar + compose + .env 即可。

---

## 四、通过堡垒机上传文件的几种方式

假设：**你的电脑** → 堡垒机（跳板机）→ **内网服务器**；内网服务器不能直接对外，只能从堡垒机拷文件进去。

### 4.1 方式一：本机 → 堡垒机 → 内网服务器（两次 SCP）

1. 在本机把要传的内容打成一个 tar（便于只传一个文件）：
   ```bash
   cd /path/to/enterprise-ai-platform
   tar -cvf opencode-export.tar opencode-server-export/enterprise-ai-opencode-local-web.tar \
       opencode-server-export/docker-compose.opencode.local-web.yml \
       opencode-server-export/.env.example
   ```
   若已有 `.env`，可把 `opencode-server-export/.env` 一并打进 tar。

2. 上传到堡垒机（示例，按你实际用户/主机名改）：
   ```bash
   scp opencode-export.tar 堡垒机用户@堡垒机IP:/tmp/
   ```

3. 登录堡垒机，再从堡垒机传到内网服务器：
   ```bash
   ssh 堡垒机用户@堡垒机IP
   scp /tmp/opencode-export.tar 内网用户@内网服务器IP:/opt/enterprise-ai-platform/
   ```

4. 在内网服务器上解压并放到目标位置：
   ```bash
   ssh 内网用户@内网服务器IP
   cd /opt/enterprise-ai-platform
   tar -xvf opencode-export.tar
   # 若 .env 未打包，在 opencode-server-export 下 cp .env.example .env 并编辑
   ```

### 4.2 方式二：本机一条命令经堡垒机跳到内网（SCP ProxyJump）

本机可直连堡垒机、堡垒机可连内网时，可一条命令从本机传到内网服务器：

```bash
scp -o ProxyJump=堡垒机用户@堡垒机IP \
    opencode-server-export/enterprise-ai-opencode-local-web.tar \
    opencode-server-export/docker-compose.opencode.local-web.yml \
    opencode-server-export/.env.example \
    内网用户@内网服务器IP:/opt/enterprise-ai-platform/opencode-server-export/
```

需先在服务器上建好 `opencode-server-export` 目录；若已有 `.env`，可一起传 `opencode-server-export/.env`。

### 4.3 方式三：只上传镜像 tar + 说明（服务器上已有 compose/.env）

若内网服务器上已经有一份 **opencode-server-export**（含 compose、.env），只需更新镜像时：

1. 只传新镜像 tar：
   ```bash
   scp -o ProxyJump=堡垒机用户@堡垒机IP \
       opencode-server-export/enterprise-ai-opencode-local-web.tar \
       内网用户@内网服务器IP:/opt/enterprise-ai-platform/opencode-server-export/
   ```
2. 在服务器上加载并改用“本地 Web”的 compose：
   ```bash
   cd /opt/enterprise-ai-platform/opencode-server-export
   docker load -i enterprise-ai-opencode-local-web.tar
   docker compose -f docker-compose.opencode.local-web.yml --env-file .env up -d
   ```

### 4.4 上传“修改过的源码”的场合（可选）

只有在**内网要自己重新构建镜像**时，才需要把修改过的源码上传到内网，例如：

- 需要上传的目录/文件：
  - **opencode-src** 整个目录（至少包含 `packages/opencode`、`packages/app`、根目录 `package.json`、`bun.lock`、`Dockerfile.local-web` 等），或
  - 仅变更过的文件：`opencode-src/packages/opencode/src/server/server.ts`，以及为构建所需的 `opencode-src/Dockerfile.local-web`、根 `package.json`、`bun.lock` 等（若内网已有未改动的 opencode-src，可只传改动文件再覆盖）。

上传方式同上：打 tar 经堡垒机 SCP，或用 ProxyJump 一次传到内网服务器，再在内网有 Docker 的环境里执行与 2.3、2.4 相同的构建和导出步骤。

---

## 五、在内网服务器上的部署步骤

1. 进入导出目录并加载镜像：
   ```bash
   cd /opt/enterprise-ai-platform/opencode-server-export
   docker load -i enterprise-ai-opencode-local-web.tar
   ```

2. 若尚未配置 `.env`：
   ```bash
   cp .env.example .env
   # 编辑 .env，设置 OPENCODE_WORKSPACE、EXTERNAL_NETWORK_NAME、OPENCODE_SERVER_PASSWORD 等
   ```

3. 使用“本地 Web”compose 启动：
   ```bash
   docker compose -f docker-compose.opencode.local-web.yml --env-file .env up -d
   ```

4. 检查：
   ```bash
   docker compose -f docker-compose.opencode.local-web.yml ps
   docker logs -f enterprise-ai-opencode
   ```

5. 浏览器访问 **http://服务器IP:4096/** 即可使用 Web 登录与对话界面，**无需**容器访问 app.opencode.ai。

---

## 六、小结

| 项目 | 说明 |
|------|------|
| 构建位置 | 在能访问外网的机器上，于仓库根执行 `docker build -f opencode-src/Dockerfile.local-web -t enterprise-ai-opencode-local-web:latest opencode-src`，再 `docker save` 得到 tar。 |
| 必须上传 | 镜像 tar、`docker-compose.opencode.local-web.yml`、`.env`（或到服务器后从 .env.example 复制并修改）。 |
| 是否要上传源码 | 不需要。改过的 server.ts 已打进镜像。仅当在内网重新构建镜像时才上传 opencode-src（或改动文件）。 |
| 堡垒机上传 | 可用两次 SCP（本机→堡垒机→内网）、或本机 SCP ProxyJump 到内网、或只传 tar 到已有 opencode-server-export 的服务器。 |
| 服务器部署 | `docker load` → 配置 `.env` → `docker compose -f docker-compose.opencode.local-web.yml --env-file .env up -d`。 |
