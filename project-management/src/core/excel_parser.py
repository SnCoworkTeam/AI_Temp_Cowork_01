"""
Excel项目周报解析器
解析2025项目周月进度报告.xlsx格式
"""
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, date
import re
import logging

logger = logging.getLogger(__name__)


class ExcelProjectParser:
    """解析Excel项目周报"""
    
    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls']
    
    async def parse_project_excel(self, file_path: str) -> Dict[str, Any]:
        """
        解析Excel文件，提取项目信息
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            包含项目信息的字典
        """
        try:
            # 读取所有sheet
            xls = pd.ExcelFile(file_path)
            logger.info(f"Excel文件包含 {len(xls.sheet_names)} 个Sheet: {xls.sheet_names}")
            
            all_projects = []
            
            # 遍历每个sheet（每个sheet代表一个项目分类）
            for sheet_name in xls.sheet_names:
                try:
                    df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                    projects = self._parse_sheet(df, sheet_name)
                    all_projects.extend(projects)
                except Exception as e:
                    logger.warning(f"解析Sheet '{sheet_name}' 失败: {str(e)}")
                    continue
            
            return {
                'projects': all_projects,
                'total_count': len(all_projects),
                'source_file': Path(file_path).name
            }
        except Exception as e:
            logger.error(f"Excel解析失败: {str(e)}", exc_info=True)
            raise ValueError(f"Excel解析失败: {str(e)}")
    
    def _parse_sheet(self, df: pd.DataFrame, sheet_name: str) -> List[Dict[str, Any]]:
        """解析单个Sheet"""
        projects = []
        
        # 查找表头行（包含"项目名称"的行）
        header_row = None
        for idx, row in df.iterrows():
            if row.notna().any() and '项目名称' in str(row.values):
                header_row = idx
                break
        
        if header_row is None:
            logger.warning(f"Sheet '{sheet_name}' 未找到表头行")
            return projects
        
        # 从表头行开始解析
        data_start_row = header_row + 2  # 跳过表头和月份行
        
        # 解析每一行项目数据
        for idx in range(data_start_row, len(df)):
            row = df.iloc[idx]
            
            # 检查是否是项目行（项目名称不为空）
            project_name = self._get_cell_value(row, 1)  # 第2列是项目名称
            if not project_name or pd.isna(project_name) or str(project_name).strip() == '':
                continue
            
            try:
                project_data = self._parse_project_row(df, idx, header_row, sheet_name)
                if project_data:
                    projects.append(project_data)
            except Exception as e:
                logger.warning(f"解析第 {idx+1} 行项目数据失败: {str(e)}")
                continue
        
        return projects
    
    def _parse_project_row(self, df: pd.DataFrame, row_idx: int, header_row: int, sheet_name: str) -> Optional[Dict[str, Any]]:
        """解析单个项目行"""
        row = df.iloc[row_idx]
        
        # 提取基本信息
        project_name = self._get_cell_value(row, 1)
        reporter = self._get_cell_value(row, 2)
        project_status = self._get_cell_value(row, 3)
        project_phase = self._get_cell_value(row, 4)
        todo_hint = self._get_cell_value(row, 5)
        
        # 生成项目编码
        project_code = self._generate_project_code(project_name, sheet_name)
        
        # 提取周报数据
        weekly_reports = self._extract_weekly_reports(df, row_idx, header_row)
        
        # 提取里程碑
        milestones = self._extract_milestones(row)
        
        # 提取任务（从周报中提取）
        tasks = self._extract_tasks_from_reports(weekly_reports)
        
        return {
            'project_code': project_code,
            'name': str(project_name).strip(),
            'description': f"来自Sheet: {sheet_name}",
            'reporter': str(reporter).strip() if reporter else None,
            'status': self._normalize_status(str(project_status).strip() if project_status else 'planning'),
            'phase': str(project_phase).strip() if project_phase else None,
            'todo_hint': str(todo_hint).strip() if todo_hint else None,
            'weekly_reports': weekly_reports,
            'milestones': milestones,
            'tasks': tasks,
            'metadata': {
                'source_sheet': sheet_name,
                'source_row': row_idx + 1
            }
        }
    
    def _extract_weekly_reports(self, df: pd.DataFrame, row_idx: int, header_row: int) -> List[Dict[str, Any]]:
        """提取周报数据"""
        reports = []
        row = df.iloc[row_idx]
        header_row_data = df.iloc[header_row]
        
        # 查找"计划"和"成果"列的位置
        plan_col = None
        achievement_col = None
        
        for col_idx in range(len(header_row_data)):
            cell_value = str(header_row_data.iloc[col_idx]).strip()
            if '计划' in cell_value or 'plan' in cell_value.lower():
                plan_col = col_idx
            if '成果' in cell_value or 'achievement' in cell_value.lower():
                achievement_col = col_idx
        
        # 从第6列开始查找周数据（跳过基本信息列）
        current_date = None
        current_week = None
        
        for col_idx in range(6, len(row)):
            cell_value = self._get_cell_value(row, col_idx)
            header_value = self._get_cell_value(header_row_data, col_idx)
            
            if not cell_value or pd.isna(cell_value):
                continue
            
            # 检查是否是日期列（周标题）
            date_match = self._parse_week_date(str(header_value))
            if date_match:
                current_date = date_match['date']
                current_week = date_match['week']
                continue
            
            # 如果是计划或成果内容
            content = str(cell_value).strip()
            if content and content != 'nan':
                # 判断是计划还是成果
                is_plan = (plan_col and col_idx == plan_col) or '计划' in str(header_value)
                is_achievement = (achievement_col and col_idx == achievement_col) or '成果' in str(header_value)
                
                if current_date:
                    # 查找或创建对应的周报
                    report = next((r for r in reports if r['report_date'] == current_date), None)
                    if not report:
                        report = {
                            'report_date': current_date,
                            'week_number': current_week,
                            'content_plan': '',
                            'content_achievement': '',
                            'key_tasks_completed': [],
                            'issues_risks': '',
                            'next_week_plan': ''
                        }
                        reports.append(report)
                    
                    if is_plan:
                        report['content_plan'] = content
                    elif is_achievement:
                        report['content_achievement'] = content
                        # 从成果中提取关键任务
                        report['key_tasks_completed'] = self._extract_tasks_from_text(content)
        
        return reports
    
    def _extract_milestones(self, row: pd.Series) -> List[Dict[str, Any]]:
        """提取里程碑"""
        milestones = []
        
        # 查找里程碑列（通常在最后几列）
        for col_idx in range(len(row) - 5, len(row)):
            cell_value = self._get_cell_value(row, col_idx)
            if cell_value and not pd.isna(cell_value):
                value_str = str(cell_value).strip()
                # 尝试解析日期
                date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', value_str)
                if date_match:
                    try:
                        milestone_date = datetime.strptime(date_match.group(1).replace('/', '-'), '%Y-%m-%d').date()
                        milestones.append({
                            'name': value_str,
                            'due_date': milestone_date.isoformat(),
                            'milestone_type': 'delivery',
                            'is_critical': True
                        })
                    except:
                        pass
        
        return milestones
    
    def _extract_tasks_from_reports(self, reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从周报中提取任务"""
        tasks = []
        task_counter = 1
        
        for report in reports:
            # 从成果中提取任务
            if report.get('content_achievement'):
                task_texts = self._extract_tasks_from_text(report['content_achievement'])
                for task_text in task_texts:
                    tasks.append({
                        'task_code': f'T{task_counter:03d}',
                        'title': task_text[:200],  # 限制长度
                        'description': task_text,
                        'status': 'completed',
                        'completed_date': report.get('report_date')
                    })
                    task_counter += 1
        
        return tasks
    
    def _extract_tasks_from_text(self, text: str) -> List[str]:
        """从文本中提取任务列表"""
        tasks = []
        # 按数字编号或换行符分割
        lines = re.split(r'\n+|\d+[、.]', text)
        for line in lines:
            line = line.strip()
            if line and len(line) > 5:  # 过滤太短的行
                tasks.append(line)
        return tasks[:10]  # 最多返回10个任务
    
    def _parse_week_date(self, text: str) -> Optional[Dict[str, Any]]:
        """解析周日期"""
        if not text or text == 'nan':
            return None
        
        # 匹配格式：第一周（12/02-12/06）或 12/02-12/06
        patterns = [
            r'第(\d+)周[（(](\d{1,2})[/-](\d{1,2})[-~](\d{1,2})[/-](\d{1,2})[）)]',
            r'(\d{1,2})[/-](\d{1,2})[-~](\d{1,2})[/-](\d{1,2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if len(match.groups()) == 5:
                        week_num = int(match.group(1))
                        month1, day1 = int(match.group(2)), int(match.group(3))
                        month2, day2 = int(match.group(4)), int(match.group(5))
                    else:
                        week_num = None
                        month1, day1 = int(match.group(1)), int(match.group(2))
                        month2, day2 = int(match.group(3)), int(match.group(4))
                    
                    # 使用当前年份
                    current_year = datetime.now().year
                    start_date = date(current_year, month1, day1)
                    
                    return {
                        'date': start_date.isoformat(),
                        'week': week_num
                    }
                except:
                    pass
        
        return None
    
    def _get_cell_value(self, row: pd.Series, col_idx: int) -> Any:
        """安全获取单元格值"""
        if col_idx >= len(row):
            return None
        value = row.iloc[col_idx]
        if pd.isna(value):
            return None
        return value
    
    def _generate_project_code(self, project_name: str, sheet_name: str) -> str:
        """生成项目编码"""
        # 使用Sheet名称前缀 + 项目名称首字母
        sheet_prefix = ''.join([c for c in sheet_name[:2] if c.isalnum()]).upper()
        name_prefix = ''.join([c for c in project_name[:3] if c.isalnum()]).upper()
        timestamp = datetime.now().strftime('%Y%m')
        return f"{sheet_prefix}{name_prefix}{timestamp}"
    
    def _normalize_status(self, status: str) -> str:
        """标准化项目状态"""
        status_lower = status.lower()
        if '正常' in status or 'active' in status_lower or '进行' in status:
            return 'active'
        elif '延迟' in status or 'delayed' in status_lower:
            return 'delayed'
        elif '完成' in status or 'completed' in status_lower:
            return 'completed'
        elif '取消' in status or 'cancelled' in status_lower:
            return 'cancelled'
        else:
            return 'planning'

