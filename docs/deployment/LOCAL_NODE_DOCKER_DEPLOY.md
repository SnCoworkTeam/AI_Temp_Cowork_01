# 本地部署（前端 Node + 后端 Docker）

## 目标

- 前端：本机 Node 启动（`web-ui`）
- 后端：本机 Docker 启动（`docker-compose`）
- 主后端容器名：`AI_TEMP_COWORK-MAIN`（对应 `api-gateway`）

## 一键启动

在项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\deployment\start-local.ps1
```

## 启动逻辑

脚本会自动执行：

1. 检查并处理旧容器 `ai_template_lyb_20260305`（重命名为 `AI_TEMP_COWORK-MAIN-legacy`）
2. 通过 `docker-compose.yml + docker-compose.local.yml` 启动后端
3. 校验主后端容器 `AI_TEMP_COWORK-MAIN`
4. 复制 `web-ui/.env.local.example` 到 `web-ui/.env.local`（如不存在）
5. 新开终端启动前端 `npm run dev`

## 手动启动（可选）

### 仅启动后端

```powershell
docker compose -f .\docker-compose.yml -f .\docker-compose.local.yml up -d --build
```

### 单独启动前端

```powershell
cd .\web-ui
if (!(Test-Path node_modules)) { npm install }
npm run dev
```
