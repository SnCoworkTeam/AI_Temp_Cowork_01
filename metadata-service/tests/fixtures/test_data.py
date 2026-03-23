"""
测试数据
"""
from datetime import datetime

# 测试数据资产
SAMPLE_DATA_ASSET = {
    "name": "test_dataset",
    "display_name": "Test Dataset",
    "description": "Test dataset for unit testing",
    "asset_type": "dataset",
    "status": "active",
    "source_system": "test_system",
    "source_path": "/test/path",
    "tags": ["test", "unit-test"],
    "schema_info": {
        "columns": [
            {"name": "id", "type": "integer"},
            {"name": "name", "type": "string"}
        ]
    }
}

# 测试AI模型
SAMPLE_AI_MODEL = {
    "name": "test_model",
    "model_type": "llm",
    "framework": "pytorch",
    "version": "1.0.0",
    "description": "Test AI model"
}

# 测试业务实体
SAMPLE_BUSINESS_ENTITY = {
    "name": "test_entity",
    "entity_type": "term",
    "definition": "Test business entity",
    "description": "Test entity for unit testing"
}

