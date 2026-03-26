"""
架构守护脚本
用于确保代码质量和不偏离设计理念
"""
import json
import ast
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import subprocess


class ViolationLevel(Enum):
    """违规级别"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Violation:
    """违规记录"""
    level: ViolationLevel
    rule: str
    message: str
    file_path: str
    line_number: Optional[int] = None
    fix_suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """验证结果"""
    success: bool
    violations: List[Violation] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class ArchitectureGuard:
    """架构守护类"""
    
    def __init__(self, project_root: Optional[str] = None):
        """
        初始化架构守护
        
        Args:
            project_root: 项目根目录路径，默认为当前目录
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.constitution_path = self.project_root / ".project_constitution.md"
        self.required_services = [
            "mcp-gateway",
            "workflow-engine",
            "web-ui",
            "shared-libs"
        ]
        self.required_service_structure = {
            "mcp-gateway": {
                "src": ["main.py", "config.py", "routes", "tools", "models"],
                "tests": ["test_health.py"],
                "requirements.txt": True,
                "Dockerfile": True
            },
            "workflow-engine": {
                "src": ["main.py", "config.py", "routes", "workflows", "nodes", "agents"],
                "tests": ["test_health.py"],
                "requirements.txt": True,
                "Dockerfile": True
            },
            "web-ui": {
                "src": ["app", "components", "lib"],
                "package.json": True,
                "Dockerfile": True
            },
            "shared-libs": {
                "common": ["logger.py", "error_handler.py", "api_client.py"],
                "schemas": ["common.py"]
            }
        }
        self.allowed_imports = {
            "mcp-gateway": {
                "fastapi": True,
                "pydantic": True,
                "shared_libs": True,
                "redis": True,
                "httpx": True,
            },
            "workflow-engine": {
                "fastapi": True,
                "pydantic": True,
                "langchain": True,
                "langgraph": True,
                "shared_libs": True,
                "redis": True,
                "httpx": True,
            },
            "web-ui": {
                "next": True,
                "react": True,
            }
        }
    
    def validate_project_structure(self) -> Dict[str, Any]:
        """
        验证项目结构是否符合宪法规范
        
        Returns:
            验证结果字典
        """
        violations = []
        details = {
            "services": {},
            "missing_files": [],
            "missing_directories": []
        }
        
        # 检查必需的服务目录
        for service in self.required_services:
            service_path = self.project_root / service
            service_details = {
                "exists": service_path.exists(),
                "structure": {}
            }
            
            if not service_path.exists():
                violations.append(Violation(
                    level=ViolationLevel.ERROR,
                    rule="required_service_missing",
                    message=f"必需的服务目录缺失: {service}",
                    file_path=str(service_path),
                    fix_suggestion=f"创建目录: mkdir -p {service}"
                ))
                details["missing_directories"].append(service)
                details["services"][service] = service_details
                continue
            
            # 检查服务结构
            if service in self.required_service_structure:
                structure = self.required_service_structure[service]
                for item, requirement in structure.items():
                    item_path = service_path / item
                    
                    if isinstance(requirement, bool):
                        # 必需文件
                        if requirement and not item_path.exists():
                            violations.append(Violation(
                                level=ViolationLevel.ERROR,
                                rule="required_file_missing",
                                message=f"必需的文件缺失: {service}/{item}",
                                file_path=str(item_path),
                                fix_suggestion=f"创建文件: {service}/{item}"
                            ))
                            details["missing_files"].append(f"{service}/{item}")
                    elif isinstance(requirement, list):
                        # 必需目录或文件列表
                        if not item_path.exists():
                            violations.append(Violation(
                                level=ViolationLevel.ERROR,
                                rule="required_directory_missing",
                                message=f"必需的目录/文件缺失: {service}/{item}",
                                file_path=str(item_path),
                                fix_suggestion=f"创建目录: mkdir -p {service}/{item}"
                            ))
                            details["missing_directories"].append(f"{service}/{item}")
                        else:
                            # 检查子项
                            for sub_item in requirement:
                                sub_item_path = item_path / sub_item
                                if not sub_item_path.exists():
                                    violations.append(Violation(
                                        level=ViolationLevel.WARNING,
                                        rule="recommended_item_missing",
                                        message=f"推荐的文件/目录缺失: {service}/{item}/{sub_item}",
                                        file_path=str(sub_item_path)
                                    ))
                    
                    service_details["structure"][item] = item_path.exists()
            
            details["services"][service] = service_details
        
        # 检查docker-compose.yml
        docker_compose = self.project_root / "docker-compose.yml"
        if not docker_compose.exists():
            violations.append(Violation(
                level=ViolationLevel.ERROR,
                rule="docker_compose_missing",
                message="docker-compose.yml 文件缺失",
                file_path=str(docker_compose),
                fix_suggestion="创建 docker-compose.yml 文件"
            ))
        
        # 检查项目宪法文件
        if not self.constitution_path.exists():
            violations.append(Violation(
                level=ViolationLevel.WARNING,
                rule="constitution_missing",
                message="项目宪法文件缺失",
                file_path=str(self.constitution_path)
            ))
        
        return {
            "success": len([v for v in violations if v.level == ViolationLevel.ERROR]) == 0,
            "violations": violations,
            "details": details
        }
    
    def validate_imports(self, file_path: str) -> List[Violation]:
        """
        检查代码导入和依赖关系
        
        Args:
            file_path: 文件路径
            
        Returns:
            违规列表
        """
        violations = []
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            return violations
        
        # 确定服务类型
        service_type = None
        for service in self.required_services:
            if service in str(file_path_obj):
                service_type = service
                break
        
        if not service_type:
            return violations
        
        # 只检查Python文件
        if file_path_obj.suffix != ".py":
            return violations
        
        try:
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path_obj))
            
            # 检查导入
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split('.')[0]
                        violation = self._check_import_allowed(
                            module_name, service_type, file_path, node.lineno
                        )
                        if violation:
                            violations.append(violation)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split('.')[0]
                        violation = self._check_import_allowed(
                            module_name, service_type, file_path, node.lineno
                        )
                        if violation:
                            violations.append(violation)
        
        except SyntaxError as e:
            violations.append(Violation(
                level=ViolationLevel.ERROR,
                rule="syntax_error",
                message=f"语法错误: {str(e)}",
                file_path=file_path,
                line_number=e.lineno
            ))
        except Exception as e:
            violations.append(Violation(
                level=ViolationLevel.WARNING,
                rule="parse_error",
                message=f"解析错误: {str(e)}",
                file_path=file_path
            ))
        
        return violations
    
    def _check_import_allowed(
        self,
        module_name: str,
        service_type: str,
        file_path: str,
        line_number: int
    ) -> Optional[Violation]:
        """检查导入是否允许"""
        # 标准库导入总是允许的
        import sys
        if module_name in sys.stdlib_module_names:
            return None
        
        # 检查是否在允许列表中
        if service_type in self.allowed_imports:
            allowed = self.allowed_imports[service_type]
            if module_name in allowed or any(
                module_name.startswith(allowed_mod)
                for allowed_mod in allowed.keys()
            ):
                return None
        
        # 检查是否是共享库导入（使用相对或绝对路径）
        if "shared_libs" in module_name or "shared-libs" in file_path:
            return None
        
        # 检查是否是相对导入
        if module_name.startswith('.'):
            return None
        
        return Violation(
            level=ViolationLevel.WARNING,
            rule="unallowed_import",
            message=f"未在允许列表中的导入: {module_name}",
            file_path=file_path,
            line_number=line_number,
            fix_suggestion=f"检查 {service_type} 的依赖配置"
        )
    
    def validate_api_spec(self, openapi_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证API接口规范
        
        Args:
            openapi_spec: OpenAPI规范字典
            
        Returns:
            验证结果
        """
        violations = []
        details = {
            "paths": {},
            "missing_health_endpoint": [],
            "missing_docs": [],
            "missing_validation": []
        }
        
        if not openapi_spec:
            violations.append(Violation(
                level=ViolationLevel.ERROR,
                rule="openapi_spec_missing",
                message="OpenAPI规范缺失",
                file_path="API"
            ))
            return {
                "success": False,
                "violations": violations,
                "details": details
            }
        
        # 检查必需的健康检查端点
        paths = openapi_spec.get("paths", {})
        health_endpoints = [
            "/api/health",
            "/api/health/ready",
            "/api/health/live"
        ]
        
        for endpoint in health_endpoints:
            if endpoint not in paths:
                violations.append(Violation(
                    level=ViolationLevel.WARNING,
                    rule="health_endpoint_missing",
                    message=f"推荐的健康检查端点缺失: {endpoint}",
                    file_path="API"
                ))
                details["missing_health_endpoint"].append(endpoint)
        
        # 检查所有路径是否有文档
        for path, methods in paths.items():
            path_details = {}
            for method, spec in methods.items():
                if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                    continue
                
                # 检查是否有描述
                if "description" not in spec or not spec.get("description"):
                    violations.append(Violation(
                        level=ViolationLevel.WARNING,
                        rule="api_doc_missing",
                        message=f"API端点缺少描述: {method.upper()} {path}",
                        file_path=f"API:{path}"
                    ))
                    details["missing_docs"].append(f"{method.upper()} {path}")
                
                # 检查响应模型
                responses = spec.get("responses", {})
                if "200" not in responses:
                    violations.append(Violation(
                        level=ViolationLevel.WARNING,
                        rule="success_response_missing",
                        message=f"缺少成功响应定义: {method.upper()} {path}",
                        file_path=f"API:{path}"
                    ))
                
                path_details[method] = {
                    "has_description": "description" in spec,
                    "has_responses": "responses" in spec
                }
            
            details["paths"][path] = path_details
        
        # 检查是否有Pydantic模型验证
        components = openapi_spec.get("components", {})
        schemas = components.get("schemas", {})
        if not schemas:
            violations.append(Violation(
                level=ViolationLevel.WARNING,
                rule="validation_schemas_missing",
                message="缺少数据验证模式（应使用Pydantic）",
                file_path="API"
            ))
            details["missing_validation"].append("schemas")
        
        return {
            "success": len([v for v in violations if v.level == ViolationLevel.ERROR]) == 0,
            "violations": violations,
            "details": details
        }
    
    def check_test_coverage(self, service: str) -> Dict[str, Any]:
        """
        检查测试覆盖率
        
        Args:
            service: 服务名称
            
        Returns:
            覆盖率信息
        """
        service_path = self.project_root / service
        tests_path = service_path / "tests"
        
        if not tests_path.exists():
            return {
                "coverage": 0,
                "has_tests": False,
                "violation": Violation(
                    level=ViolationLevel.WARNING,
                    rule="tests_missing",
                    message=f"服务 {service} 缺少测试目录",
                    file_path=str(tests_path)
                )
            }
        
        # 统计测试文件
        test_files = list(tests_path.glob("test_*.py"))
        
        # 尝试运行pytest coverage（如果可用）
        coverage_result = None
        try:
            result = subprocess.run(
                ["pytest", "--co", "-q"],
                cwd=service_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            # 解析覆盖率（简化版）
            # 实际实现需要解析coverage报告
        except Exception:
            pass
        
        return {
            "coverage": coverage_result if coverage_result else None,
            "has_tests": len(test_files) > 0,
            "test_files": [str(f.name) for f in test_files],
            "target_coverage": 80
        }
    
    def generate_health_report(self) -> Dict[str, Any]:
        """
        生成架构健康报告
        
        Returns:
            健康报告字典
        """
        report = {
            "timestamp": self._get_timestamp(),
            "project_structure": self.validate_project_structure(),
            "services": {},
            "api_validation": {},
            "test_coverage": {},
            "overall_health": "unknown"
        }
        
        # 检查每个服务的导入
        for service in self.required_services:
            service_path = self.project_root / service
            if not service_path.exists():
                continue
            
            # 检查Python文件的导入
            import_violations = []
            for py_file in service_path.rglob("*.py"):
                violations = self.validate_imports(str(py_file))
                import_violations.extend(violations)
            
            # 检查测试覆盖率
            test_info = self.check_test_coverage(service)
            
            report["services"][service] = {
                "import_violations": len([v for v in import_violations if v.level == ViolationLevel.ERROR]),
                "import_warnings": len([v for v in import_violations if v.level == ViolationLevel.WARNING]),
                "test_coverage": test_info
            }
        
        # 计算总体健康度
        total_errors = sum(
            report["services"].get(s, {}).get("import_violations", 0)
            for s in self.required_services
        )
        total_errors += len([
            v for v in report["project_structure"]["violations"]
            if v.level == ViolationLevel.ERROR
        ])
        
        if total_errors == 0:
            report["overall_health"] = "healthy"
        elif total_errors < 5:
            report["overall_health"] = "warning"
        else:
            report["overall_health"] = "unhealthy"
        
        return report
    
    def auto_fix_violations(self, violations: List[Violation]) -> bool:
        """
        自动修复违规（仅限简单情况）
        
        Args:
            violations: 违规列表
            
        Returns:
            是否成功修复
        """
        fixed_count = 0
        
        for violation in violations:
            if violation.level == ViolationLevel.ERROR:
                # 尝试自动修复缺失的文件/目录
                if violation.rule in ["required_file_missing", "required_directory_missing"]:
                    file_path = Path(violation.file_path)
                    
                    if violation.rule == "required_file_missing":
                        # 创建空文件
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_path.touch()
                        fixed_count += 1
                    elif violation.rule == "required_directory_missing":
                        # 创建目录
                        file_path.mkdir(parents=True, exist_ok=True)
                        # 创建__init__.py如果是Python包
                        if "python" in violation.message.lower() or file_path.parent.name in ["src", "lib"]:
                            init_file = file_path / "__init__.py"
                            if not init_file.exists():
                                init_file.touch()
                        fixed_count += 1
        
        return fixed_count > 0
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def export_report(self, report: Dict[str, Any], output_path: str):
        """
        导出报告到文件
        
        Args:
            report: 健康报告
            output_path: 输出文件路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 转换Violation对象为字典
        def convert_violations(obj):
            if isinstance(obj, Violation):
                return {
                    "level": obj.level.value,
                    "rule": obj.rule,
                    "message": obj.message,
                    "file_path": obj.file_path,
                    "line_number": obj.line_number,
                    "fix_suggestion": obj.fix_suggestion
                }
            elif isinstance(obj, dict):
                return {k: convert_violations(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_violations(item) for item in obj]
            return obj
        
        report_copy = convert_violations(report)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_copy, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"报告已导出到: {output_path}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="架构守护工具")
    parser.add_argument(
        "--check",
        action="store_true",
        help="检查项目结构"
    )
    parser.add_argument(
        "--validate-imports",
        type=str,
        help="验证指定文件的导入"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="生成健康报告"
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="自动修复可修复的违规"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="architecture_report.json",
        help="报告输出路径"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="项目根目录"
    )
    
    args = parser.parse_args()
    
    guard = ArchitectureGuard(project_root=args.project_root)
    
    if args.check:
        result = guard.validate_project_structure()
        print(f"项目结构验证: {'通过' if result['success'] else '失败'}")
        for violation in result["violations"]:
            print(f"  [{violation.level.value.upper()}] {violation.message}")
            if violation.file_path:
                print(f"    文件: {violation.file_path}")
    
    if args.validate_imports:
        violations = guard.validate_imports(args.validate_imports)
        print(f"导入验证 ({args.validate_imports}):")
        for violation in violations:
            print(f"  [{violation.level.value.upper()}] {violation.message}")
            if violation.line_number:
                print(f"    行号: {violation.line_number}")
    
    if args.report:
        report = guard.generate_health_report()
        print(f"\n架构健康报告:")
        print(f"  总体健康度: {report['overall_health']}")
        print(f"  时间戳: {report['timestamp']}")
        
        if args.output:
            guard.export_report(report, args.output)
    
    if args.auto_fix:
        result = guard.validate_project_structure()
        violations = result["violations"]
        fixed = guard.auto_fix_violations(violations)
        if fixed:
            print("已自动修复部分违规")
        else:
            print("没有可自动修复的违规")


if __name__ == "__main__":
    main()

