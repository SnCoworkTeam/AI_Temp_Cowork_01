#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步BPMN工作流到服务器

功能:
1. 读取本地BPMN文件
2. 上传到服务器解析
3. 保存到数据库

使用:
  python scripts/sync_bpmn_to_server.py --bpmn workflow-engine/bpmn/procure_to_pay.bpmn --server http://43.143.139.197:8080

环境变量:
  API_GATEWAY_URL: 覆盖 --server 参数
  API_TOKEN: 若需要鉴权，将自动注入 Authorization: Bearer <token>
"""
import argparse
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

import requests

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

DEFAULT_SERVER = os.getenv("API_GATEWAY_URL", "http://43.143.139.197:8080")


def http_json(method: str, url: str, **kwargs) -> requests.Response:
    """发送HTTP请求，自动添加认证头"""
    headers = kwargs.pop("headers", {}) or {}
    if "json" in kwargs and "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"
    token = os.getenv("API_TOKEN")
    if token and "Authorization" not in headers:
        headers["Authorization"] = f"Bearer {token}"
    timeout = kwargs.pop("timeout", 60)
    return requests.request(method, url, headers=headers, timeout=timeout, **kwargs)


def upload_bpmn(server: str, bpmn_file: Path) -> Dict[str, Any]:
    """上传BPMN文件并解析"""
    url = f"{server}/api/v1/bpmn/upload"
    
    print(f"📤 上传BPMN文件: {bpmn_file.name}")
    print(f"   目标URL: {url}")
    
    with open(bpmn_file, 'rb') as f:
        files = {'file': (bpmn_file.name, f, 'application/xml')}
        resp = requests.post(url, files=files, timeout=120)
    
    resp.raise_for_status()
    workflow_def = resp.json()
    
    print(f"✅ BPMN解析成功")
    print(f"   工作流名称: {workflow_def.get('name', 'N/A')}")
    print(f"   节点数量: {len(workflow_def.get('nodes', []))}")
    print(f"   连接数量: {len(workflow_def.get('connections', []))}")
    
    return workflow_def


def save_workflow(server: str, workflow_def: Dict[str, Any], overwrite: bool = True) -> Dict[str, Any]:
    """保存工作流到数据库"""
    # 尝试多个可能的API路径
    api_paths = [
        f"{server}/api/workflows",  # API Gateway代理路径
        f"{server}/api/v1/workflows",  # 带版本号的路径
    ]
    
    # 准备保存请求体（根据WorkflowSaveRequest格式）
    payload = {
        "workflow": {
            "name": workflow_def.get("name"),
            "description": workflow_def.get("description", ""),
            "version": workflow_def.get("version", "1.0.0"),
            "nodes": workflow_def.get("nodes", []),
            "connections": workflow_def.get("connections", []),
            "start_node_id": workflow_def.get("start_node_id"),
            "end_node_ids": workflow_def.get("end_node_ids", []),
            "variables": workflow_def.get("variables", {}),
            "metadata": workflow_def.get("metadata", {}),
        },
        "overwrite": overwrite
    }
    
    print(f"\n💾 保存工作流到数据库...")
    print(f"   工作流名称: {payload['workflow']['name']}")
    print(f"   覆盖已存在: {overwrite}")
    
    # 尝试每个API路径
    last_error = None
    for url in api_paths:
        try:
            print(f"   尝试URL: {url}")
            resp = http_json("POST", url, json=payload, timeout=120)
            
            if resp.status_code == 200 or resp.status_code == 201:
                result = resp.json()
                print(f"✅ 工作流保存成功")
                workflow_id = result.get("workflow_id") or result.get("id") or result.get("data", {}).get("workflow_id")
                if workflow_id:
                    print(f"   工作流ID: {workflow_id}")
                return result
            else:
                print(f"   HTTP {resp.status_code}: {resp.text[:200]}")
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
        except Exception as e:
            print(f"   错误: {e}")
            last_error = str(e)
            continue
    
    # 如果所有路径都失败，抛出错误
    print(f"❌ 所有API路径都失败")
    if last_error:
        raise Exception(f"保存失败: {last_error}")
    raise Exception("保存失败: 无法连接到服务器")


def check_workflow_exists(server: str, workflow_name: str) -> Optional[str]:
    """检查工作流是否已存在"""
    url = f"{server}/api/workflows"
    
    try:
        resp = http_json("GET", url, timeout=30)
        if resp.status_code == 200:
            workflows = resp.json()
            # 处理不同的响应格式
            if isinstance(workflows, list):
                for wf in workflows:
                    if wf.get("name") == workflow_name:
                        return wf.get("id") or wf.get("workflow_id")
            elif isinstance(workflows, dict):
                data = workflows.get("data", workflows.get("workflows", []))
                if isinstance(data, list):
                    for wf in data:
                        if wf.get("name") == workflow_name:
                            return wf.get("id") or wf.get("workflow_id")
    except Exception as e:
        print(f"⚠️  检查工作流是否存在时出错: {e}")
    
    return None


def main():
    parser = argparse.ArgumentParser(description="同步BPMN工作流到服务器")
    parser.add_argument(
        "--bpmn",
        type=Path,
        required=True,
        help="BPMN文件路径"
    )
    parser.add_argument(
        "--server",
        type=str,
        default=DEFAULT_SERVER,
        help=f"服务器地址 (默认: {DEFAULT_SERVER})"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=True,
        help="覆盖已存在的工作流 (默认: True)"
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_false",
        dest="overwrite",
        help="不覆盖已存在的工作流"
    )
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not args.bpmn.exists():
        print(f"❌ 错误: BPMN文件不存在: {args.bpmn}")
        sys.exit(1)
    
    print(f"🚀 开始同步BPMN工作流")
    print(f"   文件: {args.bpmn}")
    print(f"   服务器: {args.server}")
    print()
    
    try:
        # 1. 上传并解析BPMN
        workflow_def = upload_bpmn(args.server, args.bpmn)
        
        # 2. 检查是否已存在
        workflow_name = workflow_def.get("name")
        existing_id = check_workflow_exists(args.server, workflow_name)
        if existing_id:
            print(f"\n⚠️  工作流 '{workflow_name}' 已存在 (ID: {existing_id})")
            if not args.overwrite:
                print(f"   跳过保存（使用 --overwrite 覆盖）")
                return
            else:
                print(f"   将覆盖现有工作流")
        
        # 3. 保存到数据库
        result = save_workflow(args.server, workflow_def, overwrite=args.overwrite)
        
        print(f"\n🎉 同步完成！")
        print(f"   工作流: {workflow_name}")
        if result.get("workflow_id"):
            print(f"   ID: {result['workflow_id']}")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 网络错误: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   状态码: {e.response.status_code}")
            print(f"   响应: {e.response.text[:500]}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()




