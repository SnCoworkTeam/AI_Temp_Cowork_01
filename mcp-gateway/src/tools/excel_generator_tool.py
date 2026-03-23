"""
Excel 生成工具
支持多 Sheet 报表，输出存储到本地并可选上传 MinIO
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from openpyxl import Workbook  # type: ignore

from .storage import upload_to_minio

logger = logging.getLogger(__name__)


CONTENT_TYPE_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class ExcelGeneratorTool:
    name = "generate_excel"
    description = "生成多Sheet报表，支持表头/数据/合计，返回文件路径与下载URL"
    version = "1.0.0"

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        payload:
        - sheets: [
            {
              "name": "Sheet1",
              "headers": [...],
              "rows": [[...]],
              "summary": {"label": "合计", "formula_row": "SUM(B2:B10)" } (可选)
            }
          ]
        """
        sheets: List[Dict[str, Any]] = payload.get("sheets", []) or []

        wb = Workbook()
        # 删除默认sheet
        default_sheet = wb.active
        wb.remove(default_sheet)

        for sheet in sheets:
            ws = wb.create_sheet(sheet.get("name", "Sheet1"))
            headers = sheet.get("headers", []) or []
            if headers:
                ws.append(headers)

            for row in sheet.get("rows", []) or []:
                ws.append(row)

            summary = sheet.get("summary")
            if summary and summary.get("formula_row"):
                ws.append([summary.get("label", "合计"), summary["formula_row"]])

        tmpdir = Path(tempfile.mkdtemp())
        outfile = tmpdir / "report.xlsx"
        wb.save(outfile)

        download_url: Optional[str] = None
        try:
            download_url = upload_to_minio(outfile, content_type=CONTENT_TYPE_XLSX)
        except Exception as e:
            logger.warning(f"MinIO upload skipped/failure: {e}")

        return {
            "file_path": str(outfile),
            "download_url": download_url,
        }




















