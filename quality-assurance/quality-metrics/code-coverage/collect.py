#!/usr/bin/env python3
"""
收集代码覆盖率数据
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# 项目根目录
project_root = Path(__file__).parent.parent.parent.parent
output_dir = project_root / "quality-assurance" / "reports" / "code-coverage"
output_dir.mkdir(parents=True, exist_ok=True)


def collect_coverage():
    """收集代码覆盖率"""
    print("收集代码覆盖率...")
    
    # 运行pytest with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=.",
        "--cov-report=json",
        "--cov-report=html",
        "--cov-report=term",
        "tests/",
    ]
    
    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    # 读取覆盖率JSON报告
    coverage_file = project_root / "coverage.json"
    
    if not coverage_file.exists():
        print("❌ 覆盖率报告文件不存在")
        return None
    
    try:
        with open(coverage_file, 'r', encoding='utf-8') as f:
            coverage_data = json.load(f)
        
        # 提取摘要信息
        totals = coverage_data.get("totals", {})
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "coverage_percentage": totals.get("percent_covered", 0.0),
            "total_lines": totals.get("num_statements", 0),
            "covered_lines": totals.get("covered_lines", 0),
            "missing_lines": totals.get("missing_lines", 0),
            "excluded_lines": totals.get("excluded_lines", 0),
            "files": {}
        }
        
        # 提取文件级别的覆盖率
        for file_path, file_data in coverage_data.get("files", {}).items():
            file_totals = file_data.get("summary", {})
            summary["files"][file_path] = {
                "coverage_percentage": file_totals.get("percent_covered", 0.0),
                "total_lines": file_totals.get("num_statements", 0),
                "covered_lines": file_totals.get("covered_lines", 0),
                "missing_lines": file_totals.get("missing_lines", 0)
            }
        
        # 保存摘要
        summary_file = output_dir / "coverage-summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n覆盖率摘要已保存: {summary_file}")
        print(f"总体覆盖率: {summary['coverage_percentage']:.2f}%")
        
        return summary
        
    except Exception as e:
        print(f"❌ 读取覆盖率报告时出错: {e}")
        return None


def main():
    """主函数"""
    try:
        summary = collect_coverage()
        
        if summary is None:
            sys.exit(1)
        
        # 检查覆盖率阈值
        coverage = summary["coverage_percentage"]
        threshold = 80.0
        
        if coverage < threshold:
            print(f"\n❌ 代码覆盖率 {coverage:.2f}% 低于阈值 {threshold}%")
            sys.exit(1)
        else:
            print(f"\n✅ 代码覆盖率 {coverage:.2f}% 达到阈值 {threshold}%")
            sys.exit(0)
            
    except Exception as e:
        print(f"ERROR: 收集覆盖率时发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()









