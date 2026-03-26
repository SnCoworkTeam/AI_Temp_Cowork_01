#!/usr/bin/env python3
"""
批量修复所有测试文件中的NameError问题
使用正则表达式从测试函数名和import语句中提取函数/类名
"""
import re
import sys
from pathlib import Path
from typing import List, Tuple

def fix_file(file_path: Path) -> Tuple[int, List[str]]:
    """修复单个文件"""
    if not file_path.exists():
        return 0, []
    
    content = file_path.read_text(encoding='utf-8')
    original = content
    fixes = []
    
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        # 修复func_name
        if '{func_name}' in line:
            # 向前查找测试函数名和import
            test_name = None
            import_name = None
            
            # 向前查找（最多30行）
            for j in range(max(0, i - 30), i):
                # 查找测试函数
                if 'def test_' in lines[j]:
                    m = re.search(r'def\s+(test_\w+)', lines[j])
                    if m:
                        test_name = m.group(1)
                # 查找import语句
                if 'from' in lines[j] and 'import' in lines[j]:
                    m = re.search(r'from\s+[\w.]+\s+import\s+(\w+)', lines[j])
                    if m:
                        import_name = m.group(1)
            
            # 确定函数名
            func_name = None
            if import_name:
                func_name = import_name
            elif test_name:
                # test_get_by_id -> get_by_id
                if test_name.startswith('test_'):
                    func_name = test_name[5:]
                    if func_name == '__init__':
                        func_name = '__init__'
            
            if func_name:
                new_line = line.replace('{func_name}', func_name)
                fixes.append(f"第{i+1}行: func_name -> {func_name}")
                new_lines.append(new_line)
                continue
        
        # 修复class_name
        if '{class_name}' in line:
            # 向前查找
            test_name = None
            import_name = None
            
            for j in range(max(0, i - 30), i):
                if 'def test_' in lines[j]:
                    m = re.search(r'def\s+(test_\w+)', lines[j])
                    if m:
                        test_name = m.group(1)
                if 'from' in lines[j] and 'import' in lines[j]:
                    m = re.search(r'from\s+[\w.]+\s+import\s+(\w+)', lines[j])
                    if m:
                        import_name = m.group(1)
            
            # 确定类名
            class_name = None
            if import_name:
                class_name = import_name
            elif test_name and test_name.endswith('_initialization'):
                # test_documentmetadata_initialization -> DocumentMetadata
                base = test_name[5:-15]  # 移除test_和_initialization
                parts = base.split('_')
                class_name = ''.join(p.capitalize() for p in parts)
            
            if class_name:
                new_line = line.replace('{class_name}', class_name)
                fixes.append(f"第{i+1}行: class_name -> {class_name}")
                new_lines.append(new_line)
                continue
        
        new_lines.append(line)
    
    # 修复转义序列
    content = '\n'.join(new_lines)
    content = content.replace('src\\', 'src/')
    
    if content != original:
        file_path.write_text(content, encoding='utf-8')
        return len(fixes), fixes
    
    return 0, []

def main():
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
    
    total = 0
    fixed = []
    
    for f in all_files:
        count, fixes = fix_file(f)
        if count > 0:
            total += count
            fixed.append((f.name, count))
            print(f"[OK] {f.name}: {count} 处")
    
    print(f"\n修复完成: {len(fixed)} 个文件, {total} 处问题")

if __name__ == "__main__":
    main()
