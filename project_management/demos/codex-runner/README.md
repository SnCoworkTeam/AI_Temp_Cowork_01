# Codex Runner

在**已安装 Codex CLI 的服务器**上运行本服务，供企业 AI 平台门户中的「Codex CLI」页面调用。

## 依赖

- Python 3.10+
- 已按 [Codex-CLI-内网离线安装与门户集成](../../../docs/deployment/Codex-CLI-内网离线安装与门户集成.md) 安装并配置好 `codex`（且在 `PATH` 中或设置 `CODEX_BIN`）
- `pip install fastapi uvicorn pydantic`

## 运行

```bash
# 在安装 codex 的机器上
cd project_management/demos/codex-runner
pip install fastapi uvicorn pydantic
uvicorn main:app --host 0.0.0.0 --port 8321
```

可选环境变量：

- `CODEX_BIN`：codex 可执行文件路径或命令名（默认 `codex`）
- 内网大模型所需的 API Key 等，通过当前环境变量传入，会传给 codex 子进程

## 与门户对接

1. 确保内网能访问本服务（例如 `http://<本机IP>:8321`）。
2. 在 Web UI 或编排中配置：
   - `CODEX_RUNNER_URL=http://<本机IP>:8321`
3. 门户中打开「Codex CLI」，输入任务描述并执行即可。

## API

- `GET /health`：健康检查，可检测本机是否找到 codex。
- `POST /run`：执行 codex。请求体 `{ "prompt": "任务描述", "cwd": "/可选/工作目录" }`，返回 `{ "stdout", "stderr", "exit_code" }`。

## 说明

当前默认使用 `codex "<prompt>"` 并可选 `-C <cwd>` 调用。若您使用的 Codex CLI（如 Rust 重写版）需不同参数，可修改 `main.py` 中 `args` 的构建方式。
