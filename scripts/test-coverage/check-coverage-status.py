#!/usr/bin/env python3
"""
检查各服务的测试覆盖率状态
返回每个服务的覆盖率百分比
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# 服务列表
SERVICES = [
    "auth-service",
    "knowledge-base",
    "metadata-service",
    "workflow-engine",
    "mcp-gateway",
    "database"
]


def run_coverage_check(service_name: str) -> Optional[Dict]:
    """
    运行单个服务的覆盖率检查
    
    Returns:
        包含覆盖率信息的字典，如果失败返回None
    """
    service_path = PROJECT_ROOT / service_name
    
    if not service_path.exists():
        return None
    
    test_path = service_path / "tests"
    if not test_path.exists():
        return {
            "service": service_name,
            "coverage": 0.0,
            "status": "NO_TESTS",
            "total_lines": 0,
            "covered_lines": 0,
            "missing_lines": 0
        }
    
    try:
        # 运行pytest with coverage
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                str(test_path),
                "--cov=src",
                "--cov-report=json",
                "--cov-report=term",
                "-q"
            ],
            cwd=str(service_path),
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        # 读取覆盖率JSON报告
        coverage_json_path = service_path / ".coverage.json"
        if coverage_json_path.exists():
            with open(coverage_json_path, 'r') as f:
                coverage_data = json.load(f)
            
            totals = coverage_data.get('totals', {})
            total_lines = totals.get('num_statements', 0)
            covered_lines = totals.get('covered_lines', 0)
            missing_lines = total_lines - covered_lines
            
            coverage_percent = (covered_lines / total_lines * 100) if total_lines > 0 else 0.0
            
            return {
                "service": service_name,
                "coverage": round(coverage_percent, 2),
                "status": "OK" if coverage_percent >= 80 else "NEEDS_IMPROVEMENT",
                "total_lines": total_lines,
                "covered_lines": covered_lines,
                "missing_lines": missing_lines,
                "tests_passed": result.returncode == 0
            }
        else:
            # 从输出中解析覆盖率
            output = result.stdout + result.stderr
            # 尝试从输出中提取覆盖率
            for line in output.split('\n'):
                if 'TOTAL' in line and '%' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            total = int(parts[1])
                            missed = int(parts[2])
                            coverage_str = parts[3].rstrip('%')
                            coverage = float(coverage_str)
                            
                            return {
                                "service": service_name,
                                "coverage": coverage,
                                "status": "OK" if coverage >= 80 else "NEEDS_IMPROVEMENT",
                                "total_lines": total,
                                "covered_lines": total - missed,
                                "missing_lines": missed,
                                "tests_passed": result.returncode == 0
                            }
                        except (ValueError, IndexError):
                            pass
            
            # 如果无法解析，返回默认值
            return {
                "service": service_name,
                "coverage": 0.0,
                "status": "UNKNOWN",
                "total_lines": 0,
                "covered_lines": 0,
                "missing_lines": 0,
                "tests_passed": result.returncode == 0
            }
            
    except subprocess.TimeoutExpired:
        return {
            "service": service_name,
            "coverage": 0.0,
            "status": "TIMEOUT",
            "total_lines": 0,
            "covered_lines": 0,
            "missing_lines": 0,
            "tests_passed": False
        }
    except Exception as e:
        return {
            "service": service_name,
            "coverage": 0.0,
            "status": f"ERROR: {str(e)}",
            "total_lines": 0,
            "covered_lines": 0,
            "missing_lines": 0,
            "tests_passed": False
        }


def check_all_services() -> Dict[str, Dict]:
    """检查所有服务的覆盖率"""
    results = {}
    
    for service in SERVICES:
        print(f"Checking {service}...", file=sys.stderr)
        result = run_coverage_check(service)
        if result:
            results[service] = result
    
    return results


def main():
    """主函数"""
    results = check_all_services()
    
    # 输出JSON格式的结果
    print(json.dumps(results, indent=2))
    
    # 检查是否所有服务都达到80%
    all_above_80 = all(
        r.get("coverage", 0) >= 80.0 
        for r in results.values() 
        if r.get("status") != "NO_TESTS"
    )
    
    # 返回退出码：0表示所有服务都达到80%，1表示还有服务未达到
    sys.exit(0 if all_above_80 else 1)


if __name__ == "__main__":
    main()

