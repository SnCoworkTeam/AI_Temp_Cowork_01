"""
SSHCommandExecutor 使用示例
演示如何使用SSH命令执行工具
"""

import os
import sys
from typing import Dict, Any
from tools.ssh_executor import SSHCommandExecutor, DeploymentExecutor, CommandResult


def example_basic_usage():
    """基础使用示例"""
    print("=" * 60)
    print("示例1: 基础SSH连接和命令执行")
    print("=" * 60)

    # 初始化执行器
    executor = SSHCommandExecutor(
        host="43.143.139.197",
        username="ubuntu",
        private_key_path="enterprise_ai_platform.pem",  # 根据实际情况修改
        base_workdir="/opt/enterprise-ai-platform"
    )

    try:
        # 连接服务器
        executor.connect()

        # 执行单条命令
        result = executor.execute("ls -la")
        print(f"\n命令: {result.command}")
        print(f"退出码: {result.exit_code}")
        print(f"成功: {result.success}")
        print(f"输出:\n{result.stdout}")
        if result.stderr:
            print(f"错误:\n{result.stderr}")
        print(f"耗时: {result.duration:.2f}秒")

    except Exception as e:
        print(f"执行失败: {e}")
    finally:
        executor.close()


def example_sequence_execution():
    """命令序列执行示例"""
    print("\n" + "=" * 60)
    print("示例2: 执行命令序列")
    print("=" * 60)

    executor = SSHCommandExecutor(
        host="43.143.139.197",
        username="ubuntu",
        private_key_path="enterprise_ai_platform.pem",
        base_workdir="/opt/enterprise-ai-platform"
    )

    try:
        commands = [
            "pwd",
            "whoami",
            "date",
            "docker compose ps"
        ]

        results = executor.execute_sequence(commands, stop_on_failure=False)

        print(f"\n执行了 {len(results)} 条命令:")
        for i, result in enumerate(results, 1):
            status = "✓" if result.success else "✗"
            print(f"{status} [{i}] {result.command} (退出码: {result.exit_code})")
            if result.stdout:
                print(f"   输出: {result.stdout[:100]}...")

    except Exception as e:
        print(f"执行失败: {e}")
    finally:
        executor.close()


def example_streaming_output():
    """流式输出示例"""
    print("\n" + "=" * 60)
    print("示例3: 流式输出（实时显示命令输出）")
    print("=" * 60)

    executor = SSHCommandExecutor(
        host="43.143.139.197",
        username="ubuntu",
        private_key_path="enterprise_ai_platform.pem",
        base_workdir="/opt/enterprise-ai-platform"
    )

    try:
        def print_line(line: str):
            """实时输出回调"""
            print(f"  {line}")

        result = executor.execute_streaming(
            "docker compose logs --tail=10 web-ui",
            callback=print_line
        )

        print(f"\n命令执行完成，退出码: {result.exit_code}")

    except Exception as e:
        print(f"执行失败: {e}")
    finally:
        executor.close()


def example_file_transfer():
    """文件传输示例"""
    print("\n" + "=" * 60)
    print("示例4: 文件上传和下载")
    print("=" * 60)

    executor = SSHCommandExecutor(
        host="43.143.139.197",
        username="ubuntu",
        private_key_path="enterprise_ai_platform.pem",
        base_workdir="/opt/enterprise-ai-platform"
    )

    try:
        # 上传文件
        local_file = "test.txt"
        if os.path.exists(local_file):
            success = executor.upload_file(local_file, "test_uploaded.txt")
            print(f"文件上传: {'成功' if success else '失败'}")
        else:
            print(f"本地文件不存在: {local_file}")

        # 下载文件
        remote_file = "docker-compose.yml"
        local_save = "docker-compose_downloaded.yml"
        success = executor.download_file(remote_file, local_save)
        print(f"文件下载: {'成功' if success else '失败'}")
        if success and os.path.exists(local_save):
            print(f"下载的文件大小: {os.path.getsize(local_save)} 字节")

    except Exception as e:
        print(f"执行失败: {e}")
    finally:
        executor.close()


def example_deployment_executor():
    """部署执行器示例"""
    print("\n" + "=" * 60)
    print("示例5: 使用部署执行器")
    print("=" * 60)

    executor = DeploymentExecutor(
        host="43.143.139.197",
        username="ubuntu",
        private_key_path="enterprise_ai_platform.pem",
        base_workdir="/opt/enterprise-ai-platform"
    )

    try:
        # 检查服务状态
        print("\n1. 检查服务状态:")
        result = executor.check_service_status()
        print(result.stdout)

        # 查看日志
        print("\n2. 查看web-ui服务日志:")
        result = executor.view_logs("web-ui", lines=10)
        print(result.stdout)

        # 重启服务（注释掉，避免实际执行）
        # print("\n3. 重启服务:")
        # result = executor.restart_service("web-ui")
        # print(f"重启结果: {'成功' if result.success else '失败'}")

    except Exception as e:
        print(f"执行失败: {e}")
    finally:
        executor.close()


