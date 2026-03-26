import os
import sys
import types
import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from contextlib import contextmanager
from datetime import datetime

# 统一设置测试模式下的轻量化环境变量，避免外部依赖
os.environ.setdefault("KB_TEST_MODE", "true")
os.environ.setdefault("KB_DISABLE_EMBEDDING", "true")
os.environ.setdefault("KB_VECTOR_BACKEND", "memory")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

# --------- 伪造外部依赖（在未安装时） ---------
# psutil（memory_optimizer 依赖）
if 'psutil' not in sys.modules:
    sys.modules['psutil'] = types.ModuleType('psutil')

# luminaos_common.common.logger（routes 依赖）
try:
    import importlib.util
    spec = importlib.util.find_spec('luminaos_common')
except Exception:
    spec = None

if spec is None:
    lum_pkg = types.ModuleType('luminaos_common')
    lum_common = types.ModuleType('luminaos_common.common')
    lum_logger = types.ModuleType('luminaos_common.common.logger')
    import logging

    def setup_logger(*args, **kwargs):
        name = kwargs.get('name', 'luminaos')
        return logging.getLogger(name)

    lum_logger.setup_logger = setup_logger
    sys.modules['luminaos_common'] = lum_pkg
    sys.modules['luminaos_common.common'] = lum_common
    sys.modules['luminaos_common.common.logger'] = lum_logger


@pytest.fixture
def db_session():
    """提供一个可用于服务初始化与仓储调用的 SQLAlchemy Session mock。
    由于单元测试不依赖真实数据库，在此使用 MagicMock(spec=Session)。
    """
    return MagicMock(spec=Session)


# --------- 辅助数据结构（用于文档分块/预处理/质量评估等） ---------
class _ChunkMeta:
    def __init__(self, idx: int):
        self.chunk_index = idx
        self.start_char = idx * 10
        self.end_char = idx * 10 + 5
        self.page_number = 1
        self.metadata = {}

class _Chunk:
    def __init__(self, content: str, idx: int):
        self.content = content
        self.metadata = _ChunkMeta(idx)

class _PreprocessResult:
    def __init__(self, text: str):
        self.cleaned_text = text
        self.detected_language = "en"
        self.detected_encoding = "utf-8"

class _QualityScore:
    def __init__(self):
        self.overall_score = 0.9
        self.completeness_score = 0.9
        self.readability_score = 0.9
        self.uniqueness_score = 0.9

class _EnhancedMetadata:
    def __init__(self):
        self.summary = "summary"
        self.keywords = ["k1", "k2"]
        self.sentiment = "neutral"


