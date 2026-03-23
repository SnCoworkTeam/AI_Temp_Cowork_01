#!/usr/bin/env python3
"""
覆盖率检查器
在Docker容器中运行测试，下载覆盖率报告，判断是否达到80%
"""
import json
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

# 导入其他模块
_script_path = Path(__file__).resolve()
sys.path.insert(0, str(_script_path.parent))

# 使用importlib动态导入
import importlib.util

def import_module_from_file(module_name, file_path):
    """从文件路径动态导入模块"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

parse_ssh_config = import_module_from_file("parse_ssh_config", _script_path.parent / "parse-ssh-config.py")
run_command_with_timeout = import_module_from_file("run_command_with_timeout", _script_path.parent / "run-command-with-timeout.py")

get_ssh_config = parse_ssh_config.get_ssh_config
run_command_safe = run_command_with_timeout.run_command_safe
CommandResult = run_command_with_timeout.CommandResult


# 服务容器名称映射
SERVICE_CONTAINERS = {
    "auth-service": "enterprise-ai-auth-service",
    "knowledge-base": "enterprise-ai-knowledge-base",
    "metadata-service": "enterprise-ai-metadata-service",
    "workflow-engine": "enterprise-ai-workflow-engine",
    "mcp-gateway": "enterprise-ai-mcp-gateway",
    "database": "enterprise-ai-postgres",  # database可能没有独立容器，需要特殊处理
}


def get_container_name(service_name: str) -> str:
    """获取服务的Docker容器名称"""
    return SERVICE_CONTAINERS.get(service_name, f"enterprise-ai-{service_name}")


def run_tests_in_docker(
    service_name: str,
    ssh_config: Optional[Dict] = None,
    timeout: int = 60  # 测试可能需要更长时间
) -> CommandResult:
    """
    在Docker容器中运行测试
    
    Args:
        service_name: 服务名称
        ssh_config: SSH配置
        timeout: 超时时间（秒），测试可能需要更长时间
        
    Returns:
        CommandResult对象
    """
    if ssh_config is None:
        ssh_config = get_ssh_config()
    
    container_name = get_container_name(service_name)
    
    # 构建测试命令
    # 对于database服务，可能需要特殊处理
    if service_name == "database":
        test_cmd = (
            f'docker exec {container_name} '
            f'pytest /database/tests --cov=/database/src '
            f'--cov-report=json:/tmp/coverage.json '
            f'--cov-report=term 2>&1'
        )
    else:
        # 其他服务在容器内的路径
        test_cmd = (
            f'docker exec {container_name} '
            f'pytest /app/tests --cov=/app/src '
            f'--cov-report=json:/tmp/coverage.json '
            f'--cov-report=term 2>&1'
        )
    
    # 构建SSH命令
    ssh_cmd = (
        f'ssh -F remote.ssh '
        f'-o ConnectTimeout=10 '
        f'-o StrictHostKeyChecking=no '
        f'enterprise-ai-server '
        f'"{test_cmd}"'
    )
    
    return run_command_safe(ssh_cmd, timeout=timeout)


def download_coverage_report(
    service_name: str,
    local_path: Path,
    ssh_config: Optional[Dict] = None,
    timeout: int = 10
) -> CommandResult:
    """
    从服务器下载覆盖率报告
    
    Args:
        service_name: 服务名称
        local_path: 本地保存路径
        ssh_config: SSH配置
        timeout: 超时时间
        
    Returns:
        CommandResult对象
    """
    if ssh_config is None:
        ssh_config = get_ssh_config()
    
    # 远程覆盖率报告路径
    remote_path = "/tmp/coverage.json"
    
    # 构建scp命令
    scp_cmd = (
        f'scp -F remote.ssh '
        f'-o ConnectTimeout={timeout} '
        f'-o StrictHostKeyChecking=no '
        f'enterprise-ai-server:"{remote_path}" '
        f'"{local_path}"'
    )
    
    return run_command_safe(scp_cmd, timeout=timeout * 2)


def parse_coverage_json(coverage_file: Path) -> Dict:
    """
    解析覆盖率JSON文件
    
    Args:
        coverage_file: 覆盖率JSON文件路径
        
    Returns:
        包含覆盖率信息的字典
    """
    if not coverage_file.exists():
        return {
            "total_coverage": 0.0,
            "files": {},
            "error": "覆盖率文件不存在"
        }
    
    try:
        with open(coverage_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 计算总覆盖率
        totals = data.get("totals", {})
        total_coverage = totals.get("percent_covered", 0.0)
        
        # 提取文件覆盖率
        files_coverage = {}
        for file_path, file_data in data.get("files", {}).items():
            summary = file_data.get("summary", {})
            files_coverage[file_path] = {
                "coverage": summary.get("percent_covered", 0.0),
                "lines": summary.get("num_statements", 0),
                "covered": summary.get("covered_lines", 0),
                "missing": summary.get("missing_lines", 0)
            }
        
        return {
            "total_coverage": total_coverage,
            "files": files_coverage,
            "totals": totals
        }
    except Exception as e:
        return {
            "total_coverage": 0.0,
            "files": {},
            "error": str(e)
        }


def check_service_coverage(
    service_name: str,
    target_coverage: float = 80.0,
    ssh_config: Optional[Dict] = None,
    timeout: int = 60
) -> Dict:
    """
    检查服务的测试覆盖率
    
    Args:
        service_name: 服务名称
        target_coverage: 目标覆盖率（默认80%）
        ssh_config: SSH配置
        timeout: 超时时间
        
    Returns:
        包含覆盖率信息的字典
    """
    if ssh_config is None:
        ssh_config = get_ssh_config()
    
    _script_path = Path(__file__).resolve()
    PROJECT_ROOT = _script_path.parent.parent.parent.resolve()
    
    # 创建临时目录保存覆盖率报告
    temp_dir = PROJECT_ROOT / ".coverage-reports"
    temp_dir.mkdir(exist_ok=True)
    
    coverage_file = temp_dir / f"{service_name}-coverage.json"
    
    # 1. 运行测试
    print(f"运行 {service_name} 的测试...")
    test_result = run_tests_in_docker(service_name, ssh_config, timeout)
    
    if not test_result.success:
        return {
            "service": service_name,
            "status": "TEST_FAILED",
            "coverage": 0.0,
            "target": target_coverage,
            "meets_target": False,
            "test_output": test_result.stdout,
            "test_error": test_result.stderr,
            "returncode": test_result.returncode
        }
    
    # 2. 下载覆盖率报告
    print(f"下载覆盖率报告...")
    download_result = download_coverage_report(service_name, coverage_file, ssh_config)
    
    if not download_result.success:
        # 如果下载失败，尝试从测试输出中提取覆盖率信息
        # pytest的term输出中包含覆盖率信息
        coverage = extract_coverage_from_output(test_result.stdout)
        
        return {
            "service": service_name,
            "status": "COVERAGE_DOWNLOAD_FAILED",
            "coverage": coverage,
            "target": target_coverage,
            "meets_target": coverage >= target_coverage,
            "test_output": test_result.stdout,
            "download_error": download_result.stderr
        }
    
    # 3. 解析覆盖率报告
    coverage_data = parse_coverage_json(coverage_file)
    total_coverage = coverage_data.get("total_coverage", 0.0)
    
    return {
        "service": service_name,
        "status": "SUCCESS",
        "coverage": total_coverage,
        "target": target_coverage,
        "meets_target": total_coverage >= target_coverage,
        "coverage_data": coverage_data,
        "test_output": test_result.stdout,
        "coverage_file": str(coverage_file)
    }


def extract_coverage_from_output(output: str) -> float:
    """
    从测试输出中提取覆盖率信息
    
    Args:
        output: 测试输出文本
        
    Returns:
        覆盖率百分比
    """
    import re
    
    # 查找覆盖率行，例如: "TOTAL 123 45 63%"
    pattern = r'TOTAL\s+\d+\s+\d+\s+(\d+(?:\.\d+)?)%'
    match = re.search(pattern, output)
    
    if match:
        return float(match.group(1))
    
    # 尝试其他格式
    pattern2 = r'(\d+(?:\.\d+)?)%\s+coverage'
    match2 = re.search(pattern2, output, re.IGNORECASE)
    
    if match2:
        return float(match2.group(1))
    
    return 0.0


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="检查服务测试覆盖率")
    parser.add_argument("service", help="服务名称")
    parser.add_argument("--target", type=float, default=80.0, help="目标覆盖率（默认80%）")
    parser.add_argument("--timeout", type=int, default=60, help="超时时间（秒）")
    
    args = parser.parse_args()
    
    try:
        result = check_service_coverage(args.service, args.target, timeout=args.timeout)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get("meets_target"):
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

