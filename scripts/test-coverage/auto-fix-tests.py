#!/usr/bin/env python3
"""
自动修复测试中的常见错误
分析测试失败原因并自动修复
"""
import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# 需要人工修复的问题记录文件
FIXES_NEEDED_FILE = PROJECT_ROOT / "test-fixes-needed.md"


class TestErrorFixer:
    """测试错误修复器"""
    
    def __init__(self):
        self.fixes_applied = []
        self.fixes_needed = []
    
    def analyze_error(self, error_message: str, test_file: Path) -> Optional[str]:
        """
        分析错误消息，返回错误类型
        
        Returns:
            错误类型: 'import_error', 'syntax_error', 'type_error', 'missing_dependency', 'other'
        """
        error_lower = error_message.lower()
        
        # 导入错误
        if any(keyword in error_lower for keyword in ['module not found', 'cannot import', 'import error', 'no module named']):
            return 'import_error'
        
        # 语法错误
        if any(keyword in error_lower for keyword in ['syntax error', 'invalid syntax', 'unexpected token']):
            return 'syntax_error'
        
        # 类型错误
        if any(keyword in error_lower for keyword in ['type error', 'attribute error', 'has no attribute']):
            return 'type_error'
        
        # 缺少依赖
        if any(keyword in error_lower for keyword in ['fixture', 'mock', 'pytest', 'not found']):
            return 'missing_dependency'
        
        return 'other'
    
    def fix_import_error(self, test_file: Path, error_message: str) -> bool:
        """修复导入错误"""
        try:
            content = test_file.read_text(encoding='utf-8')
            original_content = content
            
            # 提取缺失的模块名
            module_match = re.search(r"no module named ['\"]([^'\"]+)['\"]", error_message, re.IGNORECASE)
            if not module_match:
                module_match = re.search(r"cannot import name ['\"]([^'\"]+)['\"]", error_message, re.IGNORECASE)
            
            if module_match:
                missing_module = module_match.group(1)
                
                # 尝试修复常见的导入路径问题
                # 如果导入的是 src.xxx，可能需要改为相对导入
                if missing_module.startswith('src.'):
                    # 移除 src. 前缀，使用相对导入
                    new_import = missing_module.replace('src.', '')
                    content = re.sub(
                        rf'from\s+{re.escape(missing_module)}\s+import',
                        f'from {new_import} import',
                        content
                    )
                    content = re.sub(
                        rf'import\s+{re.escape(missing_module)}',
                        f'import {new_import}',
                        content
                    )
                
                # 添加项目路径到sys.path（如果还没有）
                if 'sys.path.insert' not in content and 'sys.path.append' not in content:
                    import_section = """import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "{service_name}" / "src"))
"""
                    # 尝试从文件路径推断服务名
                    service_name = "service"
                    for part in test_file.parts:
                        if part in ['auth-service', 'knowledge-base', 'metadata-service', 
                                   'workflow-engine', 'mcp-gateway', 'database']:
                            service_name = part
                            break
                    
                    import_section = import_section.replace("{service_name}", service_name)
                    
                    # 在文件开头添加
                    if content.startswith('"""') or content.startswith("'''"):
                        # 找到第一个import语句的位置
                        import_match = re.search(r'^import |^from ', content, re.MULTILINE)
                        if import_match:
                            insert_pos = import_match.start()
                            content = content[:insert_pos] + import_section + "\n" + content[insert_pos:]
                    else:
                        content = import_section + "\n" + content
            
            if content != original_content:
                test_file.write_text(content, encoding='utf-8')
                self.fixes_applied.append({
                    "file": str(test_file),
                    "error_type": "import_error",
                    "fix": "修复导入路径",
                    "timestamp": datetime.now().isoformat()
                })
                return True
            
        except Exception as e:
            self.fixes_needed.append({
                "file": str(test_file),
                "error_type": "import_error",
                "error": error_message,
                "reason": f"自动修复失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
        
        return False
    
    def fix_syntax_error(self, test_file: Path, error_message: str) -> bool:
        """修复语法错误"""
        try:
            content = test_file.read_text(encoding='utf-8')
            original_content = content
            
            # 修复常见的语法错误
            # 1. 缺少冒号
            content = re.sub(r'(def\s+\w+\([^)]*\))\s*$', r'\1:', content, flags=re.MULTILINE)
            content = re.sub(r'(class\s+\w+[^:]*)\s*$', r'\1:', content, flags=re.MULTILINE)
            content = re.sub(r'(if\s+[^:]+|elif\s+[^:]+|else|for\s+[^:]+|while\s+[^:]+|try|except|finally)\s*$', 
                           lambda m: m.group(0) + ':', content, flags=re.MULTILINE)
            
            # 2. 修复缩进问题（简单情况）
            # 这里只处理明显的缩进错误，复杂情况需要人工修复
            
            if content != original_content:
                test_file.write_text(content, encoding='utf-8')
                self.fixes_applied.append({
                    "file": str(test_file),
                    "error_type": "syntax_error",
                    "fix": "修复语法错误",
                    "timestamp": datetime.now().isoformat()
                })
                return True
            
        except Exception as e:
            self.fixes_needed.append({
                "file": str(test_file),
                "error_type": "syntax_error",
                "error": error_message,
                "reason": f"自动修复失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
        
        return False
    
    def fix_missing_dependency(self, test_file: Path, error_message: str) -> bool:
        """修复缺少依赖的问题"""
        try:
            content = test_file.read_text(encoding='utf-8')
            original_content = content
            
            # 如果缺少fixture，添加基本的fixture
            if 'fixture' in error_message.lower() and '@pytest.fixture' not in content:
                # 添加基本的fixture定义
                fixture_code = """
@pytest.fixture
def mock_db():
    \"\"\"模拟数据库会话\"\"\"
    from unittest.mock import MagicMock
    return MagicMock()

@pytest.fixture
def mock_request():
    \"\"\"模拟FastAPI请求\"\"\"
    from unittest.mock import MagicMock
    return MagicMock()
"""
                
                # 在第一个测试类之前插入
                class_match = re.search(r'^class\s+Test', content, re.MULTILINE)
                if class_match:
                    insert_pos = class_match.start()
                    content = content[:insert_pos] + fixture_code + "\n" + content[insert_pos:]
            
            # 如果缺少mock，添加mock导入
            if 'mock' in error_message.lower() and 'from unittest.mock import' not in content:
                import_line = "from unittest.mock import Mock, MagicMock, patch, AsyncMock\n"
                # 在第一个import之后添加
                import_match = re.search(r'^(import |from )', content, re.MULTILINE)
                if import_match:
                    # 找到最后一个import语句
                    imports = list(re.finditer(r'^(import |from )', content, re.MULTILINE))
                    if imports:
                        last_import = imports[-1]
                        # 找到这一行的结束
                        line_end = content.find('\n', last_import.end())
                        if line_end != -1:
                            content = content[:line_end+1] + import_line + content[line_end+1:]
            
            if content != original_content:
                test_file.write_text(content, encoding='utf-8')
                self.fixes_applied.append({
                    "file": str(test_file),
                    "error_type": "missing_dependency",
                    "fix": "添加缺失的依赖",
                    "timestamp": datetime.now().isoformat()
                })
                return True
            
        except Exception as e:
            self.fixes_needed.append({
                "file": str(test_file),
                "error_type": "missing_dependency",
                "error": error_message,
                "reason": f"自动修复失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
        
        return False
    
    def fix_type_error(self, test_file: Path, error_message: str) -> bool:
        """修复类型错误"""
        try:
            content = test_file.read_text(encoding='utf-8')
            original_content = content
            
            # 修复常见的类型错误
            # 1. 缺少类型注解
            # 2. 属性访问错误
            
            # 如果错误提到某个属性不存在，可能需要添加mock
            attr_match = re.search(r"['\"]([^'\"]+)['\"] has no attribute ['\"]([^'\"]+)['\"]", error_message)
            if attr_match:
                obj_name = attr_match.group(1)
                attr_name = attr_match.group(2)
                
                # 在测试中添加mock属性
                mock_code = f"""
    @pytest.fixture
    def {obj_name}_mock(self):
        \"\"\"模拟{obj_name}对象\"\"\"
        from unittest.mock import MagicMock
        mock = MagicMock()
        mock.{attr_name} = MagicMock()
        return mock
"""
                # 在第一个测试类中插入
                class_match = re.search(r'^class\s+Test\w+:', content, re.MULTILINE)
                if class_match:
                    # 找到类的结束位置（下一个类或文件结束）
                    class_start = class_match.end()
                    next_class = re.search(r'^class\s+Test', content[class_start:], re.MULTILINE)
                    if next_class:
                        insert_pos = class_start + next_class.start()
                    else:
                        insert_pos = len(content)
                    
                    content = content[:insert_pos] + mock_code + content[insert_pos:]
            
            if content != original_content:
                test_file.write_text(content, encoding='utf-8')
                self.fixes_applied.append({
                    "file": str(test_file),
                    "error_type": "type_error",
                    "fix": "修复类型错误",
                    "timestamp": datetime.now().isoformat()
                })
                return True
            
        except Exception as e:
            self.fixes_needed.append({
                "file": str(test_file),
                "error_type": "type_error",
                "error": error_message,
                "reason": f"自动修复失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
        
        return False
    
    def fix_error(self, test_file: Path, error_message: str) -> bool:
        """修复错误"""
        error_type = self.analyze_error(error_message, test_file)
        
        if error_type == 'import_error':
            return self.fix_import_error(test_file, error_message)
        elif error_type == 'syntax_error':
            return self.fix_syntax_error(test_file, error_message)
        elif error_type == 'missing_dependency':
            return self.fix_missing_dependency(test_file, error_message)
        elif error_type == 'type_error':
            return self.fix_type_error(test_file, error_message)
        else:
            # 无法自动修复
            self.fixes_needed.append({
                "file": str(test_file),
                "error_type": "other",
                "error": error_message,
                "reason": "无法自动修复，需要人工介入",
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    def save_fixes_needed(self):
        """保存需要人工修复的问题"""
        if not self.fixes_needed:
            return
        
        # 读取现有内容
        existing_content = ""
        if FIXES_NEEDED_FILE.exists():
            existing_content = FIXES_NEEDED_FILE.read_text(encoding='utf-8')
        
        # 生成新内容
        new_content = f"""# 需要人工修复的测试问题

最后更新: {datetime.now().isoformat()}

## 无法自动修复的问题

"""
        
        for fix in self.fixes_needed:
            new_content += f"""### {fix['file']}

- **错误类型**: {fix['error_type']}
- **错误信息**: {fix['error']}
- **原因**: {fix['reason']}
- **时间**: {fix['timestamp']}

"""
        
        # 合并内容
        if existing_content:
            new_content = existing_content + "\n\n---\n\n" + new_content
        
        FIXES_NEEDED_FILE.write_text(new_content, encoding='utf-8')


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="自动修复测试错误")
    parser.add_argument("--test-file", help="测试文件路径")
    parser.add_argument("--error", help="错误消息")
    parser.add_argument("--test-results", help="测试结果文件路径")
    
    args = parser.parse_args()
    
    fixer = TestErrorFixer()
    
    if args.test_file and args.error:
        # 修复单个文件的错误
        test_file = Path(args.test_file)
        if test_file.exists():
            success = fixer.fix_error(test_file, args.error)
            if success:
                print(f"✓ 已修复: {test_file}")
            else:
                print(f"✗ 无法自动修复: {test_file}")
        else:
            print(f"文件不存在: {test_file}")
    elif args.test_results:
        # 从测试结果文件中读取错误并修复
        results_file = Path(args.test_results)
        if results_file.exists():
            # 这里可以解析测试结果文件，提取错误信息
            # 然后对每个失败的测试文件进行修复
            print("从测试结果文件修复...")
            # TODO: 实现从测试结果文件读取错误
        else:
            print(f"测试结果文件不存在: {results_file}")
    else:
        parser.print_help()
    
    # 保存需要人工修复的问题
    fixer.save_fixes_needed()
    
    # 输出修复统计
    print(f"\n修复统计:")
    print(f"  已修复: {len(fixer.fixes_applied)}")
    print(f"  需要人工修复: {len(fixer.fixes_needed)}")


if __name__ == "__main__":
    main()

