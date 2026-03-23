"""
工具模块
包含各种辅助工具和实用程序
"""

# 使用绝对导入，避免相对导入问题
try:
    from tools.ssh_executor import (
        SSHCommandExecutor,
        DeploymentExecutor,
        CommandResult
    )
except ImportError:
    # 如果绝对导入失败，尝试相对导入
    try:
        from .ssh_executor import (
            SSHCommandExecutor,
            DeploymentExecutor,
            CommandResult
        )
    except ImportError:
        # 如果都失败，设置为None
        SSHCommandExecutor = None
        DeploymentExecutor = None
        CommandResult = None

__all__ = [
    'SSHCommandExecutor',
    'DeploymentExecutor',
    'CommandResult'
]

