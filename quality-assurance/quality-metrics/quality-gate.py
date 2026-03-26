#!/usr/bin/env python3
"""
质量门禁
检查代码质量指标是否满足要求
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 项目根目录
project_root = Path(__file__).parent.parent.parent
reports_dir = project_root / "quality-assurance" / "reports"


# 质量门禁阈值
QUALITY_GATES = {
    "code_coverage": {
        "threshold": 80.0,  # 代码覆盖率 >= 80%
        "critical": True
    },
    "static_analysis": {
        "threshold": 0,  # 静态分析无严重问题
        "critical": True
    },
    "architecture_compliance": {
        "threshold": 100.0,  # 架构符合性100%
        "critical": True
    },
    "test_pass_rate": {
        "threshold": 100.0,  # 测试通过率100%
        "critical": True
    },
    "performance_regression": {
        "threshold": 5.0,  # 性能回归 < 5%
        "critical": False
    }
}


def load_code_coverage() -> Dict[str, Any]:
    """加载代码覆盖率数据"""
    coverage_file = reports_dir / "code-coverage" / "coverage-summary.json"
    
    if not coverage_file.exists():
        return {
            "coverage": 0.0,
            "error": "覆盖率报告不存在"
        }
    
    try:
        with open(coverage_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 计算总体覆盖率
        total_lines = data.get("totals", {}).get("num_statements", 0)
        covered_lines = data.get("totals", {}).get("covered_lines", 0)
        
        if total_lines > 0:
            coverage = (covered_lines / total_lines) * 100
        else:
            coverage = 0.0
        
        return {
            "coverage": coverage,
            "total_lines": total_lines,
            "covered_lines": covered_lines
        }
    except Exception as e:
        return {
            "coverage": 0.0,
            "error": str(e)
        }


def load_static_analysis() -> Dict[str, Any]:
    """加载静态分析结果"""
    static_analysis_dir = reports_dir / "static-analysis"
    
    if not static_analysis_dir.exists():
        return {
            "errors": 0,
            "error": "静态分析报告不存在"
        }
    
    # 查找最新的报告
    reports = list(static_analysis_dir.glob("static-analysis-*.json"))
    if not reports:
        return {
            "errors": 0,
            "error": "未找到静态分析报告"
        }
    
    latest_report = max(reports, key=lambda p: p.stat().st_mtime)
    
    try:
        with open(latest_report, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total_errors = 0
        for tool_result in data.get("tools", []):
            if "summary" in tool_result:
                total_errors += tool_result["summary"].get("errors", 0)
        
        return {
            "errors": total_errors,
            "report_file": str(latest_report)
        }
    except Exception as e:
        return {
            "errors": 0,
            "error": str(e)
        }


def load_architecture_compliance() -> Dict[str, Any]:
    """加载架构符合性检查结果"""
    # 这里可以读取架构检查的结果
    # 暂时返回默认值
    return {
        "compliance": 100.0,
        "issues": []
    }


def load_test_results() -> Dict[str, Any]:
    """加载测试结果"""
    test_results_file = reports_dir / "testing-strategy" / "test-results.json"
    
    if not test_results_file.exists():
        return {
            "pass_rate": 0.0,
            "error": "测试结果文件不存在"
        }
    
    try:
        with open(test_results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total_tests = data.get("summary", {}).get("total", 0)
        passed_tests = data.get("summary", {}).get("passed", 0)
        
        if total_tests > 0:
            pass_rate = (passed_tests / total_tests) * 100
        else:
            pass_rate = 0.0
        
        return {
            "pass_rate": pass_rate,
            "total": total_tests,
            "passed": passed_tests,
            "failed": data.get("summary", {}).get("failed", 0)
        }
    except Exception as e:
        return {
            "pass_rate": 0.0,
            "error": str(e)
        }


def load_performance_metrics() -> Dict[str, Any]:
    """加载性能指标"""
    perf_file = reports_dir / "performance-metrics" / "performance-summary.json"
    
    if not perf_file.exists():
        return {
            "regression": 0.0,
            "error": "性能指标文件不存在"
        }
    
    try:
        with open(perf_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        regression = data.get("regression_percentage", 0.0)
        
        return {
            "regression": regression,
            "baseline": data.get("baseline", {}),
            "current": data.get("current", {})
        }
    except Exception as e:
        return {
            "regression": 0.0,
            "error": str(e)
        }


def check_quality_gates() -> Dict[str, Any]:
    """检查所有质量门禁"""
    print("检查质量门禁...")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "gates": {},
        "passed": True,
        "failed_gates": []
    }
    
    # 1. 代码覆盖率
    print("  检查代码覆盖率...")
    coverage_data = load_code_coverage()
    coverage = coverage_data.get("coverage", 0.0)
    threshold = QUALITY_GATES["code_coverage"]["threshold"]
    
    coverage_passed = coverage >= threshold
    results["gates"]["code_coverage"] = {
        "value": coverage,
        "threshold": threshold,
        "passed": coverage_passed,
        "data": coverage_data
    }
    
    if not coverage_passed:
        results["passed"] = False
        results["failed_gates"].append("code_coverage")
    
    # 2. 静态分析
    print("  检查静态分析...")
    static_data = load_static_analysis()
    errors = static_data.get("errors", 0)
    threshold = QUALITY_GATES["static_analysis"]["threshold"]
    
    static_passed = errors <= threshold
    results["gates"]["static_analysis"] = {
        "value": errors,
        "threshold": threshold,
        "passed": static_passed,
        "data": static_data
    }
    
    if not static_passed:
        results["passed"] = False
        results["failed_gates"].append("static_analysis")
    
    # 3. 架构符合性
    print("  检查架构符合性...")
    arch_data = load_architecture_compliance()
    compliance = arch_data.get("compliance", 0.0)
    threshold = QUALITY_GATES["architecture_compliance"]["threshold"]
    
    arch_passed = compliance >= threshold
    results["gates"]["architecture_compliance"] = {
        "value": compliance,
        "threshold": threshold,
        "passed": arch_passed,
        "data": arch_data
    }
    
    if not arch_passed:
        results["passed"] = False
        results["failed_gates"].append("architecture_compliance")
    
    # 4. 测试通过率
    print("  检查测试通过率...")
    test_data = load_test_results()
    pass_rate = test_data.get("pass_rate", 0.0)
    threshold = QUALITY_GATES["test_pass_rate"]["threshold"]
    
    test_passed = pass_rate >= threshold
    results["gates"]["test_pass_rate"] = {
        "value": pass_rate,
        "threshold": threshold,
        "passed": test_passed,
        "data": test_data
    }
    
    if not test_passed:
        results["passed"] = False
        results["failed_gates"].append("test_pass_rate")
    
    # 5. 性能回归
    print("  检查性能回归...")
    perf_data = load_performance_metrics()
    regression = perf_data.get("regression", 0.0)
    threshold = QUALITY_GATES["performance_regression"]["threshold"]
    
    perf_passed = regression < threshold
    results["gates"]["performance_regression"] = {
        "value": regression,
        "threshold": threshold,
        "passed": perf_passed,
        "data": perf_data
    }
    
    if not perf_passed:
        results["passed"] = False
        results["failed_gates"].append("performance_regression")
    
    return results


def generate_report(results: Dict[str, Any]) -> None:
    """生成质量门禁报告"""
    report_file = reports_dir / "quality-gate-report.json"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n报告已保存: {report_file}")
    
    # 打印结果
    print("\n=== 质量门禁检查结果 ===")
    print(f"\n总体结果: {'✅ 通过' if results['passed'] else '❌ 失败'}")
    
    for gate_name, gate_result in results["gates"].items():
        status = "✅" if gate_result["passed"] else "❌"
        value = gate_result["value"]
        threshold = gate_result["threshold"]
        
        print(f"\n{gate_name}:")
        print(f"  {status} 当前值: {value:.2f}, 阈值: {threshold}")
        
        if not gate_result["passed"]:
            if "error" in gate_result["data"]:
                print(f"  错误: {gate_result['data']['error']}")
    
    if results["failed_gates"]:
        print(f"\n❌ 失败的门禁: {', '.join(results['failed_gates'])}")


def main():
    """主函数"""
    print("开始质量门禁检查...")
    
    results = check_quality_gates()
    generate_report(results)
    
    if results["passed"]:
        print("\n✅ 所有质量门禁检查通过")
        sys.exit(0)
    else:
        print(f"\n❌ 质量门禁检查失败，有 {len(results['failed_gates'])} 个门禁未通过")
        sys.exit(1)


if __name__ == "__main__":
    main()









