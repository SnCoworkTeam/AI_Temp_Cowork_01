"""
文档预处理
支持文档清洗、格式标准化、编码检测、语言检测
"""
import logging
import re
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 尝试导入语言检测库
try:
    import langdetect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("langdetect not available, language detection disabled")

# 尝试导入编码检测库
try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False
    logger.warning("chardet not available, encoding detection disabled")


@dataclass
class PreprocessingResult:
    """预处理结果"""
    cleaned_text: str
    detected_encoding: Optional[str] = None
    detected_language: Optional[str] = None
    original_length: int = 0
    cleaned_length: int = 0
    changes: Dict[str, Any] = None


class DocumentPreprocessor:
    """文档预处理器"""
    
    def __init__(self):
        # 常见噪音模式
        self.noise_patterns = [
            r'\x00',  # 空字符
            r'\r\n',  # Windows换行（标准化为\n）
            r'\r',  # Mac换行（标准化为\n）
            r'[\x00-\x08\x0B-\x0C\x0E-\x1F]',  # 控制字符
        ]
        
        # 多余空白模式
        self.whitespace_patterns = [
            (r' {2,}', ' '),  # 多个空格替换为单个
            (r'\n{3,}', '\n\n'),  # 多个换行替换为两个
            (r'\t+', ' '),  # Tab替换为空格
        ]
    
    def preprocess(
        self,
        text: str,
        encoding: Optional[str] = None,
        detect_encoding: bool = True,
        detect_language: bool = True,
        clean_text: bool = True,
        normalize_format: bool = True
    ) -> PreprocessingResult:
        """
        预处理文档
        
        Args:
            text: 原始文本
            encoding: 已知编码（如果为None则自动检测）
            detect_encoding: 是否检测编码
            detect_language: 是否检测语言
            clean_text: 是否清洗文本
            normalize_format: 是否标准化格式
        
        Returns:
            预处理结果
        """
        original_length = len(text)
        cleaned_text = text
        detected_encoding = encoding
        detected_language = None
        changes = {}
        
        # 检测编码
        if detect_encoding and not encoding and CHARDET_AVAILABLE:
            detected_encoding = self._detect_encoding(text)
            changes['encoding_detected'] = detected_encoding
        
        # 清洗文本
        if clean_text:
            cleaned_text = self._clean_text(cleaned_text)
            changes['text_cleaned'] = True
        
        # 标准化格式
        if normalize_format:
            cleaned_text = self._normalize_format(cleaned_text)
            changes['format_normalized'] = True
        
        # 检测语言
        if detect_language and LANGDETECT_AVAILABLE:
            detected_language = self._detect_language(cleaned_text)
            changes['language_detected'] = detected_language
        
        return PreprocessingResult(
            cleaned_text=cleaned_text,
            detected_encoding=detected_encoding,
            detected_language=detected_language,
            original_length=original_length,
            cleaned_length=len(cleaned_text),
            changes=changes
        )
    
    def _clean_text(self, text: str) -> str:
        """清洗文本（移除噪音）"""
        cleaned = text
        
        # 移除噪音字符
        for pattern in self.noise_patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        # 移除不可见字符（保留换行和空格）
        cleaned = ''.join(c for c in cleaned if c.isprintable() or c in '\n\t')
        
        return cleaned
    
    def _normalize_format(self, text: str) -> str:
        """标准化格式"""
        normalized = text
        
        # 标准化换行符
        normalized = normalized.replace('\r\n', '\n').replace('\r', '\n')
        
        # 标准化空白
        for pattern, replacement in self.whitespace_patterns:
            normalized = re.sub(pattern, replacement, normalized)
        
        # 移除行首行尾空白
        lines = [line.strip() for line in normalized.split('\n')]
        normalized = '\n'.join(lines)
        
        # 移除文档首尾空白
        normalized = normalized.strip()
        
        return normalized
    
    def _detect_encoding(self, text: bytes) -> Optional[str]:
        """检测文本编码"""
        if not CHARDET_AVAILABLE:
            return None
        
        try:
            result = chardet.detect(text)
            if result and result['confidence'] > 0.7:
                return result['encoding']
        except Exception as e:
            logger.warning(f"Failed to detect encoding: {str(e)}")
        
        return None
    
    def _detect_language(self, text: str) -> Optional[str]:
        """检测文本语言"""
        if not LANGDETECT_AVAILABLE:
            return None
        
        try:
            # 只检测前1000个字符（提高速度）
            sample = text[:1000] if len(text) > 1000 else text
            if not sample.strip():
                return None
            
            language = langdetect.detect(sample)
            return language
        except Exception as e:
            logger.warning(f"Failed to detect language: {str(e)}")
            return None


# 全局预处理器实例
_preprocessor: Optional[DocumentPreprocessor] = None


def get_preprocessor() -> DocumentPreprocessor:
    """获取预处理器单例"""
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = DocumentPreprocessor()
    return _preprocessor


