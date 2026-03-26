"""
LLM节点（已废弃）
此文件已废弃，请使用 workflow-engine/src/nodes/llm_node.py 中的实现

该文件保留是为了向后兼容，但实际使用的是 src/nodes/llm_node.py 中的完整实现
（支持LangChain、DeepSeek API等）
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# 导入真正的实现
from ...nodes.llm_node import LLMNode

# 重新导出，保持向后兼容
__all__ = ['LLMNode']


