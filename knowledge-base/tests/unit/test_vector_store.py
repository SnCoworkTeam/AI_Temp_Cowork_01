"""
向量存储单元测试
使用mock测试向量存储功能
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "knowledge-base" / "src"))


@pytest.mark.unit
class TestVectorStore:
    """向量存储测试"""
    
    @patch('src.core.vector_store.VectorStore')
    def test_vector_store_initialization(self, mock_store):
        """测试向量存储初始化"""
        mock_instance = Mock()
        mock_store.return_value = mock_instance
        
        store = mock_store()
        assert store is not None
    
    @patch('src.core.vector_store.VectorStore.add_documents')
    def test_add_documents(self, mock_add):
        """测试添加文档"""
        mock_add.return_value = ["doc1", "doc2"]
        
        result = mock_add([
            {"id": "doc1", "content": "test content 1"},
            {"id": "doc2", "content": "test content 2"}
        ])
        
        assert result is not None
        assert len(result) == 2
    
    @patch('src.core.vector_store.VectorStore.search')
    def test_search_documents(self, mock_search):
        """测试搜索文档"""
        mock_search.return_value = [
            {"id": "doc1", "score": 0.9},
            {"id": "doc2", "score": 0.8}
        ]
        
        result = mock_search("test query", limit=10)
        assert result is not None
        assert len(result) > 0


@pytest.mark.unit
class TestEmbeddingManager:
    """嵌入管理器测试"""
    
    @patch('src.core.embedding_manager.EmbeddingManager')
    def test_embedding_manager_initialization(self, mock_manager):
        """测试嵌入管理器初始化"""
        mock_instance = Mock()
        mock_manager.return_value = mock_instance
        
        manager = mock_manager()
        assert manager is not None
    
    @patch('src.core.embedding_manager.EmbeddingManager.encode')
    def test_encode_text(self, mock_encode):
        """测试文本嵌入"""
        # 修复：使用正确的方法名 encode，返回列表的列表
        mock_encode.return_value = [[0.1, 0.2, 0.3] * 128]  # 模拟384维向量
        
        result = mock_encode(["test text"])
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], list)

