"""
DOCX 生成工具
支持基于模板生成 Word 文档，输出存储到本地并可选上传 MinIO
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from docx import Document  # type: ignore

from .storage import upload_to_minio

logger = logging.getLogger(__name__)


CONTENT_TYPE_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class DOCXGeneratorTool:
    name = "generate_docx"
    description = "基于模板生成Word文档，支持段落/表格/图片，返回文件路径与下载URL"
    version = "1.0.0"

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        payload:
        - template: 模板路径（可选）
        - sections: [{title, content, tables: [[...]], images: [{path,title}]}]
        - outline: [标题列表]（可选）
        """
        template = payload.get("template")
        sections: List[Dict[str, Any]] = payload.get("sections", []) or []

        doc = Document(template) if template else Document()

        for sec in sections:
            if sec.get("title"):
                doc.add_heading(sec["title"], level=2)
            content = sec.get("content")
            if content:
                doc.add_paragraph(str(content))

            # 表格
            tables = sec.get("tables", []) or []
            for tbl in tables:
                rows = tbl or []
                if not rows:
                    continue
                cols = len(rows[0])
                t = doc.add_table(rows=len(rows), cols=cols)
                for i, row in enumerate(rows):
                    for j, cell in enumerate(row):
                        t.rows[i].cells[j].text = str(cell)

            # 图片
            images = sec.get("images", []) or []
            for img in images:
                path = img.get("path")
                if not path:
                    continue
                try:
                    doc.add_picture(str(path))
                except Exception as e:
                    logger.warning(f"Failed to insert image {path}: {e}")

        tmpdir = Path(tempfile.mkdtemp())
        outfile = tmpdir / "report.docx"
        doc.save(outfile)

        download_url: Optional[str] = None
        try:
            download_url = upload_to_minio(outfile, content_type=CONTENT_TYPE_DOCX)
        except Exception as e:
            logger.warning(f"MinIO upload skipped/failure: {e}")

        return {
            "file_path": str(outfile),
            "download_url": download_url,
        }




















