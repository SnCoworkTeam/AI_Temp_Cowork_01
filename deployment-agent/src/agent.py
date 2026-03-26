"""
部署协调智能体 - 主智能体类
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime

from .monitor import FileMonitor
from .analyzer import ServiceAnalyzer
from .executor import ScriptExecutor

logger = logging.getLogger(__name__)


class DeploymentCoordinatorAgent:
    """部署协调智能体（轻量级协调者）"""
    
    def __init__(
        self,
        watch_path: str = "/workspace",
        workdir: str = "/app/workdir",
        scripts_dir: str = "/workspace/scripts/deployment",
        service_map_path: Optional[str] = None
    ):
        """
        初始化部署协调智能体
        
        Args:
            watch_path: 监控的代码路径
            workdir: 工作目录（可写）
            scripts_dir: 脚本目录
            service_map_path: 服务映射配置文件路径
        """
        self.agent_id = "deployment-coordinator"
        self.name = "部署协调智能体"
        self.description = "自动监控代码变更并协调部署任务"
        
        self.watch_path = Path(watch_path)
        self.workdir = Path(workdir)
        self.workdir.mkdir(parents=True, exist_ok=True)
        
        # 初始化组件
        self.service_analyzer = ServiceAnalyzer(service_map_path)
        self.script_executor = ScriptExecutor(scripts_dir, str(self.workdir))
        self.file_monitor: Optional[FileMonitor] = None
        
        # 状态管理
        self.is_monitoring = False
        self.deployment_queue: List[Dict] = []
        self.deployment_history: List[Dict] = []
        
        logger.info(f"部署协调智能体已初始化: {self.name}")
    
    async def start_monitoring(self):
        """启动文件监控"""
        if self.is_monitoring:
            logger.warning("文件监控已在运行")
            return
        
        try:
            # 检查监控路径是否存在
            if not self.watch_path.exists():
                logger.warning(f"监控路径不存在: {self.watch_path}，跳过文件监控")
                return
            
            self.file_monitor = FileMonitor(
                watch_path=str(self.watch_path),
                callback=self._handle_file_change,
                exclude_patterns={
                    "node_modules", ".git", "__pycache__", "*.log",
                    ".pytest_cache", "venv", ".next", "dist", "build"
                }
            )
            self.file_monitor.start()
            self.is_monitoring = True
            logger.info(f"文件监控已启动: {self.watch_path}")
        except Exception as e:
            logger.error(f"启动文件监控失败: {e}，服务将继续运行但不会自动监控")
            # 不抛出异常，允许服务继续运行
    
    async def stop_monitoring(self):
        """停止文件监控"""
        if not self.is_monitoring:
            return
        
        if self.file_monitor:
            self.file_monitor.stop()
            self.file_monitor = None
        
        self.is_monitoring = False
        logger.info("文件监控已停止")
    
    async def _handle_file_change(self, file_path: str):
        """
        处理文件变更
        
        Args:
            file_path: 变更的文件路径
        """
        try:
            logger.info(f"检测到文件变更: {file_path}")
            
            # 1. 分析影响的服务
            affected_services = self.service_analyzer.analyze_changes([file_path])
            
            if not affected_services:
                logger.debug(f"文件变更不影响任何服务: {file_path}")
                return
            
            # 2. 获取所有依赖服务
            all_services = self.service_analyzer.get_all_dependencies(affected_services)
            
            # 3. 生成部署任务
            task = {
                "id": f"task_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "changed_file": file_path,
                "affected_services": affected_services,
                "all_services": all_services,
                "status": "pending"
            }
            
            # 4. 保存任务到工作目录
            task_file = self.workdir / f"{task['id']}.json"
            task_file.write_text(json.dumps(task, indent=2, ensure_ascii=False))
            
            # 5. 添加到部署队列
            self.deployment_queue.append(task)
            
            # 6. 执行部署（异步，不阻塞）
            asyncio.create_task(self._execute_deployment_task(task))
            
        except Exception as e:
            logger.error(f"处理文件变更失败: {file_path}, 错误: {e}")
    
    async def _execute_deployment_task(self, task: Dict):
        """
        执行部署任务
        
        Args:
            task: 部署任务字典
        """
        task_id = task["id"]
        services = task["all_services"]
        
        try:
            task["status"] = "running"
            logger.info(f"开始执行部署任务: {task_id}, 服务: {services}")
            
            # 执行部署
            result = await self.script_executor.execute_deployment(
                services=services,
                skip_data_sync=False,  # 包含数据同步
                skip_migration=False  # 包含数据库迁移
            )
            
            # 更新任务状态
            task["status"] = "completed" if result["result"]["success"] else "failed"
            task["result"] = result
            task["completed_at"] = datetime.now().isoformat()
            
            # 保存到历史记录
            self.deployment_history.append(task)
            
            # 更新任务文件
            task_file = self.workdir / f"{task_id}.json"
            task_file.write_text(json.dumps(task, indent=2, ensure_ascii=False))
            
            logger.info(f"部署任务完成: {task_id}, 状态: {task['status']}")
            
        except Exception as e:
            logger.error(f"执行部署任务失败: {task_id}, 错误: {e}")
            task["status"] = "failed"
            task["error"] = str(e)
            task["completed_at"] = datetime.now().isoformat()
    
    async def analyze_task(self, task_description: str, context: Dict) -> Dict:
        """
        分析部署任务
        
        Args:
            task_description: 任务描述
            context: 上下文信息
        
        Returns:
            分析结果
        """
        changed_files = context.get("changed_files", [])
        
        if not changed_files:
            return {
                "affected_services": [],
                "all_services": [],
                "deployment_plan": None
            }
        
        # 分析影响的服务
        affected_services = self.service_analyzer.analyze_changes(changed_files)
        
        # 获取所有依赖
        all_services = self.service_analyzer.get_all_dependencies(affected_services)
        
        # 生成部署计划
        deployment_plan = self.service_analyzer.generate_deployment_plan(all_services)
        
        return {
            "affected_services": affected_services,
            "all_services": all_services,
            "deployment_plan": deployment_plan
        }
    
    async def execute(
        self,
        input_data: Dict,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        执行部署任务
        
        Args:
            input_data: 输入数据（包含services等）
            context: 上下文信息
        
        Returns:
            执行结果
        """
        services = input_data.get("services", [])
        target_server = input_data.get("target_server", "app-server")
        skip_data_sync = input_data.get("skip_data_sync", False)
        skip_migration = input_data.get("skip_migration", False)
        include_neo4j = input_data.get("include_neo4j", True)
        
        results = []
        
        # 1. 执行代码和镜像同步
        if services:
            result = await self.script_executor.execute_deployment(
                services=services,
                target_server=target_server,
                skip_data_sync=skip_data_sync,
                skip_migration=skip_migration
            )
            results.append(result)
        
        # 2. 执行Neo4j数据同步（如果需要）
        if include_neo4j:
            neo4j_result = await self.script_executor.execute_neo4j_sync()
            results.append(neo4j_result)
        
        return {
            "status": "success",
            "services": services,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_status(self) -> Dict:
        """获取智能体状态"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "is_monitoring": self.is_monitoring,
            "queue_size": len(self.deployment_queue),
            "history_count": len(self.deployment_history),
            "workdir": str(self.workdir)
        }
    
    def get_deployment_history(self, limit: int = 10) -> List[Dict]:
        """获取部署历史"""
        return self.deployment_history[-limit:]




