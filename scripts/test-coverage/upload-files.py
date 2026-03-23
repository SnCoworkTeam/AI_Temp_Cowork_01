#!/usr/bin/env python3
"""
文件上传器
使用scp命令上传文件到服务器，连接限时10秒
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional

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


def ensure_remote_directory(
    ssh_config: Dict,
    remote_path: str,
    timeout: int = 10
) -> CommandResult:
    """
    确保远程目录存在
    
    Args:
        ssh_config: SSH配置字典
        remote_path: 远程路径
        timeout: 超时时间
        
    Returns:
        CommandResult对象
    """
    # 提取目录路径
    remote_dir = str(Path(remote_path).parent)
    
    # 构建SSH命令
    ssh_cmd = (
        f'ssh -F remote.ssh '
        f'-o ConnectTimeout={timeout} '
        f'-o StrictHostKeyChecking=no '
        f'enterprise-ai-server '
        f'"mkdir -p {remote_dir}"'
    )
    
    return run_command_safe(ssh_cmd, timeout=timeout)


def upload_file(
    local_file: Path,
    remote_path: str,
    ssh_config: Dict,
    timeout: int = 10
) -> CommandResult:
    """
    上传单个文件到服务器
    
    Args:
        local_file: 本地文件路径
        remote_path: 远程文件路径
        ssh_config: SSH配置字典
        timeout: 超时时间（秒）
        
    Returns:
        CommandResult对象
    """
    if not local_file.exists():
        return CommandResult(
            returncode=1,
            stdout="",
            stderr=f"本地文件不存在: {local_file}",
            elapsed_time=0.0
        )
    
    # 确保远程目录存在
    ensure_remote_directory(ssh_config, remote_path, timeout)
    
    # 构建scp命令
    # 使用-F remote.ssh来使用配置文件
    scp_cmd = (
        f'scp -F remote.ssh '
        f'-o ConnectTimeout={timeout} '
        f'-o StrictHostKeyChecking=no '
        f'"{local_file}" '
        f'enterprise-ai-server:"{remote_path}"'
    )
    
    return run_command_safe(scp_cmd, timeout=timeout * 2)  # 上传可能需要更长时间


def upload_files(
    file_mappings: List[Dict[str, str]],
    ssh_config: Optional[Dict] = None,
    remote_base_path: str = "/opt/enterprise-ai-platform",
    timeout: int = 10
) -> Dict[str, CommandResult]:
    """
    批量上传文件
    
    Args:
        file_mappings: 文件映射列表，每个元素为 {"local": "本地路径", "remote": "远程路径"}
        ssh_config: SSH配置，如果为None则自动读取
        remote_base_path: 远程基础路径
        timeout: 超时时间
        
    Returns:
        字典，key为本地文件路径，value为CommandResult
    """
    if ssh_config is None:
        ssh_config = get_ssh_config()
    
    results = {}
    
    for mapping in file_mappings:
        local_path = Path(mapping["local"])
        remote_path = mapping.get("remote")
        
        if remote_path is None:
            # 如果没有指定远程路径，使用相对路径
            remote_path = f"{remote_base_path}/{mapping['local']}".replace("\\", "/")
        
        # 确保远程路径是绝对路径
        if not remote_path.startswith("/"):
            remote_path = f"{remote_base_path}/{remote_path}"
        
        print(f"上传: {local_path} -> {remote_path}")
        
        result = upload_file(local_path, remote_path, ssh_config, timeout)
        results[str(local_path)] = result
        
        if result.success:
            print(f"  ✓ 成功")
        else:
            print(f"  ✗ 失败: {result.stderr}")
    
    return results


def upload_service_files(
    service_name: str,
    files: List[str],
    ssh_config: Optional[Dict] = None,
    remote_base_path: str = "/opt/enterprise-ai-platform",
    timeout: int = 10
) -> Dict[str, CommandResult]:
    """
    上传服务的文件
    
    Args:
        service_name: 服务名称
        files: 文件列表（相对于项目根目录）
        ssh_config: SSH配置
        remote_base_path: 远程基础路径
        timeout: 超时时间
        
    Returns:
        上传结果字典
    """
    _script_path = Path(__file__).resolve()
    PROJECT_ROOT = _script_path.parent.parent.parent.resolve()
    
    file_mappings = []
    for file_path in files:
        local_file = PROJECT_ROOT / file_path
        if local_file.exists():
            file_mappings.append({
                "local": str(file_path),
                "remote": f"{remote_base_path}/{file_path}".replace("\\", "/")
            })
        else:
            print(f"警告: 文件不存在，跳过: {file_path}")
    
    return upload_files(file_mappings, ssh_config, remote_base_path, timeout)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="上传文件到服务器")
    parser.add_argument("--file", help="单个文件路径")
    parser.add_argument("--remote", help="远程路径")
    parser.add_argument("--service", help="服务名称")
    parser.add_argument("--files", nargs="+", help="文件列表（用于服务上传）")
    parser.add_argument("--timeout", type=int, default=10, help="超时时间（秒）")
    parser.add_argument("--config", action="store_true", help="显示SSH配置")
    
    args = parser.parse_args()
    
    try:
        ssh_config = get_ssh_config()
        
        if args.config:
            print(json.dumps(ssh_config, indent=2, ensure_ascii=False))
            return
        
        if args.file:
            # 上传单个文件
            local_file = Path(args.file)
            remote_path = args.remote or f"/opt/enterprise-ai-platform/{args.file}".replace("\\", "/")
            
            result = upload_file(local_file, remote_path, ssh_config, args.timeout)
            
            if result.success:
                print(f"上传成功: {local_file}")
                sys.exit(0)
            else:
                print(f"上传失败: {result.stderr}", file=sys.stderr)
                sys.exit(1)
        
        elif args.service and args.files:
            # 上传服务文件
            results = upload_service_files(
                args.service,
                args.files,
                ssh_config,
                timeout=args.timeout
            )
            
            success_count = sum(1 for r in results.values() if r.success)
            total_count = len(results)
            
            print(f"\n上传完成: {success_count}/{total_count} 成功")
            
            if success_count == total_count:
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            parser.print_help()
            sys.exit(1)
            
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

