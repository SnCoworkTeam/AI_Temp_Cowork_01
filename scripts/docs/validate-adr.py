#!/usr/bin/env python3
"""
ADR验证工具
验证ADR文件的完整性和格式
"""
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

# 项目根目录
project_root = Path(__file__).parent.parent.parent
adr_dir = project_root / "docs" / "architecture-docs" / "decision-records"


class ADRValidator:
    """ADR验证器"""
    
    REQUIRED_SECTIONS = [
        r"^#\s+ADR-\d+",
        r"^\*\*状态\*\*",
        r"^\*\*日期\*\*",
        r"^\*\*作者\*\*",
        r"^##\s+1\.\s+决策背景和问题陈述",
        r"^##\s+2\.\s+考虑的方案",
        r"^##\s+3\.\s+决策结果",
        r"^##\s+4\.\s+影响和后果",
    ]
    
    OPTIONAL_SECTIONS = [
        r"^##\s+5\.\s+实施计划",
        r"^##\s+6\.\s+验证和监控",
        r"^##\s+7\.\s+相关决策和链接",
        r"^##\s+8\.\s+附录",
    ]
    
    VALID_STATUSES = ["提议", "已接受", "已弃用", "已替代"]
    
    def __init__(self, adr_dir: Path):
        self.adr_dir = adr_dir
        self.errors = []
        self.warnings = []
    
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """验证所有ADR文件"""
        if not self.adr_dir.exists():
            self.errors.append(f"ADR目录不存在: {self.adr_dir}")
            return False, self.errors, self.warnings
        
        adr_files = list(self.adr_dir.glob("*.md"))
        adr_files = [f for f in adr_files if f.name not in ["README.md", "adr-template.md", "0001-record-architecture-decisions.md"]]
        
        if not adr_files:
            self.warnings.append("未找到ADR文件（除了模板和说明）")
        
        for adr_file in adr_files:
            self.validate_file(adr_file)
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def validate_file(self, adr_file: Path):
        """验证单个ADR文件"""
        try:
            content = adr_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # 检查文件名格式
            if not re.match(r'^\d{4}-.*\.md$', adr_file.name):
                self.errors.append(f"{adr_file.name}: 文件名格式不正确，应为0001-title.md格式")
            
            # 检查必需部分
            self._check_required_sections(adr_file.name, content)
            
            # 检查元数据
            self._check_metadata(adr_file.name, content)
            
            # 检查ADR编号一致性
            self._check_adr_number(adr_file.name, content)
            
        except Exception as e:
            self.errors.append(f"{adr_file.name}: 文件读取错误 - {e}")
    
    def _check_required_sections(self, filename: str, content: str):
        """检查必需部分"""
        for section_pattern in self.REQUIRED_SECTIONS:
            if not re.search(section_pattern, content, re.MULTILINE):
                section_name = section_pattern.replace(r'\s+', ' ').replace('^', '').replace(r'\.', '.')
                self.errors.append(f"{filename}: 缺少必需部分: {section_name}")
    
    def _check_metadata(self, filename: str, content: str):
        """检查元数据"""
        # 检查状态
        status_match = re.search(r'\*\*状态\*\*:\s*([^\n]+)', content)
        if status_match:
            status = status_match.group(1).strip()
            if status not in self.VALID_STATUSES:
                self.errors.append(f"{filename}: 无效的状态值: {status}，应为: {', '.join(self.VALID_STATUSES)}")
        else:
            self.errors.append(f"{filename}: 缺少状态字段")
        
        # 检查日期格式
        date_match = re.search(r'\*\*日期\*\*:\s*([^\n]+)', content)
        if date_match:
            date_str = date_match.group(1).strip()
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                self.warnings.append(f"{filename}: 日期格式可能不正确: {date_str}，应为YYYY-MM-DD")
        else:
            self.errors.append(f"{filename}: 缺少日期字段")
        
        # 检查作者
        author_match = re.search(r'\*\*作者\*\*:\s*([^\n]+)', content)
        if not author_match:
            self.warnings.append(f"{filename}: 缺少作者字段")
    
    def _check_adr_number(self, filename: str, content: str):
        """检查ADR编号一致性"""
        # 从文件名提取编号
        filename_match = re.match(r'^(\d{4})', filename)
        if filename_match:
            file_number = filename_match.group(1)
            
            # 从内容提取ADR编号
            content_match = re.search(r'^#\s+ADR-(\d+)', content, re.MULTILINE)
            if content_match:
                content_number = content_match.group(1).lstrip('0') or '0'
                file_number_clean = file_number.lstrip('0') or '0'
                
                if content_number != file_number_clean:
                    self.errors.append(
                        f"{filename}: ADR编号不一致 - 文件名: {file_number}, 内容: ADR-{content_match.group(1)}"
                    )
            else:
                self.errors.append(f"{filename}: 内容中缺少ADR编号")


def validate_adr_completeness():
    """验证ADR完整性"""
    validator = ADRValidator(adr_dir)
    success, errors, warnings = validator.validate_all()
    
    if warnings:
        print("⚠️  警告:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if errors:
        print("\n❌ 错误:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    if not warnings and not errors:
        print("✅ 所有ADR文件验证通过")
    
    return success


def list_adrs():
    """列出所有ADR"""
    if not adr_dir.exists():
        print("ADR目录不存在")
        return
    
    adr_files = sorted(adr_dir.glob("*.md"))
    adr_files = [f for f in adr_files if f.name not in ["README.md", "adr-template.md"]]
    
    print(f"\n找到 {len(adr_files)} 个ADR文件:\n")
    
    for adr_file in adr_files:
        try:
            content = adr_file.read_text(encoding='utf-8')
            
            # 提取标题
            title_match = re.search(r'^#\s+ADR-\d+:\s*(.+)$', content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else "未知标题"
            
            # 提取状态
            status_match = re.search(r'\*\*状态\*\*:\s*([^\n]+)', content)
            status = status_match.group(1).strip() if status_match else "未知"
            
            # 提取日期
            date_match = re.search(r'\*\*日期\*\*:\s*([^\n]+)', content)
            date = date_match.group(1).strip() if date_match else "未知"
            
            print(f"  {adr_file.name}")
            print(f"    标题: {title}")
            print(f"    状态: {status}")
            print(f"    日期: {date}")
            print()
        except Exception as e:
            print(f"  {adr_file.name}: 读取错误 - {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ADR验证工具")
    parser.add_argument("--list", action="store_true", help="列出所有ADR")
    parser.add_argument("--validate", action="store_true", help="验证ADR完整性")
    
    args = parser.parse_args()
    
    if args.list:
        list_adrs()
    elif args.validate:
        success = validate_adr_completeness()
        sys.exit(0 if success else 1)
    else:
        # 默认验证
        success = validate_adr_completeness()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()









