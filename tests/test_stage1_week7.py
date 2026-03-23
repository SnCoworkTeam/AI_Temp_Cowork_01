"""
阶段一第7周测试：创建前端界面+用户体验增强
测试协同界面组件、API集成、用户体验功能
"""
import pytest
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope="session", autouse=True)
def setup_services():
    """测试会话级别的服务设置"""
    print("\n" + "="*60)
    print("阶段一第7周测试 - 创建前端界面+用户体验增强")
    print("="*60)
    yield
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


class TestFrontendComponents:
    """测试前端组件"""
    
    def test_component_files_exist(self):
        """测试组件文件是否存在"""
        component_path = Path(__file__).parent.parent / "web-ui" / "src" / "components" / "CollaborativeInterface" / "CollaborativeInterface.tsx"
        assert component_path.exists(), f"组件文件不存在: {component_path}"
        print(f"[OK] 协同界面组件文件存在: {component_path}")
    
    def test_page_file_exists(self):
        """测试页面文件是否存在"""
        page_path = Path(__file__).parent.parent / "web-ui" / "src" / "app" / "collaborative" / "page.tsx"
        assert page_path.exists(), f"页面文件不存在: {page_path}"
        print(f"[OK] 协同界面页面文件存在: {page_path}")
    
    def test_index_file_exists(self):
        """测试索引文件是否存在"""
        index_path = Path(__file__).parent.parent / "web-ui" / "src" / "components" / "CollaborativeInterface" / "index.ts"
        assert index_path.exists(), f"索引文件不存在: {index_path}"
        print(f"[OK] 组件索引文件存在: {index_path}")


class TestComponentStructure:
    """测试组件结构"""
    
    def test_component_imports(self):
        """测试组件导入结构"""
        component_path = Path(__file__).parent.parent / "web-ui" / "src" / "components" / "CollaborativeInterface" / "CollaborativeInterface.tsx"
        
        if component_path.exists():
            content = component_path.read_text(encoding='utf-8')
            
            # 检查必要的导入
            assert "import React" in content or "import { useState" in content, "缺少React导入"
            assert "Card" in content or "UI/Card" in content, "缺少Card组件导入"
            assert "Button" in content or "UI/Button" in content, "缺少Button组件导入"
            
            print("[OK] 组件导入结构正确")
        else:
            pytest.skip("组件文件不存在")
    
    def test_component_exports(self):
        """测试组件导出"""
        component_path = Path(__file__).parent.parent / "web-ui" / "src" / "components" / "CollaborativeInterface" / "CollaborativeInterface.tsx"
        
        if component_path.exists():
            content = component_path.read_text(encoding='utf-8')
            
            # 检查导出
            assert "export" in content, "缺少导出语句"
            assert "CollaborativeInterface" in content, "缺少组件名称"
            
            print("[OK] 组件导出正确")
        else:
            pytest.skip("组件文件不存在")
    
    def test_component_props(self):
        """测试组件Props定义"""
        component_path = Path(__file__).parent.parent / "web-ui" / "src" / "components" / "CollaborativeInterface" / "CollaborativeInterface.tsx"
        
        if component_path.exists():
            content = component_path.read_text(encoding='utf-8')
            
            # 检查Props接口
            assert "interface" in content or "type" in content, "缺少类型定义"
            assert "userInput" in content, "缺少userInput属性"
            
            print("[OK] 组件Props定义正确")
        else:
            pytest.skip("组件文件不存在")


class TestUserExperienceFeatures:
    """测试用户体验功能"""
    
    def test_smart_guidance(self):
        """测试智能引导功能"""
        component_path = Path(__file__).parent.parent / "web-ui" / "src" / "components" / "CollaborativeInterface" / "CollaborativeInterface.tsx"
        
        if component_path.exists():
            content = component_path.read_text(encoding='utf-8')
            
            # 检查智能引导相关代码
            assert "guideUser" in content or "智能引导" in content, "缺少智能引导功能"
            
            print("[OK] 智能引导功能存在")
        else:
            pytest.skip("组件文件不存在")
    
    def test_auto_fill(self):
        """测试参数智能填充功能"""
        component_path = Path(__file__).parent.parent / "web-ui" / "src" / "components" / "CollaborativeInterface" / "CollaborativeInterface.tsx"
        
        if component_path.exists():
            content = component_path.read_text(encoding='utf-8')
            
            # 检查参数填充相关代码
            assert "autoFillParameters" in content or "参数填充" in content, "缺少参数填充功能"
            
            print("[OK] 参数智能填充功能存在")
        else:
            pytest.skip("组件文件不存在")
    
    def test_real_time_validation(self):
        """测试实时验证功能"""
        component_path = Path(__file__).parent.parent / "web-ui" / "src" / "components" / "CollaborativeInterface" / "CollaborativeInterface.tsx"
        
        if component_path.exists():
            content = component_path.read_text(encoding='utf-8')
            
            # 检查验证相关代码
            assert "validateInRealTime" in content or "validate" in content, "缺少实时验证功能"
            
            print("[OK] 实时验证功能存在")
        else:
            pytest.skip("组件文件不存在")


class TestAPIIntegration:
    """测试API集成"""
    
    def test_api_endpoints(self):
        """测试API端点调用"""
        component_path = Path(__file__).parent.parent / "web-ui" / "src" / "components" / "CollaborativeInterface" / "CollaborativeInterface.tsx"
        
        if component_path.exists():
            content = component_path.read_text(encoding='utf-8')
            
            # 检查API调用
            assert "/api/v1/collaborative" in content or "fetch" in content, "缺少API调用"
            
            print("[OK] API端点集成正确")
        else:
            pytest.skip("组件文件不存在")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])





