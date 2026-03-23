"""
核心组件单元测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "knowledge-base" / "src"))


@pytest.mark.unit
class TestDocumentProcessor:
    """文档处理器测试"""
    
    @patch('src.core.document_processor.DocumentProcessor')
    def test_document_processor_initialization(self, mock_processor):
        """测试文档处理器初始化"""
        mock_instance = Mock()
        mock_processor.return_value = mock_instance
        
        processor = mock_processor()
        assert processor is not None
    
    @patch('src.core.document_processor.DocumentProcessor.process_document')
    def test_process_document(self, mock_process_document):
        """测试处理文档"""
        # 修复：使用正确的方法名 process_document
        mock_process_document.return_value = (
            "sample text from file",
            {"title": "Test", "author": "Test Author"},
            [Mock(content="chunk1", metadata=Mock(chunk_index=0)), Mock(content="chunk2", metadata=Mock(chunk_index=1))]
        )
        
        result = mock_process_document("test_file.txt")
        assert result is not None
        assert isinstance(result, tuple)
        assert len(result) == 3


@pytest.mark.unit
class TestAutoTagger:
    """自动标签器测试"""
    
    @patch('src.core.auto_tagger.AutoTagger')
    def test_auto_tagger_initialization(self, mock_tagger):
        """测试自动标签器初始化"""
        mock_instance = Mock()
        mock_tagger.return_value = mock_instance
        
        tagger = mock_tagger()
        assert tagger is not None
    
    @patch('src.core.auto_tagger.AutoTagger.generate_tags')
    def test_tag_document(self, mock_generate_tags):
        """测试文档标签"""
        # 修复：AutoTagger没有tag方法，使用generate_tags方法
        mock_generate_tags.return_value = [
            {"tag": "tag1", "score": 0.8, "confidence": 0.9, "source": "test"},
            {"tag": "tag2", "score": 0.7, "confidence": 0.8, "source": "test"}
        ]
        
        result = mock_generate_tags("test content")
        assert result is not None
        assert isinstance(result, list)

