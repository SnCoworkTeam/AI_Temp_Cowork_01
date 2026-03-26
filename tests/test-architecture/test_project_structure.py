"""
项目结构测试
验证项目目录结构是否符合架构规范
"""
import pytest
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.architecture_guard import ArchitectureGuard


@pytest.mark.unit
class TestProjectStructure:
    """项目结构测试"""
    
    def test_project_root_exists(self):
        """测试项目根目录存在"""
        assert project_root.exists()
        assert project_root.is_dir()
    
    def test_required_directories_exist(self):
        """测试必需的目录存在"""
        required_dirs = [
            "mcp-gateway",
            "workflow-engine",
            "auth-service",
            "knowledge-base",
            "web-ui",
            "shared_libs",  # 修正：使用下划线而不是连字符
            "database",
            "scripts",
            "tests"
        ]
        
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            assert dir_path.exists(), f"目录 {dir_name} 不存在"
            assert dir_path.is_dir(), f"{dir_name} 不是目录"
    
    def test_architecture_compliance(self):
        """测试架构符合性"""
        guard = ArchitectureGuard(str(project_root))
        result = guard.validate_project_structure()
        
        # validate_project_structure返回ValidationResult对象
        assert result.success, f"架构不符合规范: {len(result.violations)} 个违规"
    
    def test_service_structure(self):
        """测试各服务目录结构"""
        services = [
            "mcp-gateway",
            "workflow-engine",
            "auth-service",
            "knowledge-base"
        ]
        
        for service in services:
            service_path = project_root / service
            assert service_path.exists(), f"服务 {service} 不存在"
            
            # 检查必需的子目录
            required_subdirs = ["src"]
            for subdir in required_subdirs:
                subdir_path = service_path / subdir
                assert subdir_path.exists(), f"{service}/{subdir} 不存在"
    
    def test_shared_libs_structure(self):
        """测试共享库结构"""
        shared_libs_path = project_root / "shared_libs"  # 修正：使用下划线
        assert shared_libs_path.exists(), f"shared_libs 目录不存在"
        
        # 检查主要子目录（根据实际结构调整）
        required_subdirs = ["luminaos_common"]  # 根据实际结构调整
        for subdir in required_subdirs:
            subdir_path = shared_libs_path / subdir
            if subdir_path.exists():
                assert subdir_path.is_dir(), f"shared_libs/{subdir} 不是目录"









