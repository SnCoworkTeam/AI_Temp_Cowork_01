"""
文档处理节点
调用知识库服务进行文档解析和处理
"""
from typing import Dict, Any, Optional, List
import logging
import os

from .base_node import BaseNode, NodeExecutionError
from shared_libs.luminaos_common.common.http_client import HTTPClient
from ..config import settings

logger = logging.getLogger(__name__)


class DocumentProcessingNode(BaseNode):
    """文档处理节点 - 解析和处理文档内容"""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        config: Optional[Dict[str, Any]] = None,
        node_id: Optional[str] = None
    ):
        super().__init__(name, description, config, node_id)
        
        # 输入配置
        self.input_source = self.config.get("input_source", "state")  # state 或 file_path
        self.input_field = self.config.get("input_field", "content")  # 内容字段名
        self.file_path_field = self.config.get("file_path_field", "file_path")  # 文件路径字段名
        
        # 处理配置
        self.process_type = self.config.get("process_type", "parse")  # parse, upload, extract_metadata
        self.chunk_size = self.config.get("chunk_size", 1000)  # 分块大小
        self.chunk_overlap = self.config.get("chunk_overlap", 200)  # 分块重叠
        self.extract_metadata = self.config.get("extract_metadata", True)  # 是否提取元数据
        self.tags = self.config.get("tags", [])  # 文档标签
        
        # 知识库服务配置
        self.knowledge_base_url = self.config.get(
            "knowledge_base_url",
            settings.KNOWLEDGE_BASE_URL
        )
        self.timeout = self.config.get("timeout", 60)  # 文档处理可能需要更长时间
        
        # 输出配置
        self.output_key = self.config.get("output_key", f"{self.name}_processed")
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行文档处理节点
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态
        """
        try:
            if self.process_type == "upload":
                # 上传文档到知识库
                result = await self._upload_document(state)
            elif self.process_type == "parse":
                # 解析文档内容
                result = await self._parse_document(state)
            elif self.process_type == "extract_metadata":
                # 提取文档元数据
                result = await self._extract_metadata(state)
            else:
                raise NodeExecutionError(
                    self.name,
                    f"Unknown process type: {self.process_type}"
                )
            
            # 将结果添加到状态
            state[self.output_key] = result
            state[f"{self.name}_success"] = True
            
            logger.info(f"Document Processing Node '{self.name}' completed successfully")
            
            return state
        
        except NodeExecutionError:
            raise
        except Exception as e:
            raise NodeExecutionError(
                self.name,
                f"Document Processing Node execution failed: {str(e)}",
                e
            )
    
    async def _upload_document(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        上传文档到知识库
        
        Args:
            state: 工作流状态
        
        Returns:
            上传结果
        """
        # 获取文件路径
        file_path = self.get_state_value(state, self.file_path_field)
        if not file_path or not isinstance(file_path, str):
            raise NodeExecutionError(
                self.name,
                f"File path not found in state field: {self.file_path_field}"
            )
        
        if not os.path.exists(file_path):
            raise NodeExecutionError(
                self.name,
                f"File not found: {file_path}"
            )
        
        logger.info(f"Uploading document: {file_path}")
        
        # 调用MCP Gateway的文档管理工具
        try:
            async with HTTPClient(self.knowledge_base_url, timeout=self.timeout) as client:
                # 读取文件
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                filename = os.path.basename(file_path)
                
                # 使用multipart/form-data上传
                import httpx
                files = {'file': (filename, file_content)}
                data = {}
                if self.tags:
                    data['tags'] = ','.join(self.tags)
                
                async with httpx.AsyncClient() as http_client:
                    response = await http_client.post(
                        f"{self.knowledge_base_url}/api/documents/upload",
                        files=files,
                        data=data,
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                    upload_result = response.json()
        except Exception as e:
            raise NodeExecutionError(
                self.name,
                f"Failed to upload document: {str(e)}",
                e
            )
        
        return {
            "action": "upload",
            "document_id": upload_result.get("document_id"),
            "filename": filename,
            "status": upload_result.get("status"),
            "message": upload_result.get("message"),
        }
    
    async def _parse_document(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析文档内容
        
        Args:
            state: 工作流状态
        
        Returns:
            解析结果
        """
        # 获取文档ID或文件路径
        document_id = self.get_state_value(state, self.input_field)
        if not document_id:
            # 尝试从文件路径获取
            file_path = self.get_state_value(state, self.file_path_field)
            if file_path:
                # 先上传，再解析
                upload_result = await self._upload_document(state)
                document_id = upload_result.get("document_id")
            else:
                raise NodeExecutionError(
                    self.name,
                    f"Document ID or file path not found in state"
                )
        
        logger.info(f"Parsing document: {document_id}")
        
        # 获取文档信息（包含解析后的内容）
        try:
            async with HTTPClient(self.knowledge_base_url, timeout=self.timeout) as client:
                doc_info = await client.get(f"/api/documents/{document_id}")
        except Exception as e:
            raise NodeExecutionError(
                self.name,
                f"Failed to get document info: {str(e)}",
                e
            )
        
        # 提取文档块
        chunks = doc_info.get("chunks", [])
        processed_chunks = []
        
        for chunk in chunks:
            processed_chunks.append({
                "chunk_id": chunk.get("chunk_id"),
                "content": chunk.get("content", ""),
                "metadata": chunk.get("metadata", {}),
            })
        
        return {
            "action": "parse",
            "document_id": document_id,
            "filename": doc_info.get("filename"),
            "file_type": doc_info.get("file_type"),
            "metadata": doc_info.get("metadata", {}),
            "chunks": processed_chunks,
            "total_chunks": len(processed_chunks),
            "chunk_size": self.chunk_size,
        }
    
    async def _extract_metadata(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取文档元数据
        
        Args:
            state: 工作流状态
        
        Returns:
            元数据提取结果
        """
        # 获取文档ID
        document_id = self.get_state_value(state, self.input_field)
        if not document_id:
            raise NodeExecutionError(
                self.name,
                f"Document ID not found in state field: {self.input_field}"
            )
        
        logger.info(f"Extracting metadata from document: {document_id}")
        
        # 获取文档信息
        try:
            async with HTTPClient(self.knowledge_base_url, timeout=self.timeout) as client:
                doc_info = await client.get(f"/api/documents/{document_id}")
        except Exception as e:
            raise NodeExecutionError(
                self.name,
                f"Failed to get document info: {str(e)}",
                e
            )
        
        metadata = doc_info.get("metadata", {})
        
        return {
            "action": "extract_metadata",
            "document_id": document_id,
            "metadata": {
                "title": metadata.get("title"),
                "author": metadata.get("author"),
                "creation_date": metadata.get("creation_date"),
                "modification_date": metadata.get("modification_date"),
                "page_count": metadata.get("page_count"),
                "word_count": metadata.get("word_count"),
                "language": metadata.get("language"),
                "custom_metadata": metadata.get("custom_metadata", {}),
            },
            "file_type": doc_info.get("file_type"),
            "file_size": doc_info.get("file_size"),
            "tags": doc_info.get("tags", []),
        }
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """验证输入状态"""
        if not super().validate_input(state):
            return False
        
        if self.process_type == "upload":
            file_path = self.get_state_value(state, self.file_path_field)
            if not file_path:
                logger.warning(
                    f"Document Processing Node '{self.name}': "
                    f"file_path not found in state field '{self.file_path_field}'"
                )
                return False
        else:
            document_id = self.get_state_value(state, self.input_field)
            if not document_id:
                logger.warning(
                    f"Document Processing Node '{self.name}': "
                    f"document_id not found in state field '{self.input_field}'"
                )
                return False
        
        return True
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """验证输出状态"""
        if not super().validate_output(output):
            return False
        
        if self.output_key not in output:
            logger.warning(
                f"Document Processing Node '{self.name}' did not produce output"
            )
            return False
        
        return True









