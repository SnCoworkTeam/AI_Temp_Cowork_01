#!/usr/bin/env python3
"""
数据模型验证
在Git提交前验证数据模型定义
"""

import sys
import os
import ast
import importlib.util
from pathlib import Path
from typing import List, Tuple

# 项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def get_staged_files():
    """获取暂存的文件列表"""
    import subprocess
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]


def is_model_file(file_path: Path) -> bool:
    """判断是否为模型文件"""
    # 检查文件路径
    if "models" not in str(file_path) and "schemas" not in str(file_path):
        return False
    
    # 检查文件扩展名
    if not file_path.suffix == ".py":
        return False
    
    return True


def validate_pydantic_model(file_path: Path) -> Tuple[bool, List[str]]:
    """验证Pydantic模型"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        
        # 检查是否导入了BaseModel
        has_basemodel = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "pydantic" and any(alias.name == "BaseModel" for alias in node.names):
                    has_basemodel = True
                    break
                if node.module == "pydantic" and any(alias.name == "BaseModel" for alias in node.names):
                    has_basemodel = True
                    break
        
        # 查找所有类定义
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node)
        
        # 检查每个类是否继承自BaseModel
        for class_node in classes:
            # 检查是否有基类
            if not class_node.bases:
                continue
            
            # 检查是否继承自BaseModel
            is_basemodel_subclass = False
            for base in class_node.bases:
                if isinstance(base, ast.Name) and base.id == "BaseModel":
                    is_basemodel_subclass = True
                    break
                elif isinstance(base, ast.Attribute):
                    if base.attr == "BaseModel":
                        is_basemodel_subclass = True
                        break
            
            if is_basemodel_subclass:
                # 检查是否有文档字符串
                if not ast.get_docstring(class_node):
                    issues.append(f"{file_path.name}:{class_node.lineno} - 类 {class_node.name} 缺少文档字符串")
                
                # 检查字段是否有类型注解
                for item in class_node.body:
                    if isinstance(item, ast.AnnAssign):
                        if item.annotation is None:
                            issues.append(f"{file_path.name}:{item.lineno} - 字段缺少类型注解")
    
    except SyntaxError as e:
        issues.append(f"{file_path.name}: 语法错误 - {e}")
    except Exception as e:
        issues.append(f"{file_path.name}: 验证错误 - {e}")
    
    return len(issues) == 0, issues


def validate_sqlalchemy_model(file_path: Path) -> Tuple[bool, List[str]]:
    """验证SQLAlchemy模型"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        
        # 检查是否导入了declarative_base
        has_declarative = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "sqlalchemy.ext.declarative" or node.module == "sqlalchemy.orm":
                    has_declarative = True
                    break
        
        # 查找所有类定义
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node)
        
        # 检查每个类
        for class_node in classes:
            # 检查是否有__tablename__
            has_tablename = False
            for item in class_node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "__tablename__":
                            has_tablename = True
                            break
            
            # 如果看起来像模型但没有__tablename__，发出警告
            if has_declarative and not has_tablename:
                # 检查是否有Column定义
                has_column = False
                for item in class_node.body:
                    if isinstance(item, ast.Assign):
                        # 检查是否有Column类型
                        if isinstance(item.value, ast.Call):
                            if isinstance(item.value.func, ast.Attribute) and item.value.func.attr == "Column":
                                has_column = True
                                break
                
                if has_column:
                    issues.append(f"{file_path.name}:{class_node.lineno} - 类 {class_node.name} 缺少 __tablename__ 属性")
    
    except SyntaxError as e:
        issues.append(f"{file_path.name}: 语法错误 - {e}")
    except Exception as e:
        issues.append(f"{file_path.name}: 验证错误 - {e}")
    
    return len(issues) == 0, issues


def validate_models():
    """验证所有模型文件"""
    print("🔍 验证数据模型...")
    
    staged_files = get_staged_files()
    
    if not staged_files:
        print("ℹ️  没有暂存的文件需要检查")
        return True
    
    # 过滤模型文件
    model_files = []
    for file_path_str in staged_files:
        file_path = project_root / file_path_str
        if file_path.exists() and is_model_file(file_path):
            model_files.append(file_path)
    
    if not model_files:
        print("ℹ️  没有模型文件需要检查")
        return True
    
    print(f"  检查 {len(model_files)} 个模型文件...")
    
    all_issues = []
    
    for model_file in model_files:
        # 判断模型类型并验证
        content = model_file.read_text(encoding='utf-8')
        
        if "from pydantic" in content or "import pydantic" in content:
            valid, issues = validate_pydantic_model(model_file)
            all_issues.extend(issues)
        elif "from sqlalchemy" in content or "import sqlalchemy" in content:
            valid, issues = validate_sqlalchemy_model(model_file)
            all_issues.extend(issues)
    
    if all_issues:
        print("❌ 模型验证失败:")
        for issue in all_issues[:10]:  # 只显示前10个问题
            print(f"   - {issue}")
        if len(all_issues) > 10:
            print(f"   ... 还有 {len(all_issues) - 10} 个问题")
        return False
    
    print("✅ 模型验证通过")
    return True


def main():
    """主函数"""
    try:
        success = validate_models()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: 模型验证时发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()









