#!/usr/bin/env python3
"""
静态代码分析
使用多种工具进行静态代码分析
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 项目根目录
project_root = Path(__file__).parent.parent.parent.parent
output_dir = project_root / "quality-assurance" / "reports" / "static-analysis"
output_dir.mkdir(parents=True, exist_ok=True)


def run_pylint(project_path: Path) -> Dict[str, Any]:
    """运行Pylint分析"""
    print("运行 Pylint 分析...")
    
    results = {
        "tool": "pylint",
        "timestamp": datetime.now().isoformat(),
        "issues": []
    }
    
    try:
        # 查找所有Python文件
        python_files = list(project_path.rglob("*.py"))
        python_files = [f for f in python_files if "venv" not in str(f) and "__pycache__" not in str(f)]
        
        if not python_files:
            return results
        
        # 运行pylint
        cmd = [
            sys.executable, "-m", "pylint",
            "--output-format=json",
            "--disable=C0111",  # 禁用缺少文档字符串
            "--max-line-length=120",
        ] + [str(f) for f in python_files[:50]]  # 限制文件数量
        
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True
        )
        
        # 解析JSON输出
        if result.stdout:
            try:
                issues = json.loads(result.stdout)
                results["issues"] = issues
            except json.JSONDecodeError:
                # Pylint可能返回多行JSON
                lines = result.stdout.strip().split("\n")
                issues = []
                for line in lines:
                    if line.strip().startswith("["):
                        try:
                            issues.extend(json.loads(line))
                        except:
                            pass
                results["issues"] = issues
        
        # 统计
        error_count = sum(1 for issue in results["issues"] if issue.get("type") == "error")
        warning_count = sum(1 for issue in results["issues"] if issue.get("type") == "warning")
        
        results["summary"] = {
            "total_files": len(python_files),
            "analyzed_files": len(set(issue.get("path", "") for issue in results["issues"])),
            "errors": error_count,
            "warnings": warning_count,
            "total_issues": len(results["issues"])
        }
        
    except FileNotFoundError:
        print("  ⚠️  Pylint未安装")
        results["error"] = "Pylint not installed"
    
    return results


def run_mypy(project_path: Path) -> Dict[str, Any]:
    """运行MyPy类型检查"""
    print("运行 MyPy 类型检查...")
    
    results = {
        "tool": "mypy",
        "timestamp": datetime.now().isoformat(),
        "issues": []
    }
    
    try:
        # 查找所有Python文件
        python_files = list(project_path.rglob("*.py"))
        python_files = [f for f in python_files if "venv" not in str(f) and "__pycache__" not in str(f)]
        
        if not python_files:
            return results
        
        # 运行mypy
        cmd = [
            sys.executable, "-m", "mypy",
            "--ignore-missing-imports",
            "--no-strict-optional",
            "--show-error-codes",
        ] + [str(f) for f in python_files[:20]]  # 限制文件数量
        
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True
        )
        
        # 解析输出
        issues = []
        for line in result.stdout.split("\n"):
            if ":" in line and ("error" in line.lower() or "note" in line.lower()):
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    issues.append({
                        "file": parts[0],
                        "line": parts[1],
                        "level": parts[2].strip(),
                        "message": parts[3].strip()
                    })
        
        results["issues"] = issues
        results["summary"] = {
            "total_files": len(python_files),
            "analyzed_files": len(set(issue.get("file", "") for issue in issues)),
            "errors": len([i for i in issues if "error" in i.get("level", "").lower()]),
            "total_issues": len(issues)
        }
        
    except FileNotFoundError:
        print("  ⚠️  MyPy未安装")
        results["error"] = "MyPy not installed"
    
    return results


def run_bandit(project_path: Path) -> Dict[str, Any]:
    """运行Bandit安全扫描"""
    print("运行 Bandit 安全扫描...")
    
    results = {
        "tool": "bandit",
        "timestamp": datetime.now().isoformat(),
        "issues": []
    }
    
    try:
        # 查找所有Python文件
        python_files = list(project_path.rglob("*.py"))
        python_files = [f for f in python_files if "venv" not in str(f) and "__pycache__" not in str(f)]
        
        if not python_files:
            return results
        
        # 运行bandit
        cmd = [
            sys.executable, "-m", "bandit",
            "-r", str(project_path),
            "-f", "json",
            "-ll",  # 低/低级别
        ]
        
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True
        )
        
        # 解析JSON输出
        if result.stdout:
            try:
                bandit_results = json.loads(result.stdout)
                results["issues"] = bandit_results.get("results", [])
                results["summary"] = bandit_results.get("metrics", {})
            except json.JSONDecodeError:
                pass
        
    except FileNotFoundError:
        print("  ⚠️  Bandit未安装")
        results["error"] = "Bandit not installed"
    
    return results


def generate_report(all_results: List[Dict[str, Any]]) -> None:
    """生成分析报告"""
    report_file = output_dir / f"static-analysis-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "tools": all_results
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n报告已保存: {report_file}")
    
    # 打印摘要
    print("\n=== 静态分析摘要 ===")
    for result in all_results:
        if "summary" in result:
            print(f"\n{result['tool']}:")
            print(f"  分析文件数: {result['summary'].get('analyzed_files', 0)}")
            print(f"  错误数: {result['summary'].get('errors', 0)}")
            print(f"  警告数: {result['summary'].get('warnings', 0)}")
            print(f"  总问题数: {result['summary'].get('total_issues', 0)}")


def main():
    """主函数"""
    print("开始静态代码分析...")
    
    all_results = []
    
    # 运行各种分析工具
    all_results.append(run_pylint(project_root))
    all_results.append(run_mypy(project_root))
    all_results.append(run_bandit(project_root))
    
    # 生成报告
    generate_report(all_results)
    
    # 检查是否有严重问题
    critical_issues = 0
    for result in all_results:
        if "summary" in result:
            critical_issues += result["summary"].get("errors", 0)
    
    if critical_issues > 0:
        print(f"\n⚠️  发现 {critical_issues} 个严重问题")
        sys.exit(1)
    else:
        print("\n✅ 静态分析完成，未发现严重问题")
        sys.exit(0)


if __name__ == "__main__":
    main()









