"""
Codex Runner - 在安装 codex 的服务器上运行，接收 HTTP 请求并调用 codex 子进程。
部署后由门户 /api/codex/run 通过 CODEX_RUNNER_URL 转发请求到此服务。

用法：
  uvicorn main:app --host 0.0.0.0 --port 8321
或：
  python -m uvicorn main:app --host 0.0.0.0 --port 8321
"""

import os
import shutil
import subprocess
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Codex Runner", description="调用本机 codex CLI，供门户 /api/codex/run 转发")

CODEX_BIN = os.environ.get("CODEX_BIN", "codex")


class RunRequest(BaseModel):
    prompt: str
    cwd: str | None = None


class RunResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int


def find_codex() -> str:
    if os.path.isfile(CODEX_BIN) and os.access(CODEX_BIN, os.X_OK):
        return CODEX_BIN
    path = shutil.which(CODEX_BIN)
    if path:
        return path
    raise FileNotFoundError(f"未找到 codex 可执行文件，请安装 Codex CLI 或设置 CODEX_BIN 环境变量。当前 CODEX_BIN={CODEX_BIN!r}")


@app.get("/health")
def health():
    try:
        find_codex()
        return {"status": "ok", "codex": "found"}
    except FileNotFoundError as e:
        return {"status": "degraded", "error": str(e)}


@app.post("/run", response_model=RunResponse)
def run(req: RunRequest):
    prompt = (req.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt 不能为空")

    try:
        codex_path = find_codex()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    cwd = None
    if req.cwd and req.cwd.strip():
        p = Path(req.cwd.strip()).resolve()
        if not p.is_dir():
            raise HTTPException(status_code=400, detail=f"工作目录不存在或不是目录: {p}")
        cwd = str(p)

    # 仅传递 prompt 与工作目录，避免命令注入；不传 shell，使用列表参数
    # 多数 Codex CLI 支持 -C / --cd 指定工作目录
    args = [codex_path]
    if cwd:
        args.extend(["-C", cwd])
    args.append(prompt)
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=cwd,
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="codex 执行超时（300s）")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行 codex 失败: {e}")

    return RunResponse(
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
        exit_code=proc.returncode,
    )
