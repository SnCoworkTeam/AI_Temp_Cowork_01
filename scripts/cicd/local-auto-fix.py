#!/usr/bin/env python3
"""
本地自动修复系统（Python版本）
可以在venv或Docker中运行
"""

import os
import re
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

class LocalAutoFix:
    def __init__(self, project_dir: str = None):
        self.project_dir = Path(project_dir) if project_dir else Path(__file__).parent.parent.parent
        self.repo = "PMLiuyubin/enterprise-ai-platform"
        self.workflow = "deploy.yml"
        self.log_dir = Path(os.getenv("TEMP", "/tmp")) / "github-errors"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def get_latest_failed_run(self) -> Optional[str]:
        """获取最新失败的运行ID"""
        try:
            result = subprocess.run(
                ["gh", "run", "list", "--workflow", self.workflow, 
                 "--repo", self.repo, "--limit", "10", 
                 "--json", "databaseId,status,conclusion"],
                capture_output=True,
                text=True,
                check=True
            )
            
            runs = json.loads(result.stdout)
            for run in runs:
                if run.get("conclusion") == "failure":
                    return str(run["databaseId"])
            return None
        except subprocess.CalledProcessError as e:
            print(f"❌ 获取运行列表失败: {e}")
            return None
    
    def download_logs(self, run_id: str) -> Path:
        """下载运行日志"""
        log_dir = self.log_dir / f"run-{run_id}"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"下载运行 {run_id} 的日志...")
        
        try:
            # 获取所有作业
            result = subprocess.run(
                ["gh", "run", "view", run_id, "--repo", self.repo,
                 "--json", "jobs", "--jq", ".jobs[] | .name"],
                capture_output=True,
                text=True,
                check=True
            )
            
            jobs = result.stdout.strip().split('\n')
            
            for job in jobs:
                if not job:
                    continue
                print(f"  下载: {job}")
                # 清理文件名中的非法字符
                safe_job_name = re.sub(r'[<>:"/\\|?*$]', '_', job)
                log_file = log_dir / f"{safe_job_name}.log"
                
                with open(log_file, "w", encoding="utf-8") as f:
                    subprocess.run(
                        ["gh", "run", "view", run_id, "--repo", self.repo,
                         "--log", "--job", job],
                        stdout=f,
                        stderr=subprocess.DEVNULL
                    )
            
            return log_dir
        except subprocess.CalledProcessError as e:
            print(f"❌ 下载日志失败: {e}")
            return log_dir
    
    def extract_typescript_errors(self, log_file: Path) -> List[Dict]:
        """提取TypeScript错误"""
        errors = []
        
        if not log_file.exists():
            return errors
        
        content = log_file.read_text(encoding="utf-8", errors="ignore")
        
        # 匹配TypeScript错误模式
        pattern = r'\./(src/[^:]+):(\d+):(\d+)\s+Type error:\s*(.+)'
        matches = re.finditer(pattern, content, re.MULTILINE)
        
        for match in matches:
            errors.append({
                "type": "typescript",
                "file": match.group(1),
                "line": int(match.group(2)),
                "column": int(match.group(3)),
                "message": match.group(4).strip()
            })
        
        return errors
    
    def fix_display_name(self, file_path: Path) -> bool:
        """修复display_name缺失"""
        if not file_path.exists():
            return False
        
        content = file_path.read_text(encoding="utf-8")
        
        if "display_name" in content:
            return False
        
        # 在session_id后添加display_name
        content = re.sub(
            r'(session_id\?: string)',
            r'\1\n  display_name?: string',
            content
        )
        
        file_path.write_text(content, encoding="utf-8")
        return True
    
    def fix_missing_import(self, file_path: Path, import_name: str) -> bool:
        """修复缺失的导入"""
        if not file_path.exists():
            return False
        
        content = file_path.read_text(encoding="utf-8")
        
        if import_name in content:
            return False
        
        # 查找lucide-react导入
        pattern = r"(from ['\"]lucide-react['\"];?)"
        match = re.search(pattern, content)
        
        if match:
            # 查找导入块
            import_block_pattern = r"import\s*\{([^}]+)\}\s*from\s*['\"]lucide-react['\"]"
            import_match = re.search(import_block_pattern, content)
            
            if import_match:
                imports = import_match.group(1)
                # 添加新导入
                new_imports = f"{imports},\n  {import_name}"
                content = content.replace(import_match.group(0), 
                                        f"import {{{new_imports}}} from 'lucide-react'")
                file_path.write_text(content, encoding="utf-8")
                return True
        
        return False
    
    def fix_type_mismatch(self, file_path: Path, line_num: int) -> bool:
        """修复类型不匹配（移除错误的else分支）"""
        if not file_path.exists():
            return False
        
        lines = file_path.read_text(encoding="utf-8").split('\n')
        
        # 查找包含错误的行
        if line_num > len(lines):
            return False
        
        error_line = lines[line_num - 1]
        
        # 如果是stat.icon相关的错误，查找并修复if-else块
        if 'stat.icon' in error_line and '<span' in error_line:
            # 查找对应的if-else块
            for i in range(max(0, line_num - 20), min(len(lines), line_num + 5)):
                if 'IconComponent' in lines[i] and '?' in lines[i]:
                    # 找到if-else块，移除else部分
                    for j in range(i, min(len(lines), i + 10)):
                        if 'else' in lines[j] or ('stat.icon' in lines[j] and '<span' in lines[j]):
                            # 移除else分支
                            lines[j] = ""
                            if j + 1 < len(lines) and lines[j + 1].strip().startswith('<span'):
                                lines[j + 1] = ""
                            if j + 2 < len(lines) and '</span>' in lines[j + 2]:
                                lines[j + 2] = ""
                            # 修复if条件
                            if '?' in lines[i]:
                                lines[i] = lines[i].replace('?', '&&').replace(':', '')
                            file_path.write_text('\n'.join(lines), encoding="utf-8")
                            return True
        
        return False
    
    def auto_fix_errors(self, errors: List[Dict]) -> bool:
        """自动修复错误"""
        fixed = False
        
        for error in errors:
            file_path = self.project_dir / "web-ui" / error["file"]
            message = error["message"]
            
            print(f"修复: {error['file']}:{error['line']} - {message}")
            
            # 修复1: display_name
            if "display_name" in message and "does not exist" in message:
                if self.fix_display_name(file_path):
                    print("  ✅ 已添加display_name")
                    fixed = True
            
            # 修复2: 缺失导入
            match = re.search(r"Cannot find name '(\w+)'", message)
            if match:
                import_name = match.group(1)
                if self.fix_missing_import(file_path, import_name):
                    print(f"  ✅ 已添加导入: {import_name}")
                    fixed = True
            
            # 修复3: 类型不匹配
            if "is not assignable" in message:
                if self.fix_type_mismatch(file_path, error["line"]):
                    print("  ✅ 已修复类型错误")
                    fixed = True
        
        return fixed
    
    def verify_fixes(self) -> bool:
        """验证修复"""
        print("验证修复...")
        
        web_ui_dir = self.project_dir / "web-ui"
        os.chdir(web_ui_dir)
        
        try:
            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print("❌ 类型检查仍有错误")
                print(result.stdout)
                return False
            
            print("✅ 类型检查通过")
            return True
        finally:
            os.chdir(self.project_dir)
    
    def commit_fixes(self, run_id: str) -> bool:
        """提交修复"""
        print("提交修复...")
        
        # 检查是否有更改
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True
        )
        
        if not result.stdout.strip():
            print("⚠️ 没有更改需要提交")
            return False
        
        # 添加所有更改
        subprocess.run(["git", "add", "-A"], check=True)
        
        # 提交
        commit_message = f"""fix: 自动修复CI/CD错误

- 从GitHub Actions运行 {run_id} 提取错误
- 自动应用修复
- 修复时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            check=True
        )
        
        # 推送
        print("推送到远程...")
        subprocess.run(["git", "push", "origin", "main"], check=True)
        
        print("✅ 修复已提交并推送")
        return True
    
    def run(self):
        """运行自动修复"""
        print("=" * 50)
        print("本地自动修复系统")
        print("=" * 50)
        print()
        
        # 1. 获取最新失败运行
        print("[1/5] 查找最新失败运行...")
        run_id = self.get_latest_failed_run()
        
        if not run_id:
            print("✅ 没有失败的运行")
            return
        
        print(f"找到失败运行: {run_id}")
        
        # 2. 下载日志
        print("[2/5] 下载日志...")
        log_dir = self.download_logs(run_id)
        
        # 3. 提取错误
        print("[3/5] 提取并分析错误...")
        # 查找前端测试日志（可能有不同的名称）
        frontend_log = None
        for log_file in log_dir.glob("*.log"):
            if "frontend" in log_file.name.lower() or "Frontend" in log_file.name:
                frontend_log = log_file
                break
        
        if not frontend_log:
            # 尝试查找包含test的日志
            for log_file in log_dir.glob("*test*.log"):
                frontend_log = log_file
                break
        errors = []
        
        if frontend_log.exists():
            errors = self.extract_typescript_errors(frontend_log)
            print(f"发现 {len(errors)} 个TypeScript错误")
        
        if not errors:
            print("✅ 未发现可自动修复的错误")
            return
        
        # 4. 应用修复
        print("[4/5] 应用自动修复...")
        if not self.auto_fix_errors(errors):
            print("⚠️ 无法自动修复所有错误")
            return
        
        # 5. 验证修复
        print("[5/5] 验证修复...")
        if not self.verify_fixes():
            print("❌ 修复验证失败")
            return
        
        # 6. 提交
        if self.commit_fixes(run_id):
            print()
            print("✅ 修复完成！")
            print(f"查看新运行: https://github.com/{self.repo}/actions")

if __name__ == "__main__":
    fixer = LocalAutoFix()
    fixer.run()