# --------- 全局自动 Patch（不修改业务代码，测试模式下注入） ---------
@pytest.fixture(autouse=True)
def _patch_core_and_repos(monkeypatch):
    """在测试模式下，为核心组件与仓储注入轻量 mock，避免外部依赖/IO。
    """
    # EmbeddingManager - 关闭真实模型调用
    try:
        from src.core import embedding_manager as _em
        monkeypatch.setattr(_em.EmbeddingManager, "encode", lambda self, texts, batch_size=8: [[0.1, 0.2, 0.3]] * len(texts))
        monkeypatch.setattr(_em.EmbeddingManager, "get_dimension", lambda self: 384)
        monkeypatch.setattr(_em.EmbeddingManager, "is_available", lambda self: True)
    except Exception:
        pass

    # DocumentProcessor - 关闭真实解析/分块
    try:
        from src.core import document_processor as _dp
        monkeypatch.setattr(_dp.DocumentProcessor, "extract_text", lambda self, file_path: "sample text from file")
        monkeypatch.setattr(_dp.DocumentProcessor, "chunk_text", lambda self, text, strategy="smart": [_Chunk("chunk1", 0), _Chunk("chunk2", 1)])
    except Exception:
        pass

    # VectorStore - 使用空实现（add/search/delete）
    class _DummyVectorStore:
        def add_documents(self, texts, embeddings=None, metadatas=None, ids=None):
            return True
        def search(self, query, limit=10):
            return [{"id": "doc1", "score": 0.99}]
        def delete(self, ids=None):
            return True

    try:
        from src.core import vector_store as _vs
        monkeypatch.setattr(_vs, "get_vector_store", lambda: _DummyVectorStore())
    except Exception:
        pass

    # Processing Progress - 提供空实现（防止属性访问失败）
    class _DummyProgress:
        def start_stage(self, *args, **kwargs):
            return None
        def update_step(self, *args, **kwargs):
            return None
        def complete_stage(self, *args, **kwargs):
            return None
        def set_error(self, *args, **kwargs):
            return None

    try:
        from src.core import processing_progress as _pp
        monkeypatch.setattr(_pp, "get_progress_tracker", lambda document_id: _DummyProgress())
    except Exception:
        pass

    # Preprocessor / Quality / Metadata 增强 - 使用轻量返回
    try:
        from src.core import document_preprocessor as _prep
        monkeypatch.setattr(_prep, "get_preprocessor", lambda: type("_P", (), {"preprocess": lambda self, text: _PreprocessResult(text)})())
    except Exception:
        pass

    try:
        from src.core import document_quality as _dq
        monkeypatch.setattr(_dq, "get_quality_assessor", lambda: type("_Q", (), {"assess_quality": lambda self, text, md: _QualityScore()})())
    except Exception:
        pass

    try:
        from src.core import metadata_enhancer as _me
        monkeypatch.setattr(_me, "get_metadata_enhancer", lambda: type("_M", (), {"enhance": lambda self, text: _EnhancedMetadata()})())
    except Exception:
        pass

    # Memory Optimizer - 降低批次/禁用阈值
    class _DummyMemOpt:
        def calculate_optimal_batch_size(self, n, default_batch_size=15, min_batch_size=5, max_batch_size=30):
            return min(default_batch_size, max_batch_size)
        def get_memory_usage_mb(self):
            return 50.0
        @contextmanager
        def memory_monitor(self, name: str):
            yield
        def force_gc(self):
            return None
        def check_memory_threshold(self, ratio: float):
            return False

    try:
        from src.core import memory_optimizer as _mo
        monkeypatch.setattr(_mo, "get_memory_optimizer", lambda: _DummyMemOpt())
    except Exception:
        pass

    # Repositories - 为 DocumentService 提供最���实现
    class _DummyDoc:
        def __init__(self, doc_id="doc-123"):
            self.id = doc_id
            self.filename = "f.txt"
            self.file_type = "text"
            self.file_size = 1
            self.file_path = "/tmp/f.txt"
            self.status = "processed"
            self.version = 1
            self.tags = []
            self.category = None
            self.knowledge_base_id = None
            self.quality_score = None
            self.summary = None
            self.document_metadata = {}
            self.created_at = datetime.utcnow()
            self.processed_at = None
            self.updated_at = None

    try:
        from src.repositories import document_repository as _dr
        monkeypatch.setattr(_dr.DocumentRepository, "create_document", lambda self, **kwargs: _DummyDoc())
        monkeypatch.setattr(_dr.DocumentRepository, "get_by_id", lambda self, doc_id: _DummyDoc(doc_id))
        monkeypatch.setattr(_dr.DocumentRepository, "list_documents", lambda self, **kwargs: [_DummyDoc("doc-1"), _DummyDoc("doc-2")])
        monkeypatch.setattr(_dr.DocumentRepository, "count_documents", lambda self, **kwargs: 2)
        monkeypatch.setattr(_dr.DocumentRepository, "update_status", lambda self, doc_id, status: True)
        monkeypatch.setattr(_dr.DocumentRepository, "delete_document", lambda self, doc_id: True)
    except Exception:
        pass

    try:
        from src.repositories import chunk_repository as _cr
        monkeypatch.setattr(_cr.ChunkRepository, "get_by_document_id", lambda self, doc_id: [])
        monkeypatch.setattr(_cr.ChunkRepository, "create_chunks_batch", lambda self, doc_id, chunk_data_list: [type("_DbChunk", (), {"id": f"chunk-{i}", "chunk_index": d.get("chunk_index", i), "chunk_metadata": {}, "content": d.get("content", "")})() for i, d in enumerate(chunk_data_list)])
        monkeypatch.setattr(_cr.ChunkRepository, "delete_by_document_id", lambda self, doc_id: 0)
        monkeypatch.setattr(_cr.ChunkRepository, "get_chunks_with_embeddings", lambda self, doc_id: [])
    except Exception:
        pass

    try:
        from src.repositories import vector_repository as _vr
        monkeypatch.setattr(_vr.VectorRepository, "update_vector_index", lambda self, *args, **kwargs: True)
    except Exception:
        pass
