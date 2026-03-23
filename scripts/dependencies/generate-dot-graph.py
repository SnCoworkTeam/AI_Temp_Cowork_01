#!/usr/bin/env python3
"""
从JSON生成DOT格式的依赖关系图
"""
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
graph_dir = project_root / "dependencies" / "dependency-graph" / "service-dependencies"

# 读取graph.json
graph_file = graph_dir / "graph.json"
if not graph_file.exists():
    print("错误: graph.json不存在")
    sys.exit(1)

with open(graph_file, 'r', encoding='utf-8') as f:
    graph_data = json.load(f)

# 生成DOT格式
dot_lines = [
    "digraph ServiceDependencies {",
    "  rankdir=LR;",
    "  node [shape=box, style=rounded];",
    ""
]

# 添加节点
services = graph_data.get("services", [])
for service in services:
    service_name = service.get("name", "").replace("-", "_")
    service_type = service.get("type", "")
    dot_lines.append(f'  "{service_name}" [label="{service.get("name", "")}\\n({service_type})"];')

dot_lines.append("")

# 添加边
relationships = graph_data.get("relationships", [])
for rel in relationships:
    from_service = rel.get("from", "").replace("-", "_")
    to_service = rel.get("to", "").replace("-", "_")
    rel_type = rel.get("type", "")
    dot_lines.append(f'  "{from_service}" -> "{to_service}" [label="{rel_type}"];')

dot_lines.append("}")

# 保存DOT文件
dot_file = graph_dir / "graph.dot"
with open(dot_file, 'w', encoding='utf-8') as f:
    f.write("\n".join(dot_lines))

print(f"✅ DOT图已生成: {dot_file}")

# 尝试生成PNG（如果Graphviz可用）
try:
    import subprocess
    png_file = graph_dir / "graph.png"
    subprocess.run(
        ["dot", "-Tpng", str(dot_file), "-o", str(png_file)],
        check=True,
        capture_output=True
    )
    print(f"✅ PNG图已生成: {png_file}")
except (subprocess.CalledProcessError, FileNotFoundError):
    print("⚠️  Graphviz未安装，跳过PNG生成")









