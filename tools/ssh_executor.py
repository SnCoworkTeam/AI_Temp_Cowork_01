"""
SSH命令执行工具
基于Paramiko实现，用于AIOS平台中智能体工作流的服务器操作
"""

import paramiko
import logging
import os
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


# 数据类，用于结构化返回结果
@dataclass
class CommandResult:
    """命令执行结果结构"""
    command: str          # 原始命令
    safe_command: str     # 安全处理后的命令
    exit_code: int        # 退出码
    stdout: str          # 标准输出
    stderr: str          # 标准错误
    success: bool        # 是否成功
    timestamp: str       # 执行时间戳
    duration: float      # 执行耗时(秒)


class SSHCommandExecutor:
    """
    基于Paramiko的SSH命令执行器
    专为AIOS智能体工作流设计，支持安全命令执行和文件传输
    """

    def __init__(self,
                 host: str,
                 username: str,
                 private_key_path: Optional[str] = None,
                 password: Optional[str] = None,
                 port: int = 22,
                 base_workdir: str = "/opt/enterprise-ai-platform",
                 connection_timeout: int = 30):
        """
        初始化SSH执行器

        Args:
            host: 服务器地址
            username: 用户名
            private_key_path: 私钥路径(优先使用)
            password: 密码(私钥不存在时使用)
            port: SSH端口
            base_workdir: 基础工作目录，所有操作限制在此目录下
            connection_timeout: 连接超时时间(秒)
        """
        self.host = host
        self.port = port
        self.username = username
        self.private_key_path = private_key_path
        self.password = password
        self.base_workdir = base_workdir.rstrip('/')
        self.connection_timeout = connection_timeout

        # SSH客户端
        self.client = None
        self.sftp = None
        self.connected = False

        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def connect(self) -> bool:
        """建立SSH连接"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # 优先使用密钥认证
            if self.private_key_path and os.path.exists(self.private_key_path):
                private_key = paramiko.RSAKey.from_private_key_file(self.private_key_path)
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    pkey=private_key,
                    timeout=self.connection_timeout,
                    banner_timeout=20
                )
            elif self.password:
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=self.connection_timeout
                )
            else:
                raise ValueError("必须提供私钥路径或密码")

            # 测试连接
            self._test_connection()
            self.connected = True
            self.logger.info(f"成功连接到服务器 {self.host}:{self.port}")
            return True

        except Exception as e:
            self.logger.error(f"连接服务器失败: {e}")
            self.connected = False
            raise

    def _test_connection(self):
        """测试连接是否可用"""
        stdin, stdout, stderr = self.client.exec_command("echo 'Connection test'", timeout=5)
        exit_code = stdout.channel.recv_exit_status()
        if exit_code != 0:
            raise ConnectionError(f"连接测试失败: {stderr.read().decode()}")

    def _sanitize_command(self, command: str, project_id: Optional[str] = None) -> Tuple[str, str]:
        """
        处理命令（简化版，演示用）

        Args:
            command: 原始命令
            project_id: 项目ID（可选）

        Returns:
            Tuple[处理后的命令, 工作目录路径]
        """
        # 如果指定了项目ID，切换到项目目录
        if project_id:
            project_path = f"{self.base_workdir}/{project_id}"
            safe_project_path = os.path.normpath(project_path)
            # 创建项目目录（如果不存在）
            mkdir_cmd = f"mkdir -p {safe_project_path}"
            try:
                stdin, stdout, stderr = self.client.exec_command(mkdir_cmd, timeout=5)
                stdout.channel.recv_exit_status()
            except:
                pass  # 忽略创建目录的错误

            # 将命令限制在项目目录内执行
            safe_command = f"cd {safe_project_path} && {command}"
            return safe_command, safe_project_path
        else:
            # 没有项目ID时，使用基础工作目录
            safe_command = f"cd {self.base_workdir} && {command}"
            return safe_command, self.base_workdir

    def execute(self, command: str, project_id: Optional[str] = None, timeout: int = 30) -> CommandResult:
        """
        执行单条命令

        Args:
            command: 要执行的命令
            project_id: 项目标识符（可选）
            timeout: 命令执行超时时间(秒)

        Returns:
            CommandResult: 命令执行结果
        """
        start_time = datetime.now()

        if not self.connected:
            self.connect()

        try:
            # 处理命令
            safe_command, work_path = self._sanitize_command(command, project_id)

            self.logger.info(f"执行命令 [项目:{project_id or 'default'}] {work_path}: {safe_command}")

            # 执行命令
            stdin, stdout, stderr = self.client.exec_command(safe_command, timeout=timeout)

            # 获取输出
            stdout_text = stdout.read().decode('utf-8', errors='ignore').strip()
            stderr_text = stderr.read().decode('utf-8', errors='ignore').strip()
            exit_code = stdout.channel.recv_exit_status()

            # 计算执行时间
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # 构建结果
            result = CommandResult(
                command=command,
                safe_command=safe_command,
                exit_code=exit_code,
                stdout=stdout_text,
                stderr=stderr_text,
                success=exit_code == 0,
                timestamp=start_time.isoformat(),
                duration=duration
            )

            # 记录日志
            log_msg = f"命令执行 {'成功' if result.success else '失败'} [退出码:{exit_code}, 耗时:{duration:.2f}s]"
            if result.stderr:
                log_msg += f", 错误: {result.stderr[:100]}"
            self.logger.info(log_msg)

            return result

        except paramiko.SSHException as e:
            self.logger.error(f"SSH执行异常: {e}")
            raise
        except Exception as e:
            self.logger.error(f"命令执行失败: {e}")
            raise

    def execute_sequence(self, commands: List[str], project_id: Optional[str] = None,
                         stop_on_failure: bool = True) -> List[CommandResult]:
        """
        执行命令序列

        Args:
            commands: 命令列表
            project_id: 项目标识符（可选）
            stop_on_failure: 是否在失败时停止

        Returns:
            所有命令的执行结果列表
        """
        results = []
        for idx, cmd in enumerate(commands):
            try:
                result = self.execute(cmd, project_id)
                results.append(result)

                # 如果失败且设置了失败停止，则中断
                if not result.success and stop_on_failure:
                    self.logger.warning(f"命令序列在第 {idx+1} 条命令中断")
                    break

            except Exception as e:
                self.logger.error(f"执行序列中第 {idx+1} 条命令时发生异常: {e}")
                # 创建失败结果
                result = CommandResult(
                    command=cmd,
                    safe_command=cmd,
                    exit_code=-1,
                    stdout="",
                    stderr=str(e),
                    success=False,
                    timestamp=datetime.now().isoformat(),
                    duration=0
                )
                results.append(result)
                if stop_on_failure:
                    break

        return results

    def execute_streaming(self, command: str, project_id: Optional[str] = None,
                         callback: Optional[Callable[[str], None]] = None) -> CommandResult:
        """
        执行命令并实时流式输出

        Args:
            command: 要执行的命令
            project_id: 项目标识符（可选）
            callback: 实时输出回调函数 callback(line: str)

        Returns:
            CommandResult: 命令执行结果
        """
        start_time = datetime.now()

        if not self.connected:
            self.connect()

        try:
            safe_command, work_path = self._sanitize_command(command, project_id)

            self.logger.info(f"执行流式命令 [项目:{project_id or 'default'}] {work_path}: {safe_command}")

            # 使用 exec_command 的实时输出
            stdin, stdout, stderr = self.client.exec_command(
                safe_command,
                get_pty=True,  # 启用伪终端，支持实时输出
                timeout=None   # 不设置超时（由外部控制）
            )

            stdout_lines = []
            stderr_lines = []

            # 实时读取输出
            while True:
                # 检查是否有输出
                if stdout.channel.recv_ready():
                    line = stdout.readline()
                    if line:
                        line = line.rstrip()
                        stdout_lines.append(line)
                        if callback:
                            callback(f"[STDOUT] {line}")

                if stderr.channel.recv_stderr_ready():
                    line = stderr.readline()
                    if line:
                        line = line.rstrip()
                        stderr_lines.append(line)
                        if callback:
                            callback(f"[STDERR] {line}")

                # 检查命令是否完成
                if stdout.channel.exit_status_ready():
                    exit_code = stdout.channel.recv_exit_status()
                    break

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            return CommandResult(
                command=command,
                safe_command=safe_command,
                exit_code=exit_code,
                stdout='\n'.join(stdout_lines),
                stderr='\n'.join(stderr_lines),
                success=exit_code == 0,
                timestamp=start_time.isoformat(),
                duration=duration
            )

        except Exception as e:
            self.logger.error(f"流式命令执行失败: {e}")
            raise

    def upload_file(self, local_path: str, remote_filename: str, project_id: Optional[str] = None) -> bool:
        """
        上传文件到服务器

        Args:
            local_path: 本地文件路径
            remote_filename: 远程文件名
            project_id: 项目标识符（可选）

        Returns:
            是否上传成功
        """
        if not self.connected:
            self.connect()

        if not self.sftp:
            self.sftp = self.client.open_sftp()

        try:
            # 构建远程路径
            if project_id:
                remote_dir = f"{self.base_workdir}/{project_id}"
            else:
                remote_dir = self.base_workdir

            remote_path = f"{remote_dir}/{remote_filename}"

            # 确保远程目录存在
            self.execute(f"mkdir -p {remote_dir}", project_id)

            # 上传文件
            self.sftp.put(local_path, remote_path)
            self.logger.info(f"文件上传成功: {local_path} -> {remote_path}")
            return True

        except Exception as e:
            self.logger.error(f"文件上传失败: {e}")
            return False

    def download_file(self, remote_path: str, local_path: str, project_id: Optional[str] = None) -> bool:
        """
        从服务器下载文件

        Args:
            remote_path: 远程文件路径（相对项目目录）
            local_path: 本地保存路径
            project_id: 项目标识符（可选）

        Returns:
            是否下载成功
        """
        if not self.connected:
            self.connect()

        if not self.sftp:
            self.sftp = self.client.open_sftp()

        try:
            # 构建完整的远程路径
            if project_id:
                full_remote_path = f"{self.base_workdir}/{project_id}/{remote_path.lstrip('/')}"
            else:
                full_remote_path = f"{self.base_workdir}/{remote_path.lstrip('/')}"

            # 下载文件
            self.sftp.get(full_remote_path, local_path)
            self.logger.info(f"文件下载成功: {full_remote_path} -> {local_path}")
            return True

        except Exception as e:
            self.logger.error(f"文件下载失败: {e}")
            return False

    def close(self):
        """关闭连接"""
        if self.sftp:
            self.sftp.close()
            self.sftp = None

        if self.client:
            self.client.close()
            self.client = None

        self.connected = False
        self.logger.info("SSH连接已关闭")

    def __enter__(self):
        """上下文管理器支持"""
        if not self.connected:
            self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时自动关闭连接"""
        self.close()


