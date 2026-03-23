#!/usr/bin/env python3
"""
生成服务依赖关系图
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# 项目根目录
project_root = Path(__file__).parent.parent.parent
graph_dir = project_root / "dependencies" / "dependency-graph" / "service-dependencies"

# 读取现有的graph.json（如果存在）
graph_file = graph_dir / "graph.json"
if graph_file.exists():
    with open(graph_file, 'r', encoding='utf-8') as f:
        graph_data = json.load(f)
else:
    # 创建默认结构
    graph_data = {
        "version": "1.0.0",
        "generated_at": datetime.now().isoformat(),
        "services": [],
        "relationships": []
    }

# 更新生成时间
graph_data["generated_at"] = datetime.now().isoformat()

# 保存更新的图
graph_dir.mkdir(parents=True, exist_ok=True)
with open(graph_file, 'w', encoding='utf-8') as f:
    json.dump(graph_data, f, indent=2, ensure_ascii=False)

print(f"✅ 服务依赖图已更新: {graph_file}")









