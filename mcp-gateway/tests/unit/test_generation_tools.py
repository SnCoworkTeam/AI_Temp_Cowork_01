import asyncio
from pathlib import Path

import pytest

from src.tools.ppt_generator_tool import PPTGeneratorTool
from src.tools.docx_generator_tool import DOCXGeneratorTool
from src.tools.excel_generator_tool import ExcelGeneratorTool


@pytest.mark.asyncio
async def test_generate_ppt_local(monkeypatch):
    # 禁用 MinIO 上传，确保本地生成通过
    monkeypatch.setenv("MINIO_ENDPOINT", "")
    tool = PPTGeneratorTool()
    result = await tool.execute(
        {
            "sections": [
                {"title": "概览", "bullets": ["要点1", "要点2"]},
                {"title": "计划", "bullets": ["任务A", "任务B"]},
            ]
        }
    )
    assert "file_path" in result
    assert Path(result["file_path"]).exists()


@pytest.mark.asyncio
async def test_generate_docx_local(monkeypatch):
    monkeypatch.setenv("MINIO_ENDPOINT", "")
    tool = DOCXGeneratorTool()
    result = await tool.execute(
        {
            "sections": [
                {"title": "摘要", "content": "自动化报告摘要"},
                {"title": "数据", "tables": [["列1", "列2"], ["A", "B"]]},
            ]
        }
    )
    assert "file_path" in result
    assert Path(result["file_path"]).exists()


@pytest.mark.asyncio
async def test_generate_excel_local(monkeypatch):
    monkeypatch.setenv("MINIO_ENDPOINT", "")
    tool = ExcelGeneratorTool()
    result = await tool.execute(
        {
            "sheets": [
                {
                    "name": "Sheet1",
                    "headers": ["h1", "h2"],
                    "rows": [["a", 1], ["b", 2]],
                    "summary": {"label": "合计", "formula_row": "=SUM(B2:B3)"},
                }
            ]
        }
    )
    assert "file_path" in result
    assert Path(result["file_path"]).exists()




