def example_context_manager():
    """上下文管理器示例"""
    print("\n" + "=" * 60)
    print("示例6: 使用上下文管理器（推荐方式）")
    print("=" * 60)

    # 使用 with 语句，自动管理连接
    with SSHCommandExecutor(
        host="43.143.139.197",
        username="ubuntu",
        private_key_path="enterprise_ai_platform.pem",
        base_workdir="/opt/enterprise-ai-platform"
    ) as executor:
        result = executor.execute("echo 'Hello from SSH!'")
        print(f"输出: {result.stdout}")
        # 退出 with 块时自动关闭连接


def example_project_specific():
    """项目特定操作示例"""
    print("\n" + "=" * 60)
    print("示例7: 项目特定操作")
    print("=" * 60)

    executor = SSHCommandExecutor(
        host="43.143.139.197",
        username="ubuntu",
        private_key_path="enterprise_ai_platform.pem",
        base_workdir="/opt/enterprise-ai-platform"
    )

    try:
        project_id = "test-project"

        # 在项目目录下执行命令
        result = executor.execute("pwd", project_id=project_id)
        print(f"项目目录: {result.stdout}")

        # 创建项目文件
        result = executor.execute("echo 'test content' > test.txt", project_id=project_id)
        print(f"创建文件: {'成功' if result.success else '失败'}")

        # 列出项目文件
        result = executor.execute("ls -la", project_id=project_id)
        print(f"项目文件:\n{result.stdout}")

    except Exception as e:
        print(f"执行失败: {e}")
    finally:
        executor.close()


def example_agent_integration():
    """智能体集成示例"""
    print("\n" + "=" * 60)
    print("示例8: 智能体集成示例")
    print("=" * 60)

    class DevelopmentAgent:
        """开发智能体 - 负责代码生成和部署"""

        def __init__(self, server_config: Dict):
            self.executor = DeploymentExecutor(
                host=server_config['host'],
                username=server_config['username'],
                private_key_path=server_config['private_key_path'],
                base_workdir=server_config.get('base_workdir', '/opt/enterprise-ai-platform')
            )

        def deploy_feature(self, project_id: str, branch: str = "main") -> Dict[str, Any]:
            """部署功能特性"""
            try:
                results = self.executor.deploy_project(project_id, branch)

                success_count = sum(1 for r in results if r.success)
                total_count = len(results)

                return {
                    "success": all(r.success for r in results),
                    "project_id": project_id,
                    "commands_executed": total_count,
                    "commands_succeeded": success_count,
                    "details": [{
                        "command": r.command,
                        "exit_code": r.exit_code,
                        "stdout": r.stdout[:200],  # 限制输出长度
                        "stderr": r.stderr[:200]
                    } for r in results],
                    "summary": f"执行了 {total_count} 条命令，成功 {success_count} 条"
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
            finally:
                self.executor.close()

    # 使用示例
    server_config = {
        "host": "43.143.139.197",
        "username": "ubuntu",
        "private_key_path": "enterprise_ai_platform.pem",
        "base_workdir": "/opt/enterprise-ai-platform"
    }

    agent = DevelopmentAgent(server_config)
    result = agent.deploy_feature("test-project", "main")

    print(f"部署结果: {result['success']}")
    print(f"摘要: {result['summary']}")
    if not result['success']:
        print(f"错误: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SSHCommandExecutor 使用示例")
    print("=" * 60)
    print("\n注意: 请确保:")
    print("1. SSH密钥文件路径正确")
    print("2. 服务器地址和用户名正确")
    print("3. 网络连接正常")
    print("\n选择要运行的示例:")
    print("1. 基础使用")
    print("2. 命令序列执行")
    print("3. 流式输出")
    print("4. 文件传输")
    print("5. 部署执行器")
    print("6. 上下文管理器")
    print("7. 项目特定操作")
    print("8. 智能体集成")
    print("0. 运行所有示例（跳过需要实际操作的）")

    choice = input("\n请输入选择 (0-8): ").strip()

    examples = {
        "1": example_basic_usage,
        "2": example_sequence_execution,
        "3": example_streaming_output,
        "4": example_file_transfer,
        "5": example_deployment_executor,
        "6": example_context_manager,
        "7": example_project_specific,
        "8": example_agent_integration,
    }

    if choice == "0":
        # 运行所有示例（跳过需要实际文件操作的）
        example_basic_usage()
        example_sequence_execution()
        example_deployment_executor()
        example_context_manager()
        example_project_specific()
    elif choice in examples:
        examples[choice]()
    else:
        print("无效的选择")

