"""
智能分块策略
支持多种分块策略：固定大小、语义分块、层次分块、表格分块、代码分块等
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from ..models.document_models import DocumentChunk, ChunkMetadata

logger = logging.getLogger(__name__)


class ChunkingStrategy(str, Enum):
    """分块策略枚举"""
    FIXED = "fixed"  # 固定大小分块
    SEMANTIC = "semantic"  # 语义分块（按句子、段落）
    HIERARCHICAL = "hierarchical"  # 层次分块
    TABLE = "table"  # 表格分块
    CODE = "code"  # 代码分块
    SMART = "smart"  # 智能分块（自动选择策略）


class ChunkingStrategyFactory:
    """分块策略工厂"""
    
    @staticmethod
    def create_strategy(
        strategy: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        **kwargs
    ):
        """
        创建分块策略实例
        
        Args:
            strategy: 策略名称
            chunk_size: 分块大小
            chunk_overlap: 分块重叠
            **kwargs: 其他参数
        """
        strategy_enum = ChunkingStrategy(strategy.lower())
        
        if strategy_enum == ChunkingStrategy.FIXED:
            return FixedSizeChunking(chunk_size, chunk_overlap)
        elif strategy_enum == ChunkingStrategy.SEMANTIC:
            return SemanticChunking(chunk_size, chunk_overlap)
        elif strategy_enum == ChunkingStrategy.HIERARCHICAL:
            return HierarchicalChunking(chunk_size, chunk_overlap)
        elif strategy_enum == ChunkingStrategy.TABLE:
            return TableChunking(chunk_size, chunk_overlap)
        elif strategy_enum == ChunkingStrategy.CODE:
            return CodeChunking(chunk_size, chunk_overlap)
        elif strategy_enum == ChunkingStrategy.SMART:
            return SmartChunking(chunk_size, chunk_overlap)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")


class BaseChunkingStrategy:
    """分块策略基类"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        """
        分块文本
        
        Args:
            text: 文本内容
            metadata: 额外元数据
        
        Returns:
            文档块列表
        """
        raise NotImplementedError


class FixedSizeChunking(BaseChunkingStrategy):
    """固定大小分块策略"""
    
    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        """固定大小分块"""
        import uuid
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            
            # 尝试在句子边界处分割
            if end < len(text):
                for i in range(end, max(start, end - 100), -1):
                    if text[i] in '.!?\n':
                        end = i + 1
                        break
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk_metadata = ChunkMetadata(
                    chunk_id=str(uuid.uuid4()),
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end,
                    metadata={
                        **(metadata or {}),
                        "strategy": "fixed",
                        "chunk_size": len(chunk_text)
                    }
                )
                
                chunk = DocumentChunk(
                    chunk_id=chunk_metadata.chunk_id,
                    content=chunk_text,
                    metadata=chunk_metadata
                )
                
                chunks.append(chunk)
                chunk_index += 1
            
            # 如果已经到达文本末尾，结束循环避免死循环
            if end >= len(text):
                break

            next_start = end - self.chunk_overlap
            # 防止 start 不前进导致死循环
            if next_start <= start:
                next_start = end
            start = next_start
        
        return chunks


class SemanticChunking(BaseChunkingStrategy):
    """语义分块策略（按句子、段落）"""
    
    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        """语义分块：按段落和句子分块"""
        import uuid
        
        chunks = []
        chunk_index = 0
        
        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = ""
        current_start = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 如果当前块加上新段落超过大小限制，保存当前块
            if current_chunk and len(current_chunk) + len(para) + 2 > self.chunk_size:
                # 保存当前块
                end_pos = current_start + len(current_chunk)
                chunk_metadata = ChunkMetadata(
                    chunk_id=str(uuid.uuid4()),
                    chunk_index=chunk_index,
                    start_char=current_start,
                    end_char=end_pos,
                    metadata={
                        **(metadata or {}),
                        "strategy": "semantic",
                        "type": "paragraph"
                    }
                )
                
                chunk = DocumentChunk(
                    chunk_id=chunk_metadata.chunk_id,
                    content=current_chunk.strip(),
                    metadata=chunk_metadata
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # 开始新块（考虑重叠）
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                current_chunk = overlap_text + "\n\n" + para
                current_start = end_pos - len(overlap_text)
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
                    # 找到段落在原文中的位置
                    para_start = text.find(para, current_start)
                    if para_start != -1:
                        current_start = para_start
        
        # 处理最后一个块
        if current_chunk:
            end_pos = current_start + len(current_chunk)
            chunk_metadata = ChunkMetadata(
                chunk_id=str(uuid.uuid4()),
                chunk_index=chunk_index,
                start_char=current_start,
                end_char=end_pos,
                metadata={
                    **(metadata or {}),
                    "strategy": "semantic",
                    "type": "paragraph"
                }
            )
            
            chunk = DocumentChunk(
                chunk_id=chunk_metadata.chunk_id,
                content=current_chunk.strip(),
                metadata=chunk_metadata
            )
            chunks.append(chunk)
        
        return chunks


class HierarchicalChunking(BaseChunkingStrategy):
    """层次分块策略（文档 → 章节 → 段落 → 句子）"""
    
    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        """层次分块：多级分块"""
        import uuid
        
        chunks = []
        chunk_index = 0
        
        # 检测章节标题（Markdown风格或数字编号）
        section_pattern = re.compile(r'^(#{1,6}\s+.+|\d+\.\s+.+)$', re.MULTILINE)
        sections = []
        last_pos = 0
        
        for match in section_pattern.finditer(text):
            if match.start() > last_pos:
                sections.append((last_pos, match.start(), "content"))
            sections.append((match.start(), match.end(), "section"))
            last_pos = match.end()
        
        if last_pos < len(text):
            sections.append((last_pos, len(text), "content"))
        
        # 如果没有找到章节，按段落分块
        if not sections:
            sections = [(0, len(text), "content")]
        
        for section_start, section_end, section_type in sections:
            section_text = text[section_start:section_end]
            
            if section_type == "section":
                # 章节标题作为独立块
                chunk_metadata = ChunkMetadata(
                    chunk_id=str(uuid.uuid4()),
                    chunk_index=chunk_index,
                    start_char=section_start,
                    end_char=section_end,
                    metadata={
                        **(metadata or {}),
                        "strategy": "hierarchical",
                        "level": "section",
                        "type": "heading"
                    }
                )
                
                chunk = DocumentChunk(
                    chunk_id=chunk_metadata.chunk_id,
                    content=section_text.strip(),
                    metadata=chunk_metadata
                )
                chunks.append(chunk)
                chunk_index += 1
            else:
                # 内容部分按段落分块
                paragraphs = re.split(r'\n\s*\n', section_text)
                para_start = section_start
                
                for para in paragraphs:
                    para = para.strip()
                    if not para:
                        continue
                    
                    para_end = para_start + len(para)
                    
                    chunk_metadata = ChunkMetadata(
                        chunk_id=str(uuid.uuid4()),
                        chunk_index=chunk_index,
                        start_char=para_start,
                        end_char=para_end,
                        metadata={
                            **(metadata or {}),
                            "strategy": "hierarchical",
                            "level": "paragraph",
                            "type": "content"
                        }
                    )
                    
                    chunk = DocumentChunk(
                        chunk_id=chunk_metadata.chunk_id,
                        content=para,
                        metadata=chunk_metadata
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    
                    para_start = para_end + 2  # +2 for \n\n
        
        return chunks


class TableChunking(BaseChunkingStrategy):
    """表格分块策略（表格作为独立块）"""
    
    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        """表格分块：识别表格并作为独立块"""
        import uuid
        
        chunks = []
        chunk_index = 0
        last_pos = 0
        
        # 检测表格（Markdown表格或管道分隔的表格）
        table_pattern = re.compile(r'(\|.+\|\n)+', re.MULTILINE)
        
        for match in table_pattern.finditer(text):
            # 处理表格前的文本
            if match.start() > last_pos:
                pre_text = text[last_pos:match.start()].strip()
                if pre_text:
                    # 对非表格文本使用固定大小分块
                    fixed_chunker = FixedSizeChunking(self.chunk_size, self.chunk_overlap)
                    pre_chunks = fixed_chunker.chunk(pre_text, metadata)
                    for pre_chunk in pre_chunks:
                        pre_chunk.metadata.chunk_index = chunk_index
                        pre_chunk.metadata.metadata["strategy"] = "table_context"
                        chunks.append(pre_chunk)
                        chunk_index += 1
            
            # 表格作为独立块
            table_text = match.group(0).strip()
            chunk_metadata = ChunkMetadata(
                chunk_id=str(uuid.uuid4()),
                chunk_index=chunk_index,
                start_char=match.start(),
                end_char=match.end(),
                metadata={
                    **(metadata or {}),
                    "strategy": "table",
                    "type": "table",
                    "row_count": table_text.count('\n')
                }
            )
            
            chunk = DocumentChunk(
                chunk_id=chunk_metadata.chunk_id,
                content=table_text,
                metadata=chunk_metadata
            )
            chunks.append(chunk)
            chunk_index += 1
            
            last_pos = match.end()
        
        # 处理剩余文本
        if last_pos < len(text):
            remaining_text = text[last_pos:].strip()
            if remaining_text:
                fixed_chunker = FixedSizeChunking(self.chunk_size, self.chunk_overlap)
                remaining_chunks = fixed_chunker.chunk(remaining_text, metadata)
                for rem_chunk in remaining_chunks:
                    rem_chunk.metadata.chunk_index = chunk_index
                    rem_chunk.metadata.metadata["strategy"] = "table_context"
                    chunks.append(rem_chunk)
                    chunk_index += 1
        
        return chunks if chunks else FixedSizeChunking(self.chunk_size, self.chunk_overlap).chunk(text, metadata)


class CodeChunking(BaseChunkingStrategy):
    """代码分块策略（代码块保持完整性）"""
    
    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        """代码分块：识别代码块并保持完整性"""
        import uuid
        
        chunks = []
        chunk_index = 0
        last_pos = 0
        
        # 检测代码块（Markdown代码块或缩进代码）
        code_block_pattern = re.compile(r'```[\w]*\n(.*?)```', re.DOTALL | re.MULTILINE)
        indented_code_pattern = re.compile(r'^(\s{4,}|\t+)(.+)$', re.MULTILINE)
        
        code_blocks = []
        for match in code_block_pattern.finditer(text):
            code_blocks.append((match.start(), match.end(), match.group(0), "code_block"))
        
        for match in indented_code_pattern.finditer(text):
            # 检查是否是连续的代码块
            if not code_blocks or match.start() > code_blocks[-1][1]:
                code_blocks.append((match.start(), match.end(), match.group(0), "indented_code"))
        
        # 按位置排序
        code_blocks.sort(key=lambda x: x[0])
        
        for code_start, code_end, code_text, code_type in code_blocks:
            # 处理代码前的文本
            if code_start > last_pos:
                pre_text = text[last_pos:code_start].strip()
                if pre_text:
                    fixed_chunker = FixedSizeChunking(self.chunk_size, self.chunk_overlap)
                    pre_chunks = fixed_chunker.chunk(pre_text, metadata)
                    for pre_chunk in pre_chunks:
                        pre_chunk.metadata.chunk_index = chunk_index
                        pre_chunk.metadata.metadata["strategy"] = "code_context"
                        chunks.append(pre_chunk)
                        chunk_index += 1
            
            # 代码块作为独立块（保持完整性）
            chunk_metadata = ChunkMetadata(
                chunk_id=str(uuid.uuid4()),
                chunk_index=chunk_index,
                start_char=code_start,
                end_char=code_end,
                metadata={
                    **(metadata or {}),
                    "strategy": "code",
                    "type": code_type,
                    "language": self._detect_language(code_text)
                }
            )
            
            chunk = DocumentChunk(
                chunk_id=chunk_metadata.chunk_id,
                content=code_text.strip(),
                metadata=chunk_metadata
            )
            chunks.append(chunk)
            chunk_index += 1
            
            last_pos = code_end
        
        # 处理剩余文本
        if last_pos < len(text):
            remaining_text = text[last_pos:].strip()
            if remaining_text:
                fixed_chunker = FixedSizeChunking(self.chunk_size, self.chunk_overlap)
                remaining_chunks = fixed_chunker.chunk(remaining_text, metadata)
                for rem_chunk in remaining_chunks:
                    rem_chunk.metadata.chunk_index = chunk_index
                    rem_chunk.metadata.metadata["strategy"] = "code_context"
                    chunks.append(rem_chunk)
                    chunk_index += 1
        
        return chunks if chunks else FixedSizeChunking(self.chunk_size, self.chunk_overlap).chunk(text, metadata)
    
    def _detect_language(self, code_text: str) -> Optional[str]:
        """检测代码语言"""
        # 简单的语言检测
        if 'def ' in code_text or 'import ' in code_text:
            return "python"
        elif 'function ' in code_text or 'const ' in code_text:
            return "javascript"
        elif 'public class' in code_text or 'import java' in code_text:
            return "java"
        elif '#include' in code_text:
            return "cpp"
        return None


class SmartChunking(BaseChunkingStrategy):
    """智能分块策略（根据内容类型自动选择策略）"""
    
    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        """智能分块：根据内容自动选择最佳策略"""
        # 检测内容类型
        has_tables = bool(re.search(r'\|.+\|', text))
        has_code = bool(re.search(r'```|^\s{4,}', text, re.MULTILINE))
        has_sections = bool(re.search(r'^#{1,6}\s+|^\d+\.\s+', text, re.MULTILINE))
        
        # 根据内容类型选择策略
        if has_tables and has_code:
            # 混合内容：使用层次分块
            strategy = HierarchicalChunking(self.chunk_size, self.chunk_overlap)
        elif has_tables:
            # 有表格：使用表格分块
            strategy = TableChunking(self.chunk_size, self.chunk_overlap)
        elif has_code:
            # 有代码：使用代码分块
            strategy = CodeChunking(self.chunk_size, self.chunk_overlap)
        elif has_sections:
            # 有章节：使用层次分块
            strategy = HierarchicalChunking(self.chunk_size, self.chunk_overlap)
        else:
            # 普通文本：使用语义分块
            strategy = SemanticChunking(self.chunk_size, self.chunk_overlap)
        
        chunks = strategy.chunk(text, metadata)
        
        # 标记为智能分块
        for chunk in chunks:
            chunk.metadata.metadata["strategy"] = "smart"
            chunk.metadata.metadata["auto_selected"] = strategy.__class__.__name__
        
        return chunks

