#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流服务端到端一次性测试脚本

功能:
1) 自动探测工作流服务路由前缀: "", "/api", "/v1"
2) 创建一个最小工作流(2个顺序noop节点)
3) 启动该工作流的执行
4) 轮询执行状态直至完成或失败
5) 获取并打印执行事件/日志(若接口存在)
6) 输出结构化测试报告

使用:
  python scripts/workflow_e2e_test.py --base http://localhost:8002

环境变量:
  WF_BASE: 覆盖 --base 参数
  API_TOKEN: 若需要鉴权，将自动注入 Authorization: Bearer <token>

依赖: requests
  pip install requests
"""
import argparse
import os
import time
import json
from typing import Dict, Any, List, Optional, Tuple

import requests

DEFAULT_BASE = os.getenv("WF_BASE", "http://localhost:8002")
ROUTE_PREFIXES = ["", "/api", "/v1"]


def http_json(method: str, url: str, **kwargs) -> requests.Response:
    headers = kwargs.pop("headers", {}) or {}
    if "json" in kwargs and "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"
    token = os.getenv("API_TOKEN")
    if token and "Authorization" not in headers:
        headers["Authorization"] = f"Bearer {token}"
    timeout = kwargs.pop("timeout", 30)
    return requests.request(method, url, headers=headers, timeout=timeout, **kwargs)


def try_route(base: str, prefix: str) -> bool:
    url = f"{base}{prefix}/workflows"
    try:
        resp = http_json("GET", url)
        if resp.status_code in (200, 204):
            return True
        # 某些实现返回 200 带空数据或包装对象
        if resp.status_code == 200:
            return True
    except Exception:
        pass
    return False


def detect_prefix(base: str) -> str:
    for p in ROUTE_PREFIXES:
        if try_route(base, p):
            return p
    # 即使 GET 失败，很多服务仍允许 POST 创建，最后返回默认空前缀
    return ""


def create_workflow(base: str, prefix: str) -> Dict[str, Any]:
    url = f"{base}{prefix}/workflows"
    payload = {
        "name": "test_simple_flow",
        "description": "E2E test: noop chain",
        "nodes": [
            {"id": "n1", "type": "noop", "name": "Start"},
            {"id": "n2", "type": "noop", "name": "Second", "depends_on": ["n1"]},
        ],
        "edges": [
            {"from": "n1", "to": "n2"}
        ]
    }
    resp = http_json("POST", url, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def start_execution(base: str, prefix: str, workflow_id: str) -> Dict[str, Any]:
    url = f"{base}{prefix}/workflows/{workflow_id}/start"
    resp = http_json("POST", url, json={}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_execution(base: str, prefix: str, execution_id: str) -> Dict[str, Any]:
    url = f"{base}{prefix}/workflow-executions/{execution_id}"
    resp = http_json("GET", url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_events(base: str, prefix: str, execution_id: str) -> Optional[List[Dict[str, Any]]]:
    # 优先尝试 /events，其次 /logs
    for tail in ("events", "logs"):
        url = f"{base}{prefix}/workflow-executions/{execution_id}/{tail}"
        try:
            resp = http_json("GET", url, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    # ��见包装格式
                    arr = data.get("events") or data.get("logs") or data.get("data")
                    if isinstance(arr, list):
                        return arr
        except Exception:
            continue
    return None


def extract_id(resp_json: Dict[str, Any], *keys: str) -> Optional[str]:
    for k in keys:
        v = resp_json.get(k)
        if v:
            return str(v)
    # 常见包装 {data: {id: ...}}
    data = resp_json.get("data")
    if isinstance(data, dict):
        for k in keys:
            v = data.get(k)
            if v:
                return str(v)
    return None


def wait_for_completion(base: str, prefix: str, execution_id: str, timeout_sec: int = 600, interval: float = 2.0) -> Tuple[str, Dict[str, Any]]:
    start = time.time()
    last = {}
    terminal = {"succeeded", "finished", "completed", "failed", "error", "timeout", "cancelled"}
    while time.time() - start < timeout_sec:
        try:
            ex = get_execution(base, prefix, execution_id)
            last = ex
            status = str(ex.get("status") or ex.get("state") or ex.get("data", {}).get("status") or "unknown").lower()
            if status in terminal:
                return status, ex
        except Exception as e:
            last = {"error": str(e)}
        time.sleep(interval)
    return "timeout", last


def main():
    parser = argparse.ArgumentParser(description="Workflow service E2E one-shot test")
    parser.add_argument("--base", default=DEFAULT_BASE, help="工作流服务基地址，默认 http://localhost:8002 或 WF_BASE 环境变量")
    args = parser.parse_args()

    base = args.base.rstrip("/")

    print("=== 探测路由前缀 ===")
    prefix = detect_prefix(base)
    print(f"使用前缀: '{prefix or '/'}'")

    print("\n=== 创建最小工作流 ===")
    try:
        wj = create_workflow(base, prefix)
        workflow_id = extract_id(wj, "id", "workflow_id")
        print("创建响应:", json.dumps(wj, ensure_ascii=False))
        if not workflow_id:
            raise RuntimeError("无法解析 workflow_id")
        print(f"workflow_id = {workflow_id}")
    except Exception as e:
        print(f"[ERROR] 创建工作流失败: {e}")
        return 1

    print("\n=== 启动执行 ===")
    try:
        sj = start_execution(base, prefix, workflow_id)
        execution_id = extract_id(sj, "execution_id", "id")
        print("启动响应:", json.dumps(sj, ensure_ascii=False))
        if not execution_id:
            raise RuntimeError("无法解析 execution_id")
        print(f"execution_id = {execution_id}")
    except Exception as e:
        print(f"[ERROR] 启动执行失败: {e}")
        return 2

    print("\n=== ��询状态 ===")
    status, ex = wait_for_completion(base, prefix, execution_id, timeout_sec=600, interval=2.0)
    print(f"最终状态: {status}")
    print("执行详情:", json.dumps(ex, ensure_ascii=False))

    print("\n=== 获取事件/日志(若可用) ===")
    events = get_events(base, prefix, execution_id)
    if events is not None:
        print(f"事件/日志条数: {len(events)}")
        sample = events[:5]
        print("示例:", json.dumps(sample, ensure_ascii=False))
    else:
        print("无事件/日志接口或未返回数据")

    print("\n=== 测试报告 ===")
    report = {
        "base": base,
        "prefix": prefix,
        "workflow_id": workflow_id,
        "execution_id": execution_id,
        "final_status": status,
        "has_events": events is not None,
        "timestamp": int(time.time()),
    }
    print(json.dumps(report, ensure_ascii=False))

    # 以退出码指示成功/失败
    if status in {"succeeded", "finished", "completed"}:
        return 0
    return 3


if __name__ == "__main__":
    exit(main())
