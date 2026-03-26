#!/usr/bin/env python3
"""
SSH配置解析器
解析remote.ssh配置文件，提取连接信息
"""
import json
import re
from pathlib import Path
from typing import Dict, Optional

# 项目根目录
_script_path = Path(__file__).resolve()
PROJECT_ROOT = _script_path.parent.parent.parent.resolve()


def parse_ssh_config(config_path: Optional[Path] = None) -> Dict[str, Dict]:
    """
    解析SSH配置文件
    
    Args:
        config_path: SSH配置文件路径，默认为项目根目录下的remote.ssh
        
    Returns:
        包含所有Host配置的字典，格式为 {host_name: {key: value, ...}}
    """
    if config_path is None:
        config_path = PROJECT_ROOT / "remote.ssh"
    
    if not config_path.exists():
        raise FileNotFoundError(f"SSH配置文件不存在: {config_path}")
    
    configs = {}
    current_host = None
    current_config = {}
    
    with open(config_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # 跳过空行和注释
            if not line or line.startswith('#'):
                continue
            
            # 匹配Host行
            host_match = re.match(r'^Host\s+(.+)$', line, re.IGNORECASE)
            if host_match:
                # 保存之前的配置
                if current_host:
                    configs[current_host] = current_config
                
                # 开始新配置
                current_host = host_match.group(1).strip()
                current_config = {}
                continue
            
            # 匹配配置项（Key Value格式）
            config_match = re.match(r'^(\w+)\s+(.+)$', line)
            if config_match and current_host:
                key = config_match.group(1).strip()
                value = config_match.group(2).strip()
                current_config[key] = value
    
    # 保存最后一个配置
    if current_host:
        configs[current_host] = current_config
    
    return configs


def get_ssh_config(host_name: str = "enterprise-ai-server", config_path: Optional[Path] = None) -> Dict:
    """
    获取指定Host的SSH配置
    
    Args:
        host_name: Host名称，默认为enterprise-ai-server
        config_path: SSH配置文件路径
        
    Returns:
        包含该Host配置的字典
    """
    configs = parse_ssh_config(config_path)
    
    if host_name not in configs:
        raise ValueError(f"未找到Host配置: {host_name}")
    
    config = configs[host_name]
    
    # 提取关键信息
    result = {
        "host": host_name,
        "hostname": config.get("HostName", ""),
        "user": config.get("User", ""),
        "identity_file": config.get("IdentityFile", ""),
        "port": config.get("Port", "22"),
        "connect_timeout": config.get("ConnectTimeout", "10"),
        "strict_host_key_checking": config.get("StrictHostKeyChecking", "no"),
    }
    
    # 处理IdentityFile路径
    identity_file = result["identity_file"]
    if identity_file:
        # 如果是相对路径，转换为绝对路径
        if not Path(identity_file).is_absolute():
            # 尝试在项目根目录查找
            project_key = PROJECT_ROOT / identity_file
            if project_key.exists():
                result["identity_file"] = str(project_key)
            else:
                # 尝试在用户目录查找
                from os.path import expanduser
                user_key = Path(expanduser(f"~/.ssh/{identity_file}"))
                if user_key.exists():
                    result["identity_file"] = str(user_key)
                else:
                    result["identity_file"] = identity_file
    
    return result


def main():
    """主函数，输出JSON格式的配置"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="解析SSH配置文件")
    parser.add_argument("--host", default="enterprise-ai-server", help="Host名称")
    parser.add_argument("--config", type=Path, help="SSH配置文件路径")
    parser.add_argument("--all", action="store_true", help="输出所有Host配置")
    
    args = parser.parse_args()
    
    try:
        if args.all:
            configs = parse_ssh_config(args.config)
            print(json.dumps(configs, indent=2, ensure_ascii=False))
        else:
            config = get_ssh_config(args.host, args.config)
            print(json.dumps(config, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()

