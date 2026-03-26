# OpenCode Web 页面与官方部署说明

基于对 [OpenCode 源码](https://github.com/anomalyco/opencode)（仓库内 `opencode-src`）的检查，说明 Web 页面机制与正确部署方式。

---

## 一、OpenCode 确有 Web 页面（登录 + 对话框）

- 官方提供 **Web 界面**：可登录、在对话框中输入指令、管理会话等，与 TUI 能力一致。
- 启动方式：本机执行 **`opencode web`**（会打开浏览器）或 **`opencode serve`**（仅起服务，不自动打开浏览器）。两者启动的是**同一套 HTTP 服务**，区别只有是否自动打开浏览器。

---

## 二、官方实现方式：Web 页来自远程，本地只做代理

源码中（`packages/opencode/src/server/server.ts`）逻辑为：

1. **API 路由**：`/global/health`、`/doc`、`/session`、`/project` 等由本地服务直接处理。
2. **其余请求（含根路径 `/`）**：全部由本地服务**反向代理**到 **`https://app.opencode.ai`**：

```ts
.all("/*", async (c) => {
  const response = await proxy(`https://app.opencode.ai${path}`, {
    ...c.req,
    headers: { ...c.req.raw.headers, host: "app.opencode.ai" },
  })
  return response
})
```

因此：

- **Web 页面（HTML/JS/CSS）不在 CLI 包里**，而是 **app.opencode.ai** 上的前端应用。
- 本地/容器里的进程只起 **API + 代理**：浏览器访问 `http://你的服务器:4096/` 时，由该进程向 **https://app.opencode.ai/** 拉取页面并转发给浏览器；登录、对话等仍由本地 API 与同一后端配合完成。

---

## 三、按“官方方式”部署时的前提条件

要让 **http://服务器:4096/** 在浏览器里正常打开 Web 页面（登录 + 对话框），必须满足：

- **运行 OpenCode 的那台机器（例如 Docker 容器）能够访问 https://app.opencode.ai**  
  （出网或经代理均可，只要 HTTPS 能通）。

否则：

- 代理请求会一直挂起或失败；
- 浏览器会拿不到页面 → 出现 **ERR_EMPTY_RESPONSE** 或长时间无响应。

内网/无外网时：

- 若**完全无法**访问 app.opencode.ai，则 **根路径 `/` 的 Web 页面无法使用**；
- 可继续使用：**`/doc`**（API 文档）、以及在本机用 **`opencode attach --hostname 服务器IP --port 4096`** 使用 TUI（终端界面，功能与 Web 一致）。

---

## 四、推荐部署方式（与官方一致）

### 4.1 启动命令

与官方一致即可，二选一：

- **`opencode serve --hostname 0.0.0.0 --port 4096`**  
  适合无界面环境（如 Docker），不自动打开浏览器。
- **`opencode web --hostname 0.0.0.0 --port 4096`**  
  同一服务，若在有桌面的机器上会尝试自动打开浏览器。

当前 `opencode-server-export` 内 compose 已使用 **`opencode serve`**，与官方无冲突。

### 4.2 网络与权限

- 端口：对需要访问的客户端开放 **4096**。
- 若需使用 **Web 页面**：容器/主机需能访问 **https://app.opencode.ai**（可先在容器内测：  
  `docker exec enterprise-ai-opencode curl -sI https://app.opencode.ai/`）。
- 认证：设置 **`OPENCODE_SERVER_PASSWORD`**（及可选 **`OPENCODE_SERVER_USERNAME`**），与官方文档一致。

### 4.3 验证 Web 是否可用

1. 在服务器或容器内测代理是否通：
   ```bash
   docker exec enterprise-ai-opencode curl -sI -m 10 https://app.opencode.ai/
   ```
   若返回 HTTP 200 或 3xx，说明代理可到 app.opencode.ai。
2. 浏览器访问：**http://服务器IP:4096/**  
   - 能打开登录/会话页、能输入命令 → Web 页面按官方方式工作正常。
   - 若一直转圈或 ERR_EMPTY_RESPONSE → 多为到 app.opencode.ai 不可达，需解决出网或代理。

---

## 五、小结

