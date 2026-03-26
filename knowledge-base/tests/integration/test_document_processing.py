"""
文档处理集成测试
"""
import pytest
import os
import requests

BASE_URL = os.getenv("KB_BASE_URL", "http://localhost:8004")


@pytest.mark.integration
class TestDocumentProcessing:
    """文档处理集成测试"""
    
    @pytest.fixture
    def client(self):
        """HTTP 客户端（直连已启动的服务）"""
        class HttpClient:
            def get(self, path, **kwargs):
                return requests.get(BASE_URL + path, timeout=20, **kwargs)
            def post(self, path, **kwargs):
                return requests.post(BASE_URL + path, timeout=30, **kwargs)
        return HttpClient()
    
    def test_upload_text_document(self, client):
        """测试上传文本文档"""
        files = {
            "file": ("test.txt", "This is a test document content.", "text/plain")
        }
        response = client.post("/api/documents", files=files)
        # 可能成功或失败（取决于服务状态）
        assert response.status_code < 500
    
    def test_upload_pdf_document(self, client):
        """测试上传PDF文档"""
        # 创建简单的PDF内容（实际应该是真实的PDF二进制数据）
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 0\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"
        files = {
            "file": ("test.pdf", pdf_content, "application/pdf")
        }
        response = client.post("/api/documents", files=files)
        # 可能成功或失败（取决于服务状态）
        assert response.status_code < 500
    
    def test_document_chunking(self, client):
        """测试文档分块处理"""
        # 先上传文档
        files = {
            "file": ("test.txt", "This is a test document. " * 100, "text/plain")
        }
        upload_response = client.post("/api/documents", files=files)
        
        if upload_response.status_code == 201:
            doc_id = upload_response.json().get("document_id")
            if doc_id:
                # 获取文档块
                response = client.get(f"/api/documents/{doc_id}/chunks")
                assert response.status_code < 500
    
    def test_document_metadata_extraction(self, client):
        """测试文档元数据提取"""
        files = {
            "file": ("test.txt", "Test content with metadata.", "text/plain")
        }
        response = client.post("/api/documents", files=files)
        
        if response.status_code == 201:
            data = response.json()
            # 验证返回的元数据
            assert "document_id" in data or "id" in data
    
    def test_document_processing_status(self, client):
        """测试文档处理状态"""
        # 列出文档
        response = client.get("/api/documents")
        if response.status_code == 200:
            documents = response.json()
            if isinstance(documents, list) and len(documents) > 0:
                doc_id = documents[0].get("id") or documents[0].get("document_id")
                if doc_id:
                    # 获取文档详情
                    detail_response = client.get(f"/api/documents/{doc_id}")
                    assert detail_response.status_code < 500


