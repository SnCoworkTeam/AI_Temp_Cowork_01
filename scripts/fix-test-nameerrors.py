#!/usr/bin/env python3
"""
批量修复测试文件中的NameError问题
将func_name和class_name替换为硬编码的字符串常量
"""
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

def extract_function_name_from_test(test_content: str, test_name: str) -> str:
    """从测试内容中提取函数名"""
    # 尝试从import语句中提取
    import_match = re.search(r'from\s+[\w.]+import\s+(\w+)', test_content)
    if import_match:
        return import_match.group(1)
    
    # 尝试从测试名称中提取
    # test_get_by_id -> get_by_id
    if test_name.startswith('test_'):
        func_name = test_name[5:]  # 移除test_前缀
        # 移除_initialization后缀
        if func_name.endswith('_initialization'):
            class_name = func_name[:-15]  # 移除_initialization
            # 转换为类名（首字母大写）
            return ''.join(word.capitalize() for word in class_name.split('_'))
        return func_name
    
    return "unknown"

def extract_class_name_from_test(test_content: str, test_name: str) -> str:
    """从测试内容中提取类名"""
    # 尝试从import语句中提取
    import_match = re.search(r'from\s+[\w.]+import\s+(\w+)', test_content)
    if import_match:
        class_name = import_match.group(1)
        # 如果是初始化测试，类名通常在import中
        return class_name
    
    # 尝试从测试名称中提取
    # test_documentmetadata_initialization -> DocumentMetadata
    if test_name.endswith('_initialization'):
        class_name = test_name[5:-15]  # 移除test_和_initialization
        # 转换为类名（首字母大写，驼峰命名）
        parts = class_name.split('_')
        return ''.join(word.capitalize() for word in parts)
    
    return "Unknown"

def fix_test_file(file_path: Path) -> Tuple[int, List[str]]:
    """修复单个测试文件中的NameError"""
    if not file_path.exists():
        return 0, []
    
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    fixes = []
    
    # 修复func_name
    func_name_pattern = r"pytest\.skip\(f\"无法导入\{func_name\}: \{e\}\"\)"
    func_name_matches = list(re.finditer(func_name_pattern, content))
    
    for match in func_name_matches:
        # 获取上下文，找到测试函数名
        start = max(0, match.start() - 500)
        end = min(len(content), match.end() + 100)
        context = content[start:end]
        
        # 查找测试函数定义
        test_func_match = re.search(r'def\s+(test_\w+)', context)
        if test_func_match:
            test_name = test_func_match.group(1)
            func_name = extract_function_name_from_test(context, test_name)
            
            # 替换
            old_str = match.group(0)
            new_str = f'pytest.skip(f"无法导入{func_name}: {{e}}")'
            content = content.replace(old_str, new_str, 1)
            fixes.append(f"修复func_name: {test_name} -> {func_name}")
    
    # 修复class_name
    class_name_pattern = r"pytest\.skip\(f\"无法导入或初始化\{class_name\}: \{e\}\"\)"
    class_name_matches = list(re.finditer(class_name_pattern, content))
    
    for match in class_name_matches:
        # 获取上下文
        start = max(0, match.start() - 500)
        end = min(len(content), match.end() + 100)
        context = content[start:end]
        
        # 查找测试函数定义
        test_func_match = re.search(r'def\s+(test_\w+)', context)
        if test_func_match:
            test_name = test_func_match.group(1)
            class_name = extract_class_name_from_test(context, test_name)
            
            # 替换
            old_str = match.group(0)
            new_str = f'pytest.skip(f"无法导入或初始化{class_name}: {{e}}")'
            content = content.replace(old_str, new_str, 1)
            fixes.append(f"修复class_name: {test_name} -> {class_name}")
    
    # 修复转义序列警告
    content = content.replace('src\\', 'src/')
    content = content.replace('src\\core\\', 'src/core/')
    content = content.replace('src\\models\\', 'src/models/')
    content = content.replace('src\\repositories\\', 'src/repositories/')
    
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        return len(fixes), fixes
    
    return 0, []

def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 指定文件
        files = [Path(f) for f in sys.argv[1:]]
    else:
        # 查找所有测试文件
        project_root = Path(__file__).parent.parent
        test_dirs = [
            project_root / "knowledge-base" / "tests" / "unit",
            project_root / "metadata-service" / "tests" / "unit",
            project_root / "database" / "tests" / "unit",
        ]
        
        files = []
        for test_dir in test_dirs:
            if test_dir.exists():
                files.extend(test_dir.glob("test_*.py"))
    
    total_fixes = 0
    fixed_files = []
    
    for file_path in files:
        count, fixes = fix_test_file(file_path)
        if count > 0:
            total_fixes += count
            fixed_files.append((file_path, count, fixes))
            print(f"✅ {file_path}: 修复了 {count} 处问题")
            for fix in fixes:
                print(f"   - {fix}")
    
    print(f"\n总计修复了 {len(fixed_files)} 个文件，{total_fixes} 处问题")

if __name__ == "__main__":
    main()




