"""
Excel解析器 - 解析项目Excel文件
"""

import io
import logging
from datetime import datetime
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

try:
    import openpyxl

    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    logger.warning("openpyxl not available, will use pandas only")


class ExcelParser:
    """Excel项目数据解析器"""

    def parse_excel(self, file_content: bytes) -> list[dict[str, Any]]:
        """
        解析Excel文件内容，返回项目数据列表

        Args:
            file_content: Excel文件的二进制内容

        Returns:
            项目数据列表，每个项目是一个字典
        """
        try:
            # 使用pandas读取Excel
            excel_file = io.BytesIO(file_content)

            # 尝试读取所有sheet
            excel_data = pd.ExcelFile(excel_file)
            projects = []

            # 遍历所有sheet，查找项目数据
            for sheet_name in excel_data.sheet_names:
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)

                    # 尝试从当前sheet解析项目
                    sheet_projects = self._parse_sheet(df, sheet_name)
                    if sheet_projects:
                        projects.extend(sheet_projects)

                except Exception as e:
                    logger.warning(f"解析sheet '{sheet_name}' 失败: {e!s}")
                    continue

            # 如果没有找到项目，尝试从第一个sheet解析
            if not projects:
                try:
                    df = pd.read_excel(excel_file, sheet_name=0)
                    projects = self._parse_sheet(df, "Sheet1")
                except Exception as e:
                    logger.exception(f"解析默认sheet失败: {e!s}")

            return projects

        except Exception as e:
            logger.error(f"解析Excel文件失败: {e!s}", exc_info=True)
            msg = f"无法解析Excel文件: {e!s}"
            raise ValueError(msg)

    def _parse_sheet(self, df: pd.DataFrame, sheet_name: str) -> list[dict[str, Any]]:
        """
        从DataFrame解析项目数据

        Args:
            df: pandas DataFrame
            sheet_name: sheet名称

        Returns:
            项目数据列表
        """
        projects = []

        # 清理DataFrame：删除空行和空列
        df = df.dropna(how="all").dropna(axis=1, how="all")

        if df.empty:
            return projects

        # 尝试识别列名（支持中英文）
        column_mapping = self._identify_columns(df)

        if not column_mapping:
            # 如果没有找到标准列名，尝试按位置解析
            return self._parse_by_position(df)

        # 按列名解析
        for idx, row in df.iterrows():
            try:
                project = self._parse_row(row, column_mapping)
                if project and project.get("name") and project.get("project_code"):
                    projects.append(project)
            except Exception as e:
                logger.warning(f"解析第 {idx+1} 行失败: {e!s}")
                continue

        return projects

    def _identify_columns(self, df: pd.DataFrame) -> dict[str, str]:
        """
        识别DataFrame中的列名

        Returns:
            列名映射字典 {标准列名: 实际列名}
        """
        column_mapping = {}

        # 列名映射表（支持多种可能的列名）
        possible_columns = {
            "project_code": ["项目编码", "项目代码", "编码", "code", "project_code", "项目编号"],
            "name": ["项目名称", "名称", "name", "project_name", "项目名"],
            "description": ["项目描述", "描述", "description", "desc", "备注"],
            "status": ["状态", "项目状态", "status", "项目状态"],
            "priority": ["优先级", "priority", "重要程度"],
            "start_date": ["开始日期", "计划开始", "start_date", "开始时间"],
            "end_date": ["结束日期", "计划结束", "end_date", "结束时间"],
            "progress_percent": ["进度", "完成度", "progress", "进度百分比", "完成百分比"],
            "health_score": ["健康度", "健康评分", "health_score", "健康度评分"],
        }

        # 获取DataFrame的实际列名
        actual_columns = [str(col).strip() for col in df.columns]

        # 匹配列名
        for standard_name, possible_names in possible_columns.items():
            for actual_col in actual_columns:
                if any(name.lower() in actual_col.lower() for name in possible_names):
                    column_mapping[standard_name] = actual_col
                    break

        return column_mapping

    def _parse_row(self, row: pd.Series, column_mapping: dict[str, str]) -> dict[str, Any] | None:
        """
        解析一行数据

        Args:
            row: pandas Series（一行数据）
            column_mapping: 列名映射

        Returns:
            项目数据字典
        """
        project = {}

        # 解析各个字段
        for standard_name, actual_col in column_mapping.items():
            if actual_col in row.index:
                value = row[actual_col]

                # 处理不同类型的值
                if pd.isna(value):
                    continue

                if standard_name in ["start_date", "end_date"]:
                    # 解析日期
                    project[standard_name] = self._parse_date(value)
                elif standard_name in ["progress_percent", "health_score"]:
                    # 解析数值
                    project[standard_name] = self._parse_float(value)
                else:
                    # 字符串值
                    project[standard_name] = str(value).strip()

        return project

    def _parse_by_position(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """
        按位置解析（当无法识别列名时）

        Args:
            df: pandas DataFrame

        Returns:
            项目数据列表
        """
        projects = []

        # 假设第一行是标题，从第二行开始是数据
        # 假设列顺序：项目编码、项目名称、描述、状态等
        for idx, row in df.iterrows():
            try:
                # 跳过可能的标题行
                if idx == 0 and any(
                    "编码" in str(v).lower() or "code" in str(v).lower() for v in row.values if pd.notna(v)
                ):
                    continue

                # 按位置提取数据
                values = [v for v in row.values if pd.notna(v)]
                if len(values) < 2:
                    continue

                project = {
                    "project_code": str(values[0]).strip() if len(values) > 0 else "",
                    "name": str(values[1]).strip() if len(values) > 1 else "",
                    "description": str(values[2]).strip() if len(values) > 2 else None,
                    "status": str(values[3]).strip().lower() if len(values) > 3 else "active",
                    "priority": str(values[4]).strip() if len(values) > 4 else "medium",
                }

                # 尝试解析日期和数值
                if len(values) > 5:
                    project["start_date"] = self._parse_date(values[5])
                if len(values) > 6:
                    project["end_date"] = self._parse_date(values[6])
                if len(values) > 7:
                    project["progress_percent"] = self._parse_float(values[7])

                if project.get("project_code") and project.get("name"):
                    projects.append(project)

            except Exception as e:
                logger.warning(f"按位置解析第 {idx+1} 行失败: {e!s}")
                continue

        return projects

    def _parse_date(self, value: Any) -> datetime | None:
        """解析日期值"""
        if pd.isna(value):
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime()

        # 尝试字符串解析
        if isinstance(value, str):
            try:
                # 尝试多种日期格式
                for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        return datetime.strptime(value.strip(), fmt)
                    except ValueError:
                        continue
            except:
                pass

        return None

    def _parse_float(self, value: Any) -> float:
        """解析浮点数值"""
        if pd.isna(value):
            return 0.0

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            # 移除百分号等字符
            value = value.replace("%", "").replace(",", "").strip()
            try:
                return float(value)
            except ValueError:
                return 0.0

        return 0.0
