#!/usr/bin/env python3
"""
服务测试运行器
在服务器Docker容器中运行测试并生成覆盖率报告
"""
import json
import sys
from pathlib import Path
from typing import Dict, Optional

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
    "shared_libs": None,  # shared_libs可能没有独立容器
}


def get_container_name(service_name: str) -> Optional[str]:
    """获取服务的Docker容器名称"""
    return SERVICE_CONTAINERS.get(service_name, f"enterprise-ai-{service_name}")


def run_tests_in_docker(
    service_name: str,
    ssh_config: Optional[Dict] = None,
    timeout: int = 120  # 测试可能需要更长时间
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
    
    if container_name is None:
        return CommandResult(
            returncode=1,
            stdout="",
            stderr=f"服务 {service_name} 没有对应的Docker容器",
            elapsed_time=0.0
        )
    
    # 构建测试命令
    # 对于database服务，可能需要特殊处理
    if service_name == "database":
        test_cmd = (
            f'sudo docker exec {container_name} '
            f'python3 -m pytest /database/tests --cov=/database/src '
            f'--cov-report=json:/tmp/coverage.json '
            f'--cov-report=term-missing 2>&1'
        )
    else:
        # 其他服务在容器内的路径
        test_cmd = (
            f'sudo docker exec {container_name} '
            f'python3 -m pytest /app/tests --cov=/app/src '
            f'--cov-report=json:/tmp/coverage.json '
            f'--cov-report=term-missing 2>&1'
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


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="在服务器Docker容器中运行测试")
    parser.add_argument("service", help="服务名称")
    parser.add_argument("--timeout", type=int, default=120, help="超时时间（秒）")
    parser.add_argument("--download", type=Path, help="下载覆盖率报告到指定路径")
    
    args = parser.parse_args()
    
    try:
        ssh_config = get_ssh_config()
        
        # 运行测试
        print(f"运行 {args.service} 的测试...")
        result = run_tests_in_docker(args.service, ssh_config, args.timeout)
        
        if args.download:
            # 下载覆盖率报告
            print(f"下载覆盖率报告到 {args.download}...")
            download_result = download_coverage_report(args.service, args.download, ssh_config)
            
            if download_result.success:
                print(f"覆盖率报告已下载到: {args.download}")
            else:
                print(f"下载失败: {download_result.stderr}", file=sys.stderr)
        
        # 输出结果
        output = {
            "service": args.service,
            "success": result.success,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "elapsed_time": result.elapsed_time
        }
        
        print(json.dumps(output, indent=2, ensure_ascii=False))
        
        sys.exit(0 if result.success else 1)
        
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

