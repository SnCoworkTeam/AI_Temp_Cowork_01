#!/usr/bin/env python3
"""
文档完整性检查
检查代码是否有对应的文档
"""
import sys
import ast
from pathlib import Path
from typing import List, Dict

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def check_function_documentation(file_path: Path) -> List[str]:
    """检查函数是否有文档字符串"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        
        for node in ast.walk(tree):
            # 检查公共函数和类
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                # 跳过私有方法（以下划线开头）
                if node.name.startswith('_') and not node.name.startswith('__'):
                    continue
                
                # 检查是否有文档字符串
                if not ast.get_docstring(node):
                    issues.append(
                        f"{file_path.relative_to(project_root)}:{node.lineno} - "
                        f"{'函数' if isinstance(node, ast.FunctionDef) else '类'} "
                        f"'{node.name}' 缺少文档字符串"
                    )
    except Exception as e:
        issues.append(f"{file_path.relative_to(project_root)}: 解析错误 - {e}")
    
    return issues


def check_api_documentation() -> List[str]:
    """检查API端点是否有文档"""
    issues = []
    
    services = [
        "mcp-gateway/src/routes",
        "workflow-engine/src/routes",
        "auth-service/src/routes",
        "knowledge-base/src/routes"
    ]
    
    for service_path in services:
        routes_dir = project_root / service_path
        if not routes_dir.exists():
            continue
        
        for py_file in routes_dir.rglob("*.py"):
            if "__init__" in str(py_file):
                continue
            
            file_issues = check_function_documentation(py_file)
            issues.extend(file_issues)
    
    return issues


def main():
    """主函数"""
    print("检查文档完整性...")
    
    issues = check_api_documentation()
    
    if issues:
        print(f"\n❌ 发现 {len(issues)} 个文档问题:")
        for issue in issues[:20]:  # 只显示前20个
            print(f"  - {issue}")
        if len(issues) > 20:
            print(f"  ... 还有 {len(issues) - 20} 个问题")
        sys.exit(1)
    else:
        print("✅ 文档检查通过")
        sys.exit(0)


if __name__ == "__main__":
    main()









