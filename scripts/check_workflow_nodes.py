#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查工作流节点名称"""

import sys
import json
import requests

WORKFLOW_ID = "abc62b1c-cda0-461a-a0ad-89851f2aa8cb"
API_URL = f"http://localhost:8080/api/workflows/{WORKFLOW_ID}"

try:
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.json()
    
    workflow = data.get("workflow", {})
    nodes = workflow.get("nodes", [])
    
    print("=" * 60)
    print("采购到付款流程 - 节点名称列表")
    print("=" * 60)
    
    for i, node in enumerate(nodes, 1):
        node_name = node.get("name", "未命名")
        node_type = node.get("node_type", "unknown")
        print(f"{i:2d}. {node_name} ({node_type})")
    
    print("=" * 60)
    print(f"总计: {len(nodes)} 个节点")
    
except Exception as e:
    print(f"错误: {e}", file=sys.stderr)
    sys.exit(1)





