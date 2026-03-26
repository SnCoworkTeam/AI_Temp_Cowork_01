#!/usr/bin/env python3
"""
批量修复所有测试文件中的NameError问题
自动从测试函数名和import语句中提取函数/类名
"""
import re
import sys
from pathlib import Path
from typing import List, Tuple

def extract_function_name(test_content: str, test_name: str, import_line: str = "") -> str:
    """从测试内容中提取函数名"""
    # 优先从import语句提取
    if import_line:
        import_match = re.search(r'from\s+[\w.]+\s+import\s+(\w+)', import_line)
        if import_match:
            return import_match.group(1)
    
    # 从测试函数名提取
    if test_name.startswith('test_'):
        func_name = test_name[5:]  # 移除test_前缀
        
        # 移除特殊后缀
        if func_name.endswith('_initialization'):
            return None  # 这是类初始化，不是函数
        elif func_name == '__init__':
            return '__init__'
        else:
            return func_name
    
    return None

def extract_class_name(test_content: str, test_name: str, import_line: str = "") -> str:
    """从测试内容中提取类名"""
    # 优先从import语句提取
    if import_line:
        import_match = re.search(r'from\s+[\w.]+\s+import\s+(\w+)', import_line)
        if import_match:
            return import_match.group(1)
    
    # 从测试函数名提取
    if test_name.endswith('_initialization'):
        class_name = test_name[5:-15]  # 移除test_和_initialization
        # 转换为类名（驼峰命名）
        parts = class_name.split('_')
        return ''.join(word.capitalize() for word in parts)
    
    return None

def fix_test_file(file_path: Path) -> Tuple[int, List[str]]:
    """修复单个测试文件中的NameError"""
    if not file_path.exists():
        return 0, []
    
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    fixes = []
    
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # 检查是否有func_name或class_name
        if '{func_name}' in line or '{class_name}' in line:
            # 向前查找测试函数定义和import语句
            test_func_name = None
            import_line = None
            
            # 向前查找（最多50行）
            for j in range(max(0, i - 50), i):
                if 'def test_' in lines[j]:
                    match = re.search(r'def\s+(test_\w+)', lines[j])
                    if match:
                        test_func_name = match.group(1)
                if 'from' in lines[j] and 'import' in lines[j]:
                    import_line = lines[j]
            
            # 修复func_name
            if '{func_name}' in line:
                func_name = extract_function_name(content, test_func_name or "", import_line or "")
                if func_name:
                    new_line = line.replace('{func_name}', func_name)
                    fixes.append(f"第{i+1}行: func_name -> {func_name}")
                    new_lines.append(new_line)
                    i += 1
                    continue
            
            # 修复class_name
            if '{class_name}' in line:
                class_name = extract_class_name(content, test_func_name or "", import_line or "")
                if class_name:
                    new_line = line.replace('{class_name}', class_name)
                    fixes.append(f"第{i+1}行: class_name -> {class_name}")
                    new_lines.append(new_line)
                    i += 1
                    continue
        
        new_lines.append(line)
        i += 1
    
    # 修复转义序列
    content = '\n'.join(new_lines)
    content = content.replace('src\\', 'src/')
    content = content.replace('src\\core\\', 'src/core/')
    content = content.replace('src\\models\\', 'src/models/')
    content = content.replace('src\\repositories\\', 'src/repositories/')
    content = content.replace('src\\api\\', 'src/api/')
    content = content.replace('src\\services\\', 'src/services/')
    content = content.replace('src\\collectors\\', 'src/collectors/')
    
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        return len(fixes), fixes
    
    return 0, []

def main():
    """主函数"""
    project_root = Path(__file__).parent.parent
    
    test_dirs = [
        project_root / "knowledge-base" / "tests" / "unit",
        project_root / "metadata-service" / "tests" / "unit",
        project_root / "database" / "tests" / "unit",
    ]
    
    all_files = []
    for test_dir in test_dirs:
        if test_dir.exists():
            all_files.extend(test_dir.glob("test_*.py"))
    
    print(f"找到 {len(all_files)} 个测试文件")
    print("开始批量修复...\n")
    
    total_fixes = 0
    fixed_files = []
    
    for file_path in all_files:
        count, fixes = fix_test_file(file_path)
        if count > 0:
            total_fixes += count
            fixed_files.append((file_path, count, fixes))
            print(f"✅ {file_path.name}: 修复了 {count} 处问题")
            if len(fixes) <= 5:
                for fix in fixes:
                    print(f"   - {fix}")
            else:
                for fix in fixes[:3]:
                    print(f"   - {fix}")
                print(f"   ... 还有 {len(fixes) - 3} 处修复")
    
    print(f"\n==========================================")
    print(f"修复完成！")
    print(f"==========================================")
    print(f"修复了 {len(fixed_files)} 个文件，共 {total_fixes} 处问题")

if __name__ == "__main__":
    main()




