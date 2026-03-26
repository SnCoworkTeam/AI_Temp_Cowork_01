#!/usr/bin/env python3
"""
Cursor任务监控脚本
检测Cursor是否卡住，如果卡住则自动发送继续执行指令
"""
import time
import re
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import json

# 尝试导入pyautogui，如果失败则使用替代方案
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("警告: pyautogui未安装，将使用文件方式发送指令")

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent


class CursorMonitor:
    def __init__(self, check_interval=30, timeout_threshold=300):
        """
        初始化监控器
        
        Args:
            check_interval: 检查间隔(秒)，默认30秒
            timeout_threshold: 超时阈值(秒)，默认300秒(5分钟)
        """
        self.check_interval = check_interval
        self.timeout_threshold = timeout_threshold
        self.last_activity_time = time.time()
        self.monitoring = False
        self.activity_file = PROJECT_ROOT / ".cursor-activity.log"
        self.instruction_file = PROJECT_ROOT / "continue-coverage-improvement.txt"
        
        # 卡住检测模式
        self.stuck_patterns = [
            r"卡住|stuck|hanging|freeze|冻结",
            r"连接中|connecting",
            r"等待|waiting",
            r"超时|timeout",
            r"错误|error|失败|fail"
        ]
    
    def log_activity(self, message: str):
        """记录活动日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        try:
            with open(self.activity_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"记录日志失败: {e}")
    
    def update_activity_time(self):
        """更新活动时间"""
        self.last_activity_time = time.time()
        self.log_activity("活动时间已更新")
    
    def send_continue_instruction(self):
        """发送继续执行指令"""
        instruction = """继续执行测试覆盖率提升计划，为所有未达到80%覆盖率的服务添加测试，直到所有服务都达到80%覆盖率。"""
        
        try:
            # 方法1: 写入指令文件
            with open(self.instruction_file, 'w', encoding='utf-8') as f:
                f.write(instruction)
            
            self.log_activity(f"已创建继续执行指令文件: {self.instruction_file}")
            print(f"✅ 已创建继续执行指令文件")
            print(f"📄 文件路径: {self.instruction_file}")
            print(f"📝 指令内容: {instruction}")
            
            # 方法2: 如果pyautogui可用，尝试直接发送
            if PYAUTOGUI_AVAILABLE:
                try:
                    # 等待一下，确保Cursor窗口在前台
                    time.sleep(2)
                    
                    # 发送指令（需要Cursor窗口处于活动状态）
                    pyautogui.write(instruction, interval=0.05)
                    pyautogui.press('enter')
                    
                    self.log_activity("已通过pyautogui发送指令")
                    print("✅ 已通过pyautogui发送指令到Cursor")
                except Exception as e:
                    self.log_activity(f"pyautogui发送失败: {e}")
                    print(f"⚠️ pyautogui发送失败，已使用文件方式: {e}")
            
            # 方法3: 创建标记文件，让其他脚本检测
            marker_file = PROJECT_ROOT / ".cursor-continue-requested"
            with open(marker_file, 'w', encoding='utf-8') as f:
                f.write(datetime.now().isoformat())
            
            return True
            
        except Exception as e:
            self.log_activity(f"发送指令失败: {e}")
            print(f"❌ 发送指令失败: {e}")
            return False
    
    def check_activity_file(self) -> bool:
        """检查活动文件，判断是否有新活动"""
        try:
            if not self.activity_file.exists():
                return False
            
            # 检查文件最后修改时间
            file_mtime = os.path.getmtime(self.activity_file)
            current_time = time.time()
            
            # 如果文件在最近1分钟内被修改，认为有活动
            if current_time - file_mtime < 60:
                return True
                
        except Exception as e:
            print(f"检查活动文件失败: {e}")
        
        return False
    
    def check_coverage_progress(self) -> bool:
        """检查测试覆盖率提升进度"""
        try:
            # 检查是否有覆盖率检查脚本的输出
            coverage_script = PROJECT_ROOT / "scripts" / "test-coverage" / "check-coverage-status.py"
            if not coverage_script.exists():
                return True  # 如果脚本不存在，假设需要继续
            
            # 可以运行快速检查（可选）
            # 这里简化处理，只检查标记文件
            
            return True
            
        except Exception as e:
            print(f"检查覆盖率进度失败: {e}")
            return True
    
    def check_for_stuck_indicators(self) -> bool:
        """检查是否卡住"""
        try:
            current_time = time.time()
            time_since_activity = current_time - self.last_activity_time
            
            # 检查时间阈值
            if time_since_activity > self.timeout_threshold:
                self.log_activity(f"检测到超时: {time_since_activity:.0f}秒未活动")
                return True
            
            # 检查活动文件
            if self.check_activity_file():
                self.update_activity_time()
                return False
            
            # 检查覆盖率进度
            if not self.check_coverage_progress():
                self.log_activity("覆盖率提升可能已完成")
                return False
                
        except Exception as e:
            self.log_activity(f"检测错误: {e}")
            print(f"检测错误: {e}")
        
        return False
    
    def monitor_loop(self):
        """监控循环"""
        self.log_activity("监控循环启动")
        print(f"🔍 监控循环启动 (检查间隔: {self.check_interval}秒, 超时阈值: {self.timeout_threshold}秒)")
        
        while self.monitoring:
            try:
                if self.check_for_stuck_indicators():
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"\n🚨 [{timestamp}] 检测到任务可能卡住")
                    self.log_activity("检测到任务可能卡住，发送继续执行指令")
                    
                    if self.send_continue_instruction():
                        self.update_activity_time()
                        print("✅ 已发送继续执行指令\n")
                    else:
                        print("❌ 发送指令失败\n")
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                self.log_activity("收到中断信号")
                print("\n⏹️ 收到中断信号，停止监控")
                break
            except Exception as e:
                self.log_activity(f"监控循环错误: {e}")
                print(f"监控循环错误: {e}")
                time.sleep(self.check_interval)
    
    def start_monitoring(self):
        """开始监控"""
        self.monitoring = True
        self.last_activity_time = time.time()
        self.log_activity("Cursor任务监控启动")
        
        # 在后台线程运行监控循环
        import threading
        monitor_thread = threading.Thread(target=self.monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        print("=" * 50)
        print("🔍 Cursor任务监控已启动")
        print(f"   检查间隔: {self.check_interval}秒")
        print(f"   超时阈值: {self.timeout_threshold}秒 ({self.timeout_threshold/60:.1f}分钟)")
        print(f"   活动日志: {self.activity_file}")
        print(f"   指令文件: {self.instruction_file}")
        print("=" * 50)
        print("\n提示: 按 Ctrl+C 停止监控\n")
        
        return monitor_thread
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        self.log_activity("Cursor任务监控停止")
        print("⏹️ Cursor任务监控已停止")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cursor任务监控脚本")
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="检查间隔(秒)，默认30秒"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="超时阈值(秒)，默认300秒(5分钟)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="只检查一次然后退出"
    )
    
    args = parser.parse_args()
    
    monitor = CursorMonitor(
        check_interval=args.interval,
        timeout_threshold=args.timeout
    )
    
    if args.once:
        # 单次检查模式
        print("执行单次检查...")
        if monitor.check_for_stuck_indicators():
            monitor.send_continue_instruction()
    else:
        # 持续监控模式
        monitor_thread = monitor.start_monitoring()
        
        try:
            # 保持主线程运行
            while monitor.monitoring:
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop_monitoring()
            print("\n程序已退出")


if __name__ == "__main__":
    main()

