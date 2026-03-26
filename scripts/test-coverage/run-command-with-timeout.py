#!/usr/bin/env python3
"""
命令执行器（带超时）
执行Windows命令，支持超时和自动重试
"""
import subprocess
import sys
import time
from typing import Optional, Tuple


class CommandResult:
    """命令执行结果"""
    def __init__(self, returncode: int, stdout: str, stderr: str, elapsed_time: float):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.elapsed_time = elapsed_time
        self.success = returncode == 0
    
    def __repr__(self):
        return f"CommandResult(returncode={self.returncode}, success={self.success}, elapsed={self.elapsed_time:.2f}s)"


def run_command_with_timeout(
    cmd: str,
    timeout: int = 10,
    max_retries: int = 3,
    shell: bool = True,
    cwd: Optional[str] = None,
    env: Optional[dict] = None
) -> CommandResult:
    """
    执行命令，带超时和自动重试
    
    Args:
        cmd: 要执行的命令
        timeout: 超时时间（秒），默认10秒
        max_retries: 最大重试次数，默认3次
        shell: 是否使用shell执行，默认True
        cwd: 工作目录
        env: 环境变量
        
    Returns:
        CommandResult对象，包含执行结果
        
    Raises:
        subprocess.TimeoutExpired: 如果所有重试都超时
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            
            result = subprocess.run(
                cmd,
                shell=shell,
                timeout=timeout,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=cwd,
                env=env
            )
            
            elapsed_time = time.time() - start_time
            
            return CommandResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                elapsed_time=elapsed_time
            )
            
        except subprocess.TimeoutExpired as e:
            last_exception = e
            if attempt < max_retries - 1:
                # 重试前等待一小段时间
                time.sleep(0.5)
                continue
            else:
                # 最后一次重试也超时，抛出异常
                raise subprocess.TimeoutExpired(
                    cmd=cmd,
                    timeout=timeout,
                    output=getattr(e, 'output', ''),
                    stderr=getattr(e, 'stderr', '')
                )
        except Exception as e:
            # 其他异常也重试
            last_exception = e
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue
            else:
                raise
    
    # 如果所有重试都失败，返回错误结果
    return CommandResult(
        returncode=1,
        stdout="",
        stderr=f"命令执行失败: {str(last_exception)}",
        elapsed_time=0.0
    )


def run_command_safe(
    cmd: str,
    timeout: int = 10,
    max_retries: int = 3,
    **kwargs
) -> CommandResult:
    """
    安全执行命令，捕获所有异常
    
    Args:
        cmd: 要执行的命令
        timeout: 超时时间（秒）
        max_retries: 最大重试次数
        **kwargs: 其他参数传递给run_command_with_timeout
        
    Returns:
        CommandResult对象，即使出错也会返回结果
    """
    try:
        return run_command_with_timeout(cmd, timeout, max_retries, **kwargs)
    except subprocess.TimeoutExpired as e:
        return CommandResult(
            returncode=124,  # timeout退出码
            stdout=getattr(e, 'output', '') or '',
            stderr=getattr(e, 'stderr', '') or f"命令超时（{timeout}秒）",
            elapsed_time=timeout
        )
    except Exception as e:
        return CommandResult(
            returncode=1,
            stdout="",
            stderr=f"命令执行异常: {str(e)}",
            elapsed_time=0.0
        )


def main():
    """主函数，用于测试"""
    import argparse
    
    parser = argparse.ArgumentParser(description="执行命令（带超时）")
    parser.add_argument("command", help="要执行的命令")
    parser.add_argument("--timeout", type=int, default=10, help="超时时间（秒）")
    parser.add_argument("--retries", type=int, default=3, help="最大重试次数")
    parser.add_argument("--safe", action="store_true", help="安全模式，捕获所有异常")
    
    args = parser.parse_args()
    
    if args.safe:
        result = run_command_safe(args.command, args.timeout, args.retries)
    else:
        result = run_command_with_timeout(args.command, args.timeout, args.retries)
    
    print(f"返回码: {result.returncode}")
    print(f"执行时间: {result.elapsed_time:.2f}秒")
    print(f"成功: {result.success}")
    
    if result.stdout:
        print("\n标准输出:")
        print(result.stdout)
    
    if result.stderr:
        print("\n错误输出:")
        print(result.stderr, file=sys.stderr)
    
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

