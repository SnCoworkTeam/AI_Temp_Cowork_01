#!/usr/bin/env python3
"""
代码复杂度分析
分析代码的圈复杂度、认知复杂度等指标
"""

import sys
import ast
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# 项目根目录
project_root = Path(__file__).parent.parent.parent.parent
output_dir = project_root / "quality-assurance" / "reports" / "complexity-analysis"
output_dir.mkdir(parents=True, exist_ok=True)


class ComplexityVisitor(ast.NodeVisitor):
    """AST访问者，用于计算复杂度"""
    
    def __init__(self):
        self.complexity = 1  # 基础复杂度为1
        self.max_complexity = 0
        self.functions = []
    
    def visit_FunctionDef(self, node):
        """访问函数定义"""
        # 重置复杂度计数器
        old_complexity = self.complexity
        self.complexity = 1
        
        # 访问函数体
        self.generic_visit(node)
        
        # 记录函数复杂度
        func_complexity = self.complexity
        self.functions.append({
            "name": node.name,
            "line": node.lineno,
            "complexity": func_complexity,
            "parameters": len(node.args.args)
        })
        
        if func_complexity > self.max_complexity:
            self.max_complexity = func_complexity
        
        # 恢复复杂度
        self.complexity = old_complexity
    
    def visit_If(self, node):
        """访问if语句"""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_For(self, node):
        """访问for循环"""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_While(self, node):
        """访问while循环"""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_Try(self, node):
        """访问try语句"""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_With(self, node):
        """访问with语句"""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_BoolOp(self, node):
        """访问布尔操作（and/or）"""
        self.complexity += len(node.values) - 1
        self.generic_visit(node)
    
    def visit_IfExp(self, node):
        """访问条件表达式"""
        self.complexity += 1
        self.generic_visit(node)


def analyze_file_complexity(file_path: Path) -> Dict[str, Any]:
    """分析单个文件的复杂度"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        
        return {
            "file": str(file_path.relative_to(project_root)),
            "max_complexity": visitor.max_complexity,
            "functions": visitor.functions,
            "total_functions": len(visitor.functions)
        }
    except SyntaxError as e:
        return {
            "file": str(file_path.relative_to(project_root)),
            "error": f"语法错误: {e}"
        }
    except Exception as e:
        return {
            "file": str(file_path.relative_to(project_root)),
            "error": str(e)
        }


def analyze_complexity() -> Dict[str, Any]:
    """分析整个项目的复杂度"""
    print("分析代码复杂度...")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "files": [],
        "summary": {
            "total_files": 0,
            "high_complexity_files": 0,
            "high_complexity_functions": 0,
            "max_complexity": 0,
            "avg_complexity": 0.0
        }
    }
    
    # 查找所有Python文件
    python_files = list(project_root.rglob("*.py"))
    python_files = [
        f for f in python_files
        if "venv" not in str(f)
        and "__pycache__" not in str(f)
        and ".git" not in str(f)
        and "migrations" not in str(f)  # 排除迁移文件
    ]
    
    results["summary"]["total_files"] = len(python_files)
    
    all_complexities = []
    high_complexity_threshold = 10
    
    for py_file in python_files:
        file_result = analyze_file_complexity(py_file)
        results["files"].append(file_result)
        
        if "max_complexity" in file_result:
            max_comp = file_result["max_complexity"]
            all_complexities.append(max_comp)
            
            if max_comp > high_complexity_threshold:
                results["summary"]["high_complexity_files"] += 1
            
            # 检查函数复杂度
            for func in file_result.get("functions", []):
                if func["complexity"] > high_complexity_threshold:
                    results["summary"]["high_complexity_functions"] += 1
    
    # 计算统计信息
    if all_complexities:
        results["summary"]["max_complexity"] = max(all_complexities)
        results["summary"]["avg_complexity"] = sum(all_complexities) / len(all_complexities)
    
    return results


def generate_report(results: Dict[str, Any]) -> None:
    """生成复杂度分析报告"""
    report_file = output_dir / f"complexity-analysis-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n报告已保存: {report_file}")
    
    # 打印摘要
    print("\n=== 复杂度分析摘要 ===")
    summary = results["summary"]
    print(f"总文件数: {summary['total_files']}")
    print(f"高复杂度文件数 (>10): {summary['high_complexity_files']}")
    print(f"高复杂度函数数 (>10): {summary['high_complexity_functions']}")
    print(f"最大复杂度: {summary['max_complexity']}")
    print(f"平均复杂度: {summary['avg_complexity']:.2f}")
    
    # 列出高复杂度函数
    if summary['high_complexity_functions'] > 0:
        print("\n高复杂度函数 (>10):")
        for file_result in results["files"]:
            for func in file_result.get("functions", []):
                if func["complexity"] > 10:
                    print(f"  {file_result['file']}:{func['line']} - {func['name']} (复杂度: {func['complexity']})")


def main():
    """主函数"""
    print("开始复杂度分析...")
    
    results = analyze_complexity()
    generate_report(results)
    
    # 检查是否有高复杂度代码
    high_complexity_count = results["summary"]["high_complexity_functions"]
    
    if high_complexity_count > 0:
        print(f"\n⚠️  发现 {high_complexity_count} 个高复杂度函数（>10）")
        print("💡 建议重构这些函数以降低复杂度")
        sys.exit(1)
    else:
        print("\n✅ 复杂度分析完成，未发现高复杂度代码")
        sys.exit(0)


if __name__ == "__main__":
    main()









