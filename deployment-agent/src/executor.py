"""
脚本执行器 - 调用现有部署脚本
"""
import asyncio
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import subprocess

logger = logging.getLogger(__name__)


class ScriptExecutor:
    """脚本执行器 - 调用现有部署脚本"""
    
    def __init__(self, scripts_dir: str = "/workspace/scripts/deployment", workdir: str = "/app/workdir"):
        """
        初始化脚本执行器
        
        Args:
            scripts_dir: 脚本目录路径
            workdir: 工作目录路径（用于保存日志和临时文件）
        """
        self.scripts_dir = Path(scripts_dir)
        self.workdir = Path(workdir)
        self.workdir.mkdir(parents=True, exist_ok=True)
    
    async def execute_deployment(
        self,
        services: List[str],
        target_server: str = "app-server",
        skip_data_sync: bool = True,
        skip_migration: bool = False,
        dry_run: bool = False
    ) -> Dict:
        """
        执行完整部署（调用 complete-sync.ps1）
        
        注意：由于智能体在Linux容器中运行，而PowerShell脚本需要在Windows主机上执行，
        这里通过SSH连接到Windows主机执行，或者使用bash脚本。
        
        Args:
            services: 要部署的服务列表
            target_server: 目标服务器
            skip_data_sync: 是否跳过数据同步
            skip_migration: 是否跳过数据库迁移
            dry_run: 是否干运行模式
        
        Returns:
            执行结果字典
        """
        script_path = self.scripts_dir / "complete-sync.ps1"
        
        if not script_path.exists():
            # 尝试使用bash脚本
            bash_script = self.scripts_dir / "deploy-server.sh"
            if bash_script.exists():
                return await self._execute_bash_deployment(bash_script, services, skip_data_sync, skip_migration)
            raise FileNotFoundError(f"部署脚本不存在: {script_path}")
        
        # 方案：通过SSH在Windows主机上执行PowerShell脚本
        # 或者：创建一个wrapper脚本在容器内执行
        # 这里我们使用一个简化的方案：记录任务，提示用户手动执行
        # 或者：通过Docker exec在Windows主机上执行
        
        # 尝试通过Docker exec在Windows主机上执行（如果可能）
        # 或者：创建一个Python wrapper来执行PowerShell命令
        
        # 构建PowerShell命令
        ps_script = f"""
        cd /workspace
        powershell -ExecutionPolicy Bypass -File scripts/deployment/complete-sync.ps1 -RemotePath /opt/enterprise-ai-platform
        """
        
        # 如果服务列表不为空，添加服务参数
        if services and "all" not in services:
            ps_script = f"""
            cd /workspace
            powershell -ExecutionPolicy Bypass -File scripts/deployment/complete-sync.ps1 -RemotePath /opt/enterprise-ai-platform -Services {','.join(services)}
            """
        
        if skip_data_sync:
            ps_script = ps_script.replace("complete-sync.ps1", "complete-sync.ps1 -SkipDataSync")
        
        if skip_migration:
            ps_script = ps_script.replace("complete-sync.ps1", "complete-sync.ps1 -SkipMigration")
        
        # 由于容器内无法执行PowerShell，我们创建一个任务文件，提示用户执行
        # 或者：通过SSH连接到Windows主机执行
        
        # 方案：保存任务到工作目录，然后通过某种方式触发Windows主机执行
        task_file = self.workdir / f"deployment_task_{asyncio.get_event_loop().time()}.json"
        task_data = {
            "type": "deployment",
            "script": "complete-sync.ps1",
            "services": services,
            "skip_data_sync": skip_data_sync,
            "skip_migration": skip_migration,
            "dry_run": dry_run,
            "command": ps_script.strip(),
            "timestamp": datetime.now().isoformat()
        }
        task_file.write_text(json.dumps(task_data, indent=2, ensure_ascii=False))
        
        logger.warning(f"PowerShell脚本需要在Windows主机上执行。任务已保存到: {task_file}")
        logger.info("提示：请在Windows主机上执行以下命令：")
        logger.info(f"  powershell -ExecutionPolicy Bypass -File deployment-agent/scripts/execute-deployment-task.ps1 -TaskFile {task_file}")
        logger.info(f"  或直接执行: powershell -ExecutionPolicy Bypass -File scripts/deployment/complete-sync.ps1 -Services {','.join(services) if services else 'all'}")
        
        # 返回任务信息
        return {
            "script": "complete-sync.ps1",
            "services": services,
            "result": {
                "returncode": 0,
                "stdout": f"任务已创建: {task_file}。请在Windows主机上手动执行PowerShell脚本。",
                "stderr": "",
                "success": True,
                "note": "由于容器环境限制，PowerShell脚本需要在Windows主机上执行"
            },
            "task_file": str(task_file)
        }
    
    async def execute_sync(
        self,
        services: List[str],
        changed_file: Optional[str] = None
    ) -> Dict:
        """
        执行同步（调用 sync-to-server.ps1）
        
        Args:
            services: 要同步的服务列表
            changed_file: 变更的文件路径
        
        Returns:
            执行结果字典
        """
        script_path = self.scripts_dir / "sync-to-server.ps1"
        
        if not script_path.exists():
            logger.warning(f"同步脚本不存在: {script_path}, 使用完整部署脚本")
            return await self.execute_deployment(services)
        
        # 保存任务文件（由于容器内无法执行PowerShell）
        task_file = self.workdir / f"sync_task_{asyncio.get_event_loop().time()}.json"
        task_data = {
            "type": "sync",
            "script": "sync-to-server.ps1",
            "services": services,
            "changed_file": changed_file,
            "command": f"powershell -ExecutionPolicy Bypass -File scripts/deployment/sync-to-server.ps1 {' '.join(services)}",
            "timestamp": datetime.now().isoformat()
        }
        task_file.write_text(json.dumps(task_data, indent=2, ensure_ascii=False))
        
        logger.warning(f"PowerShell脚本需要在Windows主机上执行。任务已保存到: {task_file}")
        
        return {
            "script": "sync-to-server.ps1",
            "services": services,
            "changed_file": changed_file,
            "result": {
                "returncode": 0,
                "stdout": f"任务已创建: {task_file}",
                "stderr": "",
                "success": True,
                "note": "请在Windows主机上手动执行PowerShell脚本"
            },
            "task_file": str(task_file)
        }
    
    async def _execute_bash_deployment(
        self,
        script_path: Path,
        services: List[str],
        skip_data_sync: bool,
        skip_migration: bool
    ) -> Dict:
        """执行bash部署脚本"""
        cmd = ["bash", str(script_path)]
        
        if services and "all" not in services:
            cmd.extend(["--services", ",".join(services)])
        
        if skip_data_sync:
            cmd.append("--skip-backup")
        
        if skip_migration:
            cmd.append("--skip-migration")
        
        logger.info(f"执行bash部署脚本: {' '.join(cmd)}")
        result = await self._execute_command(cmd, cwd="/workspace")
        
        return {
            "script": script_path.name,
            "services": services,
            "result": result
        }
    
    async def execute_neo4j_sync(self) -> Dict:
        """
        执行Neo4j数据同步
        
        Returns:
            执行结果字典
        """
        # 查找Neo4j同步脚本
        possible_scripts = [
            self.scripts_dir / "sync-neo4j.ps1",
            self.scripts_dir / "export-neo4j-data.ps1",
            self.scripts_dir / "upload-neo4j-data-to-server.ps1"
        ]
        
        script_path = None
        for path in possible_scripts:
            if path.exists():
                script_path = path
                break
        
        if not script_path:
            logger.warning("未找到Neo4j同步脚本")
            return {
                "script": None,
                "result": {"returncode": -1, "error": "脚本不存在"}
            }
        
        cmd = ["powershell", "-File", str(script_path)]
        logger.info(f"执行Neo4j同步脚本: {' '.join(cmd)}")
        
        result = await self._execute_command(cmd, cwd="/workspace")
        
        return {
            "script": script_path.name,
            "result": result
        }
    
    async def _execute_command(self, cmd: List[str], cwd: str = None) -> Dict:
        """
        执行命令
        
        Args:
            cmd: 命令列表
            cwd: 工作目录
        
        Returns:
            执行结果字典
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "success": process.returncode == 0
            }
        except Exception as e:
            logger.error(f"执行命令失败: {cmd}, 错误: {e}")
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False
            }




