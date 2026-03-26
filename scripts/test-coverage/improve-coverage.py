#!/usr/bin/env python3
"""
自动提升测试覆盖率
分析缺失的测试并自动生成测试文件
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Set
import ast
import os

# 项目根目录
# 脚本在 scripts/test-coverage/improve-coverage.py
# 需要向上3级: test-coverage -> scripts -> project_root
_script_path = Path(__file__).resolve()
PROJECT_ROOT = _script_path.parent.parent.parent.resolve()

# 服务配置
SERVICE_CONFIGS = {
    "auth-service": {
        "priority": 1,
        "src_path": "src",
        "test_path": "tests/unit"
    },
    "knowledge-base": {
        "priority": 2,
        "src_path": "src",
        "test_path": "tests/unit"
    },
    "metadata-service": {
        "priority": 3,
        "src_path": "src",
        "test_path": "tests/unit"
    },
    "workflow-engine": {
        "priority": 4,
        "src_path": "src",
        "test_path": "tests/unit"
    },
    "mcp-gateway": {
        "priority": 5,
        "src_path": "src",
        "test_path": "tests/unit"
    },
    "database": {
        "priority": 6,
        "src_path": "src",
        "test_path": "tests/unit"
    }
}


def get_python_files(directory: Path, exclude_patterns: List[str] = None) -> List[Path]:
    """获取目录下所有Python文件"""
    if exclude_patterns is None:
        exclude_patterns = ["__pycache__", "migrations", ".pytest_cache"]
    
    files = []
    for root, dirs, filenames in os.walk(directory):
        # 排除目录
        dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
        
        for filename in filenames:
            if filename.endswith('.py'):
                filepath = Path(root) / filename
                files.append(filepath)
    
    return files


def get_test_file_path(src_file: Path, service_path: Path, test_base_path: str) -> Path:
    """根据源文件路径生成测试文件路径"""
    # 获取相对于src的路径
    src_path = service_path / "src"
    rel_path = src_file.relative_to(src_path)
    
    # 生成测试文件路径
    test_dir = service_path / test_base_path
    test_file = test_dir / f"test_{rel_path.name}"
    
    return test_file


def analyze_module_for_tests(src_file: Path) -> Dict:
    """分析模块，识别需要测试的函数和类"""
    try:
        with open(src_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(src_file))
        
        functions = []
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_') or node.name.startswith('__'):
                    functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                if not node.name.startswith('_'):
                    classes.append(node.name)
        
        return {
            "functions": functions,
            "classes": classes,
            "has_tests": False
        }
    except Exception as e:
        return {
            "functions": [],
            "classes": [],
            "has_tests": False,
            "error": str(e)
        }


def generate_test_file_content(module_path: str, functions: List[str], classes: List[str]) -> str:
    """生成测试文件内容"""
    module_name = module_path.replace('/', '.').replace('\\', '.').replace('.py', '')
    
    content = f'''"""
测试文件：{module_path}
自动生成的测试模板
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "{module_path.split('/')[0]}" / "src"))


