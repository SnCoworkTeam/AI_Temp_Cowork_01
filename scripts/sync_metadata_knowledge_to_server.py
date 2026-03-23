#!/usr/bin/env python3
"""
元数据和知识库数据同步脚本
将本地Docker中的元数据和知识库数据同步到服务器
"""

import os
import sys
import subprocess
import json
import tarfile
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import argparse

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置
DOCKER_COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"
BACKUP_DIR = PROJECT_ROOT / "backups" / "sync"
LOG_DIR = PROJECT_ROOT / "logs" / "sync"

# 创建目录
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 日志函数
def log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [{level}] {message}"
    print(log_message)
    
    log_file = LOG_DIR / f"sync_{datetime.now().strftime('%Y%m%d')}.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_message + "\n")

def error_exit(message: str):
    log(message, "ERROR")
    sys.exit(1)

def check_docker_running():
    """检查Docker是否运行"""
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_docker_container_id(service_name: str) -> Optional[str]:
    """获取Docker容器ID"""
    try:
        result = subprocess.run(
            ["docker-compose", "-f", str(DOCKER_COMPOSE_FILE), "ps", "-q", service_name],
            capture_output=True,
            text=True,
            check=True,
            cwd=PROJECT_ROOT
        )
        container_id = result.stdout.strip()
        return container_id if container_id else None
    except subprocess.CalledProcessError:
        return None

def export_postgres_data(output_file: Path) -> bool:
    """导出PostgreSQL数据"""
    log("开始导出PostgreSQL数据...")
    
    # 从环境变量或docker-compose获取数据库配置
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "ai_platform")
    db_user = os.getenv("DB_USER", "ai_user")
    db_password = os.getenv("DB_PASSWORD", "ai_password")
    
    # 检查PostgreSQL容器
    postgres_container = get_docker_container_id("postgres")
    if not postgres_container:
        log("PostgreSQL容器未运行，尝试直接连接...", "WARNING")
        # 尝试直接连接
        pg_dump_cmd = [
            "pg_dump",
            "-h", db_host,
            "-p", db_port,
            "-U", db_user,
            "-d", db_name,
            "--clean",
            "--if-exists",
            "--create"
        ]
    else:
        # 使用docker exec
        log(f"使用PostgreSQL容器: {postgres_container[:12]}")
        pg_dump_cmd = [
            "docker", "exec",
            postgres_container,
            "pg_dump",
            "-U", db_user,
            "-d", db_name,
            "--clean",
            "--if-exists"
        ]
    
    try:
        env = os.environ.copy()
        if db_password:
            env["PGPASSWORD"] = db_password
        
        with open(output_file, "w", encoding="utf-8") as f:
            result = subprocess.run(
                pg_dump_cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                env=env,
                check=True,
                text=True
            )
        
        # 压缩
        compressed_file = output_file.with_suffix(".sql.gz")
        log(f"压缩PostgreSQL备份: {compressed_file}")
        subprocess.run(
            ["gzip", "-c", str(output_file)],
            stdout=open(compressed_file, "wb"),
            check=True
        )
        output_file.unlink()  # 删除未压缩文件
        
        log(f"PostgreSQL数据导出完成: {compressed_file}")
        return True
        
    except subprocess.CalledProcessError as e:
        log(f"PostgreSQL导出失败: {e.stderr}", "ERROR")
        return False
    except FileNotFoundError:
        log("pg_dump或gzip命令未找到，请安装PostgreSQL客户端工具", "ERROR")
        return False

