#!/usr/bin/env python3
"""
代码文档生成脚本
从代码注释自动生成文档
"""
import sys
import ast
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def extract_docstring(node: ast.AST) -> str:
    """提取文档字符串"""
    if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
        return ast.get_docstring(node) or ""
    return ""


def extract_function_info(node: ast.FunctionDef) -> Dict[str, Any]:
    """提取函数信息"""
    info = {
        "name": node.name,
        "docstring": extract_docstring(node),
        "parameters": [],
        "returns": None,
        "decorators": [d.id if isinstance(d, ast.Name) else "unknown" for d in node.decorator_list],
        "line_number": node.lineno
    }
    
    # 提取参数
    for arg in node.args.args:
        param_info = {
            "name": arg.arg,
            "type": None,
            "default": None
        }
        
        # 获取类型注解
        if arg.annotation:
            if isinstance(arg.annotation, ast.Name):
                param_info["type"] = arg.annotation.id
            elif isinstance(arg.annotation, ast.Constant):
                param_info["type"] = str(arg.annotation.value)
        
        info["parameters"].append(param_info)
    
    # 提取返回类型
    if node.returns:
        if isinstance(node.returns, ast.Name):
            info["returns"] = node.returns.id
    
    return info


def extract_class_info(node: ast.ClassDef) -> Dict[str, Any]:
    """提取类信息"""
    info = {
        "name": node.name,
        "docstring": extract_docstring(node),
        "bases": [],
        "methods": [],
        "line_number": node.lineno
    }
    
    # 提取基类
    for base in node.bases:
        if isinstance(base, ast.Name):
            info["bases"].append(base.id)
    
    # 提取方法
    for item in node.body:
        if isinstance(item, ast.FunctionDef):
            method_info = extract_function_info(item)
            info["methods"].append(method_info)
    
    return info


def extract_module_info(file_path: Path) -> Dict[str, Any]:
    """提取模块信息"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        
        module_info = {
            "file": str(file_path.relative_to(project_root)),
            "docstring": extract_docstring(tree),
            "classes": [],
            "functions": [],
            "imports": []
        }
        
        # 提取导入
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_info["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    module_info["imports"].append(f"{module}.{alias.name}")
        
        # 提取类和函数
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                module_info["classes"].append(extract_class_info(node))
            elif isinstance(node, ast.FunctionDef):
                module_info["functions"].append(extract_function_info(node))
        
        return module_info
    except Exception as e:
        return {
            "file": str(file_path.relative_to(project_root)),
            "error": str(e)
        }


def generate_markdown_docs(module_info: Dict[str, Any]) -> str:
    """生成Markdown文档"""
    lines = []
    
    lines.append(f"# {Path(module_info['file']).stem}")
    lines.append("")
    
    if module_info.get("docstring"):
        lines.append(module_info["docstring"])
        lines.append("")
    
    lines.append(f"**文件路径**: `{module_info['file']}`")
    lines.append("")
    
    # 类文档
    if module_info.get("classes"):
        lines.append("## 类")
        lines.append("")
        for cls in module_info["classes"]:
            lines.append(f"### {cls['name']}")
            lines.append("")
            if cls.get("docstring"):
                lines.append(cls["docstring"])
                lines.append("")
            
            if cls.get("bases"):
                lines.append(f"**继承自**: {', '.join(cls['bases'])}")
                lines.append("")
            
            # 方法
            if cls.get("methods"):
                lines.append("#### 方法")
                lines.append("")
                for method in cls["methods"]:
                    lines.append(f"##### `{method['name']}`")
                    lines.append("")
                    if method.get("docstring"):
                        lines.append(method["docstring"])
                        lines.append("")
                    
                    if method.get("parameters"):
                        lines.append("**参数**:")
                        lines.append("")
                        for param in method["parameters"]:
                            param_str = f"- `{param['name']}`"
                            if param.get("type"):
                                param_str += f": {param['type']}"
                            lines.append(param_str)
                        lines.append("")
                    
                    if method.get("returns"):
                        lines.append(f"**返回**: `{method['returns']}`")
                        lines.append("")
    
    # 函数文档
    if module_info.get("functions"):
        lines.append("## 函数")
        lines.append("")
        for func in module_info["functions"]:
            lines.append(f"### `{func['name']}`")
            lines.append("")
            if func.get("docstring"):
                lines.append(func["docstring"])
                lines.append("")
            
            if func.get("parameters"):
                lines.append("**参数**:")
                lines.append("")
                for param in func["parameters"]:
                    param_str = f"- `{param['name']}`"
                    if param.get("type"):
                        param_str += f": {param['type']}"
                    lines.append(param_str)
                lines.append("")
            
            if func.get("returns"):
                lines.append(f"**返回**: `{func['returns']}`")
                lines.append("")
    
    return "\n".join(lines)


def generate_code_docs():
    """生成所有代码文档"""
    print("开始生成代码文档...")
    
    docs_dir = project_root / "docs" / "auto-generated" / "code-docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    services = [
        "mcp-gateway/src",
        "workflow-engine/src",
        "auth-service/src",
        "knowledge-base/src",
        "shared-libs",
        "database/src"
    ]
    
    all_modules = []
    
    for service_path in services:
        service_full_path = project_root / service_path
        if not service_full_path.exists():
            continue
        
        print(f"\n处理服务: {service_path}")
        
        # 查找所有Python文件
        for py_file in service_full_path.rglob("*.py"):
            # 跳过测试文件和特殊文件
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue
            
            module_info = extract_module_info(py_file)
            if "error" not in module_info:
                all_modules.append(module_info)
                
                # 生成Markdown文档
                md_content = generate_markdown_docs(module_info)
                
                # 保存文档
                relative_path = py_file.relative_to(project_root)
                doc_file = docs_dir / relative_path.with_suffix(".md")
                doc_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(doc_file, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                
                print(f"  ✅ {relative_path}")
    
    # 生成索引
    index_file = docs_dir / "README.md"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("# 代码文档索引\n\n")
        f.write(f"生成时间: {datetime.now().isoformat()}\n\n")
        f.write("## 模块列表\n\n")
        
        for module in sorted(all_modules, key=lambda x: x["file"]):
            f.write(f"- [{module['file']}]({module['file'].replace('.py', '.md')})\n")
    
    print(f"\n✅ 代码文档生成完成")
    print(f"文档保存在: {docs_dir}")


if __name__ == "__main__":
    generate_code_docs()