| 项目 | 说明 |
|------|------|
| Web 页面 | 有；支持登录与在对话框中输入命令，由 **app.opencode.ai** 提供，本地只做代理。 |
| 官方部署 | 使用 **`opencode serve`** 或 **`opencode web`**，绑定 `0.0.0.0` 与端口 4096；与当前 compose 一致。 |
| 根路径 `/` 打不开的常见原因 | 运行 OpenCode 的机器（如 Docker 容器）**无法访问 https://app.opencode.ai**。 |
| 内网/无外网 | 无法用浏览器打开 `/` 时，可用 **`/doc`** + **`opencode attach`**（TUI）获得同等能力。 |

当前仓库内的 **opencode-server-export** 与 **docker-compose.opencode.yml** 已按官方方式（serve + 代理到 app.opencode.ai）配置；若需在浏览器中使用 Web 页面，只需保证容器能访问 **https://app.opencode.ai** 即可。

---

## 六、为什么一定要通过 app.opencode.ai？不通过会有什么影响？

### 6.1 设计原因：Web 前端不在 CLI 包里

- 官方 **CLI 安装包（opencode serve）里只包含服务端**：API 路由、会话、项目、LSP、认证等逻辑都在本地。
- **Web 前端（HTML/JS/CSS）没有随 CLI 分发**，而是部署在 **https://app.opencode.ai** 上。
- 因此“打开根路径 `/`”时，本地服务没有静态文件可返回，只能把请求**转交给** app.opencode.ai，由它返回页面，再经本地代理转给浏览器。

也就是说：**不是“必须通过 app.opencode.ai 才能用 Web”**，而是**官方选择把 Web 资源放在 app.opencode.ai，本地只做代理**。从架构上完全可以改为“本地自己提供静态文件”，无需该域名。

### 6.2 app.opencode.ai 实际提供什么

| 内容 | 是否依赖 app.opencode.ai |
|------|---------------------------|
| **静态资源**（`/`、`/index.html`、`/assets/*.js`、`/assets/*.css` 等） | **是**：官方默认从这里拉取并代理给浏览器。 |
| **登录 / 会话 / 对话 API**（`/session`、`/project`、`/global` 等） | **否**：全部由本地 `opencode serve` 处理。 |
| **认证（密码、Provider 等）** | **否**：存在本地，不经过 app.opencode.ai。 |
| **CORS** | **否**：服务端已对 `*.opencode.ai` 放行，但 API 调用在“浏览器 → 当前页面的 origin”下，用同源或相对路径即可。 |

前端在**非 opencode.ai 域名**下（例如 `http://你的服务器:4096`）会使用 **`window.location.origin`** 作为 API 地址（见 `packages/app/src/app.tsx`），即和当前页面同源，因此**登录与对话不依赖 app.opencode.ai**，只依赖“页面本身从哪来”。

### 6.3 不通过 app.opencode.ai 会怎样

- **不放开出网、也不做代理**，且**不改代码、不提供本地静态资源**时：
  - 浏览器访问 `http://服务器:4096/` → 本地服务把请求代理到 app.opencode.ai → **代理请求失败**（超时或连接错误）→ 浏览器得到 **ERR_EMPTY_RESPONSE** 或一直转圈。
  - 结果：**Web 页面打不开**；**/doc** 和 **opencode attach** 仍可用（它们不依赖 app.opencode.ai）。

- **若改为本地提供 Web 静态文件**（本仓库已在服务端支持）：
  - 设置 **`OPENCODE_SERVE_WEB_LOCAL=1`** 和 **`OPENCODE_WEB_ROOT=/path/to/app/dist`**，并把 `packages/app` 构建产物放到该目录、打进镜像。
  - 此时 **根路径 `/` 及所有静态资源由本地直接返回**，不再请求 app.opencode.ai，**无出网要求**，内网/离线均可使用 Web 页面。

### 6.4 小结

| 问题 | 结论 |
|------|------|
| 为什么“一定要”通过 app.opencode.ai？ | 因为官方把 Web 前端放在该域名，CLI 未内置静态资源，默认只能通过代理拉取。 |
| 不通过它会有什么影响？ | 默认配置下：根路径 `/` 会代理失败，Web 页打不开；API、认证、/doc、TUI 不受影响。 |
| 能否不依赖 app.opencode.ai？ | 可以：用本仓库的“本地 Web”逻辑（环境变量 + 自建前端产物），即可完全不访问 app.opencode.ai。 |
