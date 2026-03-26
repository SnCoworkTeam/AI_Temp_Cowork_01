#!/usr/bin/env python3
"""测试文档解析"""
import sys
sys.path.insert(0, '/app')

from src.core.document_processor import get_document_processor

file_path = '/app/documents/6f45695a-d007-410a-a214-275ab8397486.docx'

print("="*60)
print("测试文档解析")
print("="*60)
print(f"文件路径: {file_path}")

try:
    processor = get_document_processor()
    print("文档处理器已加载")
    
    print("\n开始解析文档...")
    result = processor.process_document(file_path, chunking_strategy='smart')
    
    if isinstance(result, tuple):
        text, metadata, chunks = result
        print(f"✅ 解析成功！")
        print(f"文本长度: {len(text)} 字符")
        print(f"块数: {len(chunks)}")
        if metadata:
            print(f"元数据: {metadata}")
    else:
        print(f"✅ 解析成功！")
        print(f"文本长度: {len(result.get('text', ''))} 字符")
        print(f"块数: {len(result.get('chunks', []))}")
        
except Exception as e:
    print(f"❌ 解析失败: {str(e)}")
    import traceback
    traceback.print_exc()


