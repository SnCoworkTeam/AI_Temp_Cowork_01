#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Gateway 知识库上传与检索端到端测试脚本

功能:
1) 获取或创建知识库
2) 通过 API 网关上传本地文件 (multipart/form-data)
3) 可选轮询处理状态（如果返回 job_id 且提供任务查询接口）
4) 校验文档是否入库 (列表/可选详情)
5) 执行多条检索并输出命中来源与相似度

使用示例:
  python scripts/kb_gateway_upload_and_search.py \
    --file "demo_knowledge/F5业务蓝图报告_TJJ_MM_v1.3.docx" \
    --kb "test_kb" \
    --gateway "http://43.143.139.197:8080"

依赖: requests
  pip install requests
"""
import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

import requests

DEFAULT_GATEWAY = os.getenv("API_GATEWAY_URL", "http://43.143.139.197:8080")


def http_json(method: str, url: str, **kwargs) -> requests.Response:
    headers = kwargs.pop("headers", {}) or {}
    if "json" in kwargs and "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"
    # 可选鉴权: 从环境变量注入
    token = os.getenv("API_TOKEN")
    if token and "Authorization" not in headers:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(method, url, headers=headers, timeout=kwargs.pop("timeout", 30), **kwargs)


def get_kbs(base: str) -> List[Dict[str, Any]]:
    # 兼容两种返回格式: list 或 {knowledge_bases: [...]} / {data: [...]}
    url = f"{base}/api/knowledge/knowledge-bases"
    resp = http_json("GET", url)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("knowledge_bases"), list):
            return data["knowledge_bases"]
        if isinstance(data.get("data"), list):
            return data["data"]
    return []


def create_kb(base: str, name: str, description: str = "") -> Dict[str, Any]:
    url = f"{base}/api/knowledge/knowledge-bases"
    payload = {"name": name, "description": description or f"created by kb_gateway_upload_and_search"}
    resp = http_json("POST", url, json=payload)
    resp.raise_for_status()
    return resp.json()


def ensure_kb(base: str, kb_identifier: str) -> str:
    kbs = get_kbs(base)
    # kb_identifier 可匹配 name 或 id
    for kb in kbs:
        if str(kb.get("id")) == kb_identifier or kb.get("name") == kb_identifier:
            return str(kb.get("id"))
    # 不存在则创建
    created = create_kb(base, kb_identifier, "gateway upload test")
    return str(created.get("id") or created.get("kb_id") or created.get("data", {}).get("id"))


def upload_document(base: str, kb_id: str, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    # 首选路由: /api/knowledge/knowledge-bases/{kb_id}/documents/upload
    url_primary = f"{base}/api/knowledge/knowledge-bases/{kb_id}/documents/upload"
    files = {
        "file": (os.path.basename(file_path), open(file_path, "rb"), "application/octet-stream"),
    }
    data = {}
    if metadata:
        # 以单独字段传递 metadata_json，兼容多数实现
        data["metadata"] = json.dumps(metadata, ensure_ascii=False)
    try:
        resp = requests.post(url_primary, files=files, data=data, timeout=120)
        if resp.status_code in (200, 201):
            return resp.json()
        # 兜底: 尝试备用路由 /api/knowledge/documents/upload?knowledge_base_id=
        url_fallback = f"{base}/api/knowledge/documents/upload?knowledge_base_id={kb_id}"
        files["file"][1].seek(0)
        resp2 = requests.post(url_fallback, files=files, data=data, timeout=120)
        resp2.raise_for_status()
        return resp2.json()
    finally:
        try:
            files["file"][1].close()
        except Exception:
            pass


def get_job_status(base: str, job_id: str) -> Optional[Dict[str, Any]]:
    # 如果没有该接口会 404，调用方需容错
    url = f"{base}/api/knowledge/jobs/{job_id}"
    resp = http_json("GET", url)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def wait_job(base: str, job_id: str, timeout_sec: int = 300, interval: float = 2.0) -> str:
    start = time.time()
    last_status = "unknown"
    while time.time() - start < timeout_sec:
        js = get_job_status(base, job_id)
        if not js:
            # 无任务接口，直接返回 unknown
            return "unknown"
        status = str(js.get("status") or js.get("state") or js.get("data", {}).get("status") or "unknown")
        last_status = status
        if status.lower() in ("succeeded", "success", "finished", "completed", "done"):
            return status
        if status.lower() in ("failed", "error", "timeout"):
            raise RuntimeError(f"Job {job_id} failed with status={status}")
        time.sleep(interval)
    return last_status


def list_documents(base: str, page: int = 1, page_size: int = 10) -> List[Dict[str, Any]]:
    url = f"{base}/api/knowledge/documents?page={page}&page_size={page_size}"
    resp = http_json("GET", url)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("documents"), list):
            return data["documents"]
        if isinstance(data.get("data"), list):
            return data["data"]
    return []


def search(base: str, kb_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    # 首选: /api/knowledge/search
    url_primary = f"{base}/api/knowledge/search"
    payload = {"knowledge_base_id": kb_id, "query": query, "top_k": top_k}
    resp = http_json("POST", url_primary, json=payload)
    if resp.status_code == 404:
        # 兜底: /api/knowledge/semantic-search
        url_fallback = f"{base}/api/knowledge/semantic-search"
        resp = http_json("POST", url_fallback, json=payload)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("results") or data.get("data") or []
    return []


def main():
    parser = argparse.ArgumentParser(description="API Gateway KB upload and search E2E test")
    parser.add_argument("--file", required=True, help="要上传的本地文件路径")
    parser.add_argument("--kb", required=True, help="知识库标识（可为名称或ID，不存在则自动创建）")
    parser.add_argument("--gateway", default=DEFAULT_GATEWAY, help="API Gateway 基地址，默认从 API_GATEWAY_URL 或 http://43.143.139.197:8080")
    parser.add_argument("--no-wait", action="store_true", help="不等待处理任务完成")
    parser.add_argument("--top-k", type=int, default=5, help="检索返回条数")
    args = parser.parse_args()

    base = args.gateway.rstrip("/")
    file_path = args.file

    if not os.path.exists(file_path):
        print(f"[ERROR] 文件不存在: {file_path}")
        sys.exit(1)

    print("=== 1) 获取/创建知识库 ===")
    kb_id = ensure_kb(base, args.kb)
    if not kb_id:
        print("[ERROR] 无法获取或创建知识库ID")
        sys.exit(2)
    print(f"KB ID: {kb_id}")

    print("\n=== 2) 上传文档 ===")
    metadata = {"source": "gateway-upload-test", "doc_type": "blueprint", "module": "MM"}
    try:
        up = upload_document(base, kb_id, file_path, metadata)
    except Exception as e:
        print(f"[ERROR] 上传失败: {e}")
        sys.exit(3)
    print("上传响应:", json.dumps(up, ensure_ascii=False))

    job_id = str(up.get("job_id") or up.get("task_id") or up.get("jobId") or "").strip()
    doc_id = str(up.get("document_id") or up.get("doc_id") or up.get("id") or "").strip()

    if job_id and not args.no_wait:
        print("\n=== 3) 轮询处理任务 ===")
        try:
            status = wait_job(base, job_id, timeout_sec=600, interval=2.5)
            print(f"任务完成: status={status}")
        except Exception as e:
            print(f"[WARN] 任务状态异常: {e}，继续进行列表与检索验证…")

    print("\n=== 4) 文档列表验证 ===")
    try:
        docs = list_documents(base, page=1, page_size=20)
        print(f"文档列表数量: {len(docs)}")
        # 尝试在列表中查找刚上传的文档
        hits = []
        base_name = os.path.basename(file_path)
        for d in docs:
            title = (d.get("title") or d.get("file_name") or d.get("name") or "").lower()
            if base_name.lower() in title or (doc_id and str(d.get("id")) == doc_id):
                hits.append(d)
        print(f"列表命中 {len(hits)} 条，示例: {json.dumps(hits[:1], ensure_ascii=False)}")
    except Exception as e:
        print(f"[WARN] 文档列表验证失败: {e}")

    print("\n=== 5) 检索验证 ===")
    queries = [
        "物料管理总体业务解决方案",
        "启用批次管理专题方案",
        "采购寻源流程",
    ]
    for q in queries:
        try:
            results = search(base, kb_id, q, top_k=args.top_k)
            print(f"\nQuery: {q}")
            print(f"Results: {len(results)}")
            for i, r in enumerate(results[:args.top_k], 1):
                text = r.get("text") or r.get("snippet") or r.get("content") or ""
                doc = r.get("document_id") or r.get("doc_id") or r.get("source_id") or r.get("document", {}).get("id")
                score = r.get("score") or r.get("similarity")
                print(f"  {i}. score={score} doc_id={doc} text={text[:120].replace('\n', ' ')}…")
        except Exception as e:
            print(f"  [WARN] 检索失败: {e}")

    print("\n=== 完成 ===")


if __name__ == "__main__":
    main()
