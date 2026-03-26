"""
MCP Gateway 工具函数测试
"""
import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "mcp-gateway" / "src"))


@pytest.mark.unit
class TestUtils:
    """工具函数测试"""
    
    def test_parameter_validation(self):
        """测试参数验证"""
        try:
            from src.core.config_manager import validate_parameters
        except ImportError:
            pytest.skip("validate_parameters not available")
            return
        
        # 有效参数
        valid_params = {"input": "test"}
        schema = {
            "type": "object",
            "properties": {
                "input": {"type": "string"}
            },
            "required": ["input"]
        }
        
        result = validate_parameters(valid_params, schema)
        assert result is True
        
        # 无效参数
        invalid_params = {}
        result = validate_parameters(invalid_params, schema)
        assert result is False
    
    def test_error_handling(self):
        """测试错误处理"""
        try:
            from shared_libs.common.error_handler import create_error_response
        except ImportError:
            pytest.skip("create_error_response not available")
            return
        
        error_response = create_error_response(
            status_code=400,
            message="Test error",
            details="Test details"
        )
        
        assert error_response.status_code == 400
        data = error_response.body
        assert "Test error" in str(data)