def export_chroma_data(output_file: Path) -> bool:
    """导出Chroma向量数据库"""
    log("开始导出Chroma向量数据库...")
    
    # 查找Chroma数据目录
    chroma_volume = "enterprise-ai-platform_knowledge_base_chroma"
    
    try:
        # 获取volume路径
        result = subprocess.run(
            ["docker", "volume", "inspect", chroma_volume],
            capture_output=True,
            text=True,
            check=True
        )
        volume_info = json.loads(result.stdout)[0]
        volume_path = volume_info.get("Mountpoint")
        
        if not volume_path:
            log("无法找到Chroma volume路径", "WARNING")
            return False
        
        log(f"Chroma数据目录: {volume_path}")
        
        # 创建临时容器来访问volume
        temp_container = f"chroma_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 启动临时容器
        subprocess.run(
            ["docker", "run", "--rm", "-d", "--name", temp_container,
             "-v", f"{chroma_volume}:/data", "alpine", "sleep", "3600"],
            check=True,
            capture_output=True
        )
        
        try:
            # 打包数据 - 直接写入文件
            tar_cmd = ["docker", "exec", temp_container, "tar", "-czf", "-", "-C", "/data", "."]
            with open(output_file, "wb") as f:
                result = subprocess.run(
                    tar_cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    check=True
                )
            
            log(f"Chroma数据导出完成: {output_file}")
            return True
            
        finally:
            # 清理临时容器
            subprocess.run(
                ["docker", "rm", "-f", temp_container],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
    except subprocess.CalledProcessError as e:
        log(f"Chroma导出失败: {e.stderr}", "ERROR")
        return False
    except Exception as e:
        log(f"Chroma导出失败: {str(e)}", "ERROR")
        return False

def export_documents(output_file: Path) -> bool:
    """导出文档文件"""
    log("开始导出文档文件...")
    
    documents_volume = "enterprise-ai-platform_knowledge_base_documents"
    
    try:
        # 获取volume路径
        result = subprocess.run(
            ["docker", "volume", "inspect", documents_volume],
            capture_output=True,
            text=True,
            check=True
        )
        volume_info = json.loads(result.stdout)[0]
        volume_path = volume_info.get("Mountpoint")
        
        if not volume_path:
            log("无法找到文档volume路径", "WARNING")
            return False
        
        log(f"文档目录: {volume_path}")
        
        # 创建临时容器
        temp_container = f"docs_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        subprocess.run(
            ["docker", "run", "--rm", "-d", "--name", temp_container,
             "-v", f"{documents_volume}:/data", "alpine", "sleep", "3600"],
            check=True,
            capture_output=True
        )
        
        try:
            # 打包文档 - 直接写入文件
            tar_cmd = ["docker", "exec", temp_container, "tar", "-czf", "-", "-C", "/data", "."]
            with open(output_file, "wb") as f:
                result = subprocess.run(
                    tar_cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    check=True
                )
            
            log(f"文档导出完成: {output_file}")
            return True
            
        finally:
            subprocess.run(
                ["docker", "rm", "-f", temp_container],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
    except subprocess.CalledProcessError as e:
        log(f"文档导出失败: {e.stderr}", "ERROR")
        return False
    except Exception as e:
        log(f"文档导出失败: {str(e)}", "ERROR")
        return False

def create_sync_package(output_dir: Path) -> Optional[Path]:
    """创建同步包"""
    log("创建同步包...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"metadata_knowledge_sync_{timestamp}.tar.gz"
    package_path = output_dir / package_name
    
    # 导出数据
    postgres_file = output_dir / f"postgres_{timestamp}.sql.gz"
    chroma_file = output_dir / f"chroma_{timestamp}.tar.gz"
    documents_file = output_dir / f"documents_{timestamp}.tar.gz"
    
    success_count = 0
    
    # 导出PostgreSQL
    if export_postgres_data(postgres_file):
        success_count += 1
    else:
        log("跳过PostgreSQL导出", "WARNING")
    
    # 导出Chroma
    if export_chroma_data(chroma_file):
        success_count += 1
    else:
        log("跳过Chroma导出", "WARNING")
    
    # 导出文档
    if export_documents(documents_file):
        success_count += 1
    else:
        log("跳过文档导出", "WARNING")
    
    if success_count == 0:
        log("没有成功导出任何数据", "ERROR")
        return None
    
    # 创建元数据文件
    metadata = {
        "timestamp": timestamp,
        "date": datetime.now().isoformat(),
        "exports": {
            "postgres": str(postgres_file.name) if postgres_file.exists() else None,
            "chroma": str(chroma_file.name) if chroma_file.exists() else None,
            "documents": str(documents_file.name) if documents_file.exists() else None
        },
        "version": "1.0.0"
    }
    
    metadata_file = output_dir / f"metadata_{timestamp}.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    # 打包所有文件
    log(f"打包同步文件: {package_path}")
    with tarfile.open(package_path, "w:gz") as tar:
        for file in [postgres_file, chroma_file, documents_file, metadata_file]:
            if file.exists():
                tar.add(file, arcname=file.name)
                log(f"  添加文件: {file.name}")
    
    log(f"同步包创建完成: {package_path}")
    return package_path

def upload_to_server(package_path: Path, server_host: str, server_path: str) -> bool:
    """上传到服务器"""
    log(f"上传同步包到服务器: {server_host}:{server_path}")
    
    try:
        # 使用scp上传
        remote_path = f"{server_host}:{server_path}/{package_path.name}"
        subprocess.run(
            ["scp", str(package_path), remote_path],
            check=True
        )
        log(f"上传成功: {remote_path}")
        return True
    except subprocess.CalledProcessError as e:
        log(f"上传失败: {str(e)}", "ERROR")
        return False
    except FileNotFoundError:
        log("scp命令未找到，请安装SSH客户端", "ERROR")
        return False

def main():
    parser = argparse.ArgumentParser(description="同步元数据和知识库数据到服务器")
    parser.add_argument("--server-host", help="服务器地址 (例如: user@192.168.1.100)")
    parser.add_argument("--server-path", default="/opt/enterprise-ai-platform/backups", help="服务器路径")
    parser.add_argument("--no-upload", action="store_true", help="只导出，不上传")
    parser.add_argument("--output-dir", type=Path, default=BACKUP_DIR, help="输出目录")
    
    args = parser.parse_args()
    
    log("=" * 60)
    log("元数据和知识库数据同步开始")
    log("=" * 60)
    
    # 检查Docker
    if not check_docker_running():
        error_exit("Docker未运行，请先启动Docker")
    
    # 创建同步包
    package_path = create_sync_package(args.output_dir)
    if not package_path:
        error_exit("同步包创建失败")
    
    # 上传到服务器
    if not args.no_upload:
        if not args.server_host:
            log("未指定服务器地址，跳过上传", "WARNING")
            log(f"同步包已保存到: {package_path}")
        else:
            if upload_to_server(package_path, args.server_host, args.server_path):
                log("=" * 60)
                log("数据同步完成！")
                log("=" * 60)
                log(f"同步包: {package_path}")
                log(f"服务器路径: {args.server_host}:{args.server_path}/{package_path.name}")
            else:
                error_exit("上传失败")
    else:
        log("=" * 60)
        log("数据导出完成（未上传）")
        log("=" * 60)
        log(f"同步包: {package_path}")

if __name__ == "__main__":
    main()

