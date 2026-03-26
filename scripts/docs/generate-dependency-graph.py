#!/usr/bin/env python3
"""
依赖图生成脚本
生成模块依赖关系图
"""
import sys
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def extract_imports(file_path: Path) -> Tuple[List[str], List[str]]:
    """提取文件中的导入"""
    imports = []
    from_imports = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    from_imports.append(f"{module}.{alias.name}")
    except Exception:
        pass
    
    return imports, from_imports


def build_dependency_graph() -> Dict[str, Set[str]]:
    """构建依赖图"""
    graph = defaultdict(set)
    
    services = [
        "mcp-gateway/src",
        "workflow-engine/src",
        "auth-service/src",
        "knowledge-base/src",
        "shared-libs",
        "database/src"
    ]
    
    for service_path in services:
        service_full_path = project_root / service_path
        if not service_full_path.exists():
            continue
        
        for py_file in service_full_path.rglob("*.py"):
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue
            
            relative_path = str(py_file.relative_to(project_root))
            imports, from_imports = extract_imports(py_file)
            
            all_imports = imports + from_imports
            for imp in all_imports:
                # 只记录项目内部的导入
                if any(imp.startswith(prefix) for prefix in [
                    "mcp_gateway", "workflow_engine", "auth_service",
                    "knowledge_base", "shared_libs", "database"
                ]):
                    graph[relative_path].add(imp)
    
    return graph


def generate_dot_graph(graph: Dict[str, Set[str]], output_file: Path):
    """生成Graphviz DOT格式的依赖图"""
    print("生成依赖图...")
    
    lines = ["digraph Dependencies {", "  rankdir=LR;", "  node [shape=box];", ""]
    
    # 添加节点
    nodes = set(graph.keys())
    for node in nodes:
        for dep in graph[node]:
            # 简化节点名称
            node_name = node.replace("/", "_").replace(".py", "").replace("-", "_")
            dep_name = dep.replace(".", "_").replace("-", "_")
            lines.append(f'  "{node_name}" -> "{dep_name}";')
    
    lines.append("}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    print(f"  ✅ DOT文件已保存: {output_file}")
    
    # 尝试生成图片
    try:
        import subprocess
        png_file = output_file.with_suffix(".png")
        subprocess.run(
            ["dot", "-Tpng", str(output_file), "-o", str(png_file)],
            check=True
        )
        print(f"  ✅ PNG图片已保存: {png_file}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  提示: 安装Graphviz以生成图片 (brew install graphviz 或 apt-get install graphviz)")


def generate_mermaid_graph(graph: Dict[str, Set[str]], output_file: Path):
    """生成Mermaid格式的依赖图"""
    print("生成Mermaid依赖图...")
    
    lines = ["graph TD"]
    
    # 添加边
    for node, deps in graph.items():
        if deps:
            node_name = node.replace("/", "_").replace(".py", "").replace("-", "_")[:30]
            for dep in deps:
                dep_name = dep.replace(".", "_").replace("-", "_")[:30]
                lines.append(f'    {node_name} --> {dep_name}')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    print(f"  ✅ Mermaid文件已保存: {output_file}")


def generate_dependency_graph():
    """生成依赖图"""
    print("开始生成依赖图...")
    
    docs_dir = project_root / "docs" / "auto-generated" / "dependency-graphs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    graph = build_dependency_graph()
    
    # 生成DOT格式
    dot_file = docs_dir / "dependencies.dot"
    generate_dot_graph(graph, dot_file)
    
    # 生成Mermaid格式
    mermaid_file = docs_dir / "dependencies.mmd"
    generate_mermaid_graph(graph, mermaid_file)
    
    # 生成统计信息
    stats_file = docs_dir / "dependency-stats.md"
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("# 依赖统计\n\n")
        f.write(f"总模块数: {len(graph)}\n\n")
        f.write("## 依赖最多的模块\n\n")
        
        sorted_modules = sorted(graph.items(), key=lambda x: len(x[1]), reverse=True)
        for module, deps in sorted_modules[:10]:
            f.write(f"- `{module}`: {len(deps)} 个依赖\n")
    
    print(f"\n✅ 依赖图生成完成")
    print(f"文档保存在: {docs_dir}")


if __name__ == "__main__":
    generate_dependency_graph()









