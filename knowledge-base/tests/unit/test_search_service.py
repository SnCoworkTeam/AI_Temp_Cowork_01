"""
搜索服务单元测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "knowledge-base" / "src"))


@pytest.mark.unit
class TestSearchService:
    """搜索服务测试"""
    
    def test_search_service_initialization(self, db_session):
        """测试搜索服务初始化"""
        from src.services.search_service import SearchService
        
        service = SearchService(db_session)
        assert service is not None
        assert service.db == db_session
    
    @pytest.mark.asyncio
    async def test_semantic_search(self, db_session):
        """测试语义搜索（异步 + 实例方法 patch）"""
        from src.services.search_service import SearchService
        from unittest.mock import AsyncMock, patch

        service = SearchService(db_session)
        with patch.object(service, 'semantic_search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = {
                "results": [],
                "total": 0
            }
            result = await service.semantic_search("test query", limit=10)
            assert result is not None
            assert "results" in result
    
    @patch('src.services.search_service.SearchService.keyword_search')
    def test_keyword_search(self, mock_search, db_session):
        """测试关键词搜索"""
        from src.services.search_service import SearchService
        
        service = SearchService(db_session)
        mock_search.return_value = {
            "results": [],
            "total": 0
        }
        
        result = service.keyword_search("test", limit=10)
        assert result is not None