# 部署执行器 - 封装常用部署操作
class DeploymentExecutor(SSHCommandExecutor):
    """部署执行器 - 封装常用部署操作"""

    def deploy_project(self, project_id: str, branch: str = "main") -> List[CommandResult]:
        """部署项目"""
        commands = [
            f"cd {self.base_workdir}",
            f"git pull origin {branch}",
            "docker compose restart web-ui",
            "sleep 5",
            "docker compose logs --tail=20 web-ui"
        ]
        return self.execute_sequence(commands, project_id, stop_on_failure=True)

    def run_migration(self, project_id: Optional[str] = None) -> CommandResult:
        """运行数据库迁移"""
        return self.execute(
            "docker compose exec -T project-management alembic upgrade head",
            project_id
        )

    def restart_service(self, service_name: str, project_id: Optional[str] = None) -> CommandResult:
        """重启服务"""
        return self.execute(
            f"docker compose restart {service_name}",
            project_id
        )

    def check_service_status(self, project_id: Optional[str] = None) -> CommandResult:
        """检查服务状态"""
        return self.execute(
            "docker compose ps",
            project_id
        )

    def view_logs(self, service_name: str, lines: int = 50, project_id: Optional[str] = None) -> CommandResult:
        """查看服务日志"""
        return self.execute(
            f"docker compose logs --tail={lines} {service_name}",
            project_id
        )