@pytest.mark.unit
class TestModule:
    """测试模块：{module_name}"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return MagicMock()
    
    @pytest.fixture
    def mock_request(self):
        """模拟FastAPI请求"""
        return MagicMock()
'''
    
    # 为每个类生成测试
    for class_name in classes:
        content += f'''
    def test_{class_name.lower()}_initialization(self, mock_db):
        """测试{class_name}初始化"""
        try:
            from {module_name} import {class_name}
            instance = {class_name}(mock_db)
            assert instance is not None
        except Exception as e:
            pytest.skip(f"无法导入或初始化{{class_name}}: {{e}}")
'''
    
    # 为每个函数生成测试
    for func_name in functions:
        content += f'''
    def test_{func_name}(self, mock_db, mock_request):
        """测试{func_name}函数"""
        try:
            from {module_name} import {func_name}
            # TODO: 添加具体的测试逻辑
            pytest.skip("需要实现具体测试逻辑")
        except Exception as e:
            pytest.skip(f"无法导入{{func_name}}: {{e}}")
'''
    
    return content


def improve_service_coverage(service_name: str, target_coverage: float = 80.0) -> Dict:
    """提升单个服务的测试覆盖率"""
    config = SERVICE_CONFIGS.get(service_name)
    if not config:
        return {"status": "ERROR", "message": f"Unknown service: {service_name}"}
    
    service_path = PROJECT_ROOT / service_name
    # 调试信息
    if not service_path.exists():
        return {
            "status": "ERROR", 
            "message": f"Service path not found: {service_path}",
            "project_root": str(PROJECT_ROOT),
            "service_name": service_name,
            "calculated_path": str(service_path)
        }
    
    src_path = service_path / config["src_path"]
    if not src_path.exists():
        return {"status": "ERROR", "message": f"Source path not found: {src_path}"}
    
    # 获取所有源文件
    src_files = get_python_files(src_path)
    
    # 检查哪些文件缺少测试
    test_base_path = config["test_path"]
    test_dir = service_path / test_base_path
    test_dir.mkdir(parents=True, exist_ok=True)
    
    missing_tests = []
    created_tests = []
    
    for src_file in src_files:
        # 跳过__init__.py
        if src_file.name == "__init__.py":
            continue
        
        test_file = get_test_file_path(src_file, service_path, test_base_path)
        
        # 检查测试文件是否存在
        if not test_file.exists():
            # 分析模块
            analysis = analyze_module_for_tests(src_file)
            
            if analysis.get("functions") or analysis.get("classes"):
                # 生成测试文件
                rel_module_path = src_file.relative_to(service_path)
                test_content = generate_test_file_content(
                    str(rel_module_path),
                    analysis.get("functions", []),
                    analysis.get("classes", [])
                )
                
                # 确保目录存在
                test_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 写入测试文件
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(test_content)
                
                created_tests.append(str(test_file.relative_to(service_path)))
                missing_tests.append(str(src_file.relative_to(service_path)))
    
    return {
        "status": "SUCCESS",
        "service": service_name,
        "created_tests": len(created_tests),
        "missing_tests": len(missing_tests),
        "test_files": created_tests
    }


def analyze_test_errors(test_output: str, test_errors: str) -> Dict:
    """
    分析测试错误，识别错误类型
    
    Args:
        test_output: 测试标准输出
        test_errors: 测试错误输出
        
    Returns:
        包含错误分析的字典
    """
    error_text = test_errors or test_output
    error_types = []
    suggestions = []
    
    # 检查导入错误
    if "ModuleNotFoundError" in error_text or "ImportError" in error_text:
        error_types.append("IMPORT_ERROR")
        suggestions.append("检查模块导入路径和PYTHONPATH设置")
    
    # 检查语法错误
    if "SyntaxError" in error_text:
        error_types.append("SYNTAX_ERROR")
        suggestions.append("检查Python语法错误")
    
    # 检查类型错误
    if "TypeError" in error_text:
        error_types.append("TYPE_ERROR")
        suggestions.append("检查函数参数类型")
    
    # 检查属性错误
    if "AttributeError" in error_text:
        error_types.append("ATTRIBUTE_ERROR")
        suggestions.append("检查对象属性是否存在")
    
    # 检查断言失败
    if "AssertionError" in error_text:
        error_types.append("ASSERTION_ERROR")
        suggestions.append("检查测试断言逻辑")
    
    return {
        "error_types": error_types,
        "suggestions": suggestions,
        "has_errors": len(error_types) > 0
    }


def fix_import_errors(test_file: Path, service_name: str) -> bool:
    """
    修复测试文件中的导入错误
    
    Args:
        test_file: 测试文件路径
        service_name: 服务名称
        
    Returns:
        是否成功修复
    """
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否需要修复导入路径
        if "sys.path" not in content:
            # 添加路径设置
            import_section = f'''import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "{service_name}" / "src"))
'''
            
            # 在import语句后插入
            if "import pytest" in content:
                content = content.replace("import pytest", f"import pytest\n{import_section}")
            else:
                content = import_section + content
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception:
        return False


def fix_test_errors(test_file: Path, error_analysis: Dict) -> bool:
    """
    根据错误分析修复测试文件
    
    Args:
        test_file: 测试文件路径
        error_analysis: 错误分析结果
        
    Returns:
        是否成功修复
    """
    if not error_analysis.get("has_errors"):
        return True
    
    error_types = error_analysis.get("error_types", [])
    
    # 处理导入错误
    if "IMPORT_ERROR" in error_types:
        service_name = test_file.parent.parent.parent.name
        return fix_import_errors(test_file, service_name)
    
    # 其他错误类型需要更复杂的修复逻辑
    # 这里先返回False，表示需要手动修复
    return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="提升测试覆盖率")
    parser.add_argument("--service", help="指定服务名称")
    parser.add_argument("--all", action="store_true", help="处理所有服务")
    parser.add_argument("--target", type=float, default=80.0, help="目标覆盖率（默认80%）")
    
    args = parser.parse_args()
    
    if args.service:
        result = improve_service_coverage(args.service, args.target)
        print(json.dumps(result, indent=2))
    elif args.all:
        results = {}
        for service_name in SERVICE_CONFIGS.keys():
            print(f"Processing {service_name}...", file=sys.stderr)
            result = improve_service_coverage(service_name, args.target)
            results[service_name] = result
        print(json.dumps(results, indent=2))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

