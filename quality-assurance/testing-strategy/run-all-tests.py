#!/usr/bin/env python3
"""
运行所有测试
包括单元测试、集成测试、端到端测试和性能测试
"""

import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

# 项目根目录
project_root = Path(__file__).parent.parent.parent
output_dir = project_root / "quality-assurance" / "reports" / "testing-strategy"
output_dir.mkdir(parents=True, exist_ok=True)


def run_pytest(test_type: str, test_path: str, coverage: bool = False) -> dict:
    """运行pytest测试"""
    print(f"\n运行 {test_type} 测试...")
    
    cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        "-v",
        "--tb=short",
    ]
    
    if coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=json",
            "--cov-report=html",
            f"--cov-report=term-missing",
        ])
    
    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    # 解析结果
    total = 0
    passed = 0
    failed = 0
    
    for line in result.stdout.split("\n"):
        if "passed" in line and "failed" in line:
            # 解析测试统计
            parts = line.split()
            for part in parts:
                if part.isdigit():
                    if total == 0:
                        total = int(part)
                    elif passed == 0:
                        passed = int(part)
                    elif failed == 0:
                        failed = int(part)
    
    return {
        "type": test_type,
        "path": test_path,
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": total - passed - failed,
        "success": result.returncode == 0,
        "output": result.stdout,
        "error": result.stderr
    }


def run_all_tests():
    """运行所有测试"""
    print("开始运行所有测试...")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "summary": {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }
    }
    
    # 1. 单元测试
    unit_test_result = run_pytest("unit", "tests/unit", coverage=True)
    results["tests"].append(unit_test_result)
    
    # 2. 集成测试
    integration_test_result = run_pytest("integration", "tests/integration")
    results["tests"].append(integration_test_result)
    
    # 3. 端到端测试
    e2e_test_result = run_pytest("e2e", "tests/e2e")
    results["tests"].append(e2e_test_result)
    
    # 汇总统计
    for test_result in results["tests"]:
        results["summary"]["total"] += test_result["total"]
        results["summary"]["passed"] += test_result["passed"]
        results["summary"]["failed"] += test_result["failed"]
        results["summary"]["skipped"] += test_result["skipped"]
    
    # 计算通过率
    if results["summary"]["total"] > 0:
        results["summary"]["pass_rate"] = (
            results["summary"]["passed"] / results["summary"]["total"]
        ) * 100
    else:
        results["summary"]["pass_rate"] = 0.0
    
    # 保存结果
    result_file = output_dir / "test-results.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # 打印摘要
    print("\n=== 测试结果摘要 ===")
    print(f"总测试数: {results['summary']['total']}")
    print(f"通过: {results['summary']['passed']}")
    print(f"失败: {results['summary']['failed']}")
    print(f"跳过: {results['summary']['skipped']}")
    print(f"通过率: {results['summary']['pass_rate']:.2f}%")
    
    return results


def main():
    """主函数"""
    try:
        results = run_all_tests()
        
        # 检查测试通过率
        pass_rate = results["summary"]["pass_rate"]
        if pass_rate < 100.0:
            print(f"\n❌ 测试通过率 {pass_rate:.2f}% 低于100%")
            sys.exit(1)
        else:
            print("\n✅ 所有测试通过")
            sys.exit(0)
    except Exception as e:
        print(f"ERROR: 运行测试时发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()









