#!/usr/bin/env python3
"""
根据Excel文件更新项目信息：匹配填报人并更新基础数据分类
"""
import sys
import os
import pandas as pd
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'auth-service' / 'src'))
sys.path.insert(0, str(project_root / 'database' / 'src'))
sys.path.insert(0, str(project_root / 'project-management' / 'src'))

from sqlalchemy.orm import Session
from database.src.core.session import get_session
from database.src.models.user_models import User
from database.src.models.project_models import Project
from database.src.models.basic_data_models import BasicDataCategory, ProjectBasicDataMapping
from uuid import UUID

EXCEL_FILE = "/tmp/2025项目周月进度报告.xlsx"

def read_excel_data(excel_file: str):
    """读取Excel文件数据"""
    try:
        # 读取Excel，跳过第一行，使用第二行作为表头
        df = pd.read_excel(excel_file, sheet_name=0, header=1)
        
        # 识别关键列
        project_name_col = None
        reporter_col = None
        
        for col in df.columns:
            col_str = str(col)
            if '项目名称' in col_str:
                project_name_col = col
            elif '填报人' in col_str:
                reporter_col = col
        
        if not project_name_col:
            print("Error: Cannot find project name column")
            print(f"Available columns: {list(df.columns)[:10]}")
            return []
        
        print(f"Using project name column: {project_name_col}")
        if reporter_col:
            print(f"Using reporter column: {reporter_col}")
        
        # 提取项目数据
        projects_data = []
        for idx, row in df.iterrows():
            project_name_val = row[project_name_col]
            
            # 跳过空值
            if pd.isna(project_name_val):
                continue
            
            project_name = str(project_name_val).strip()
            
            # 处理换行符（Excel中可能有\n）
            project_name = project_name.replace('\n', ' ').replace('\r', ' ')
            
            # 跳过无效值
            if not project_name or project_name == 'nan' or project_name.lower() == 'none':
                continue
            
            # 跳过表头行（如果项目名称列的值看起来像表头）
            if project_name in ['项目名称', '项目', 'Unnamed: 0']:
                continue
            
            reporter_name = ""
            if reporter_col and pd.notna(row[reporter_col]):
                reporter_name = str(row[reporter_col]).strip()
            
            # 处理填报人（可能包含多个，用/分隔）
            reporters = []
            if reporter_name and reporter_name != 'nan' and reporter_name.lower() != 'none':
                # 分割多个填报人
                for r in reporter_name.split('/'):
                    r = r.strip()
                    if r:
                        reporters.append(r)
            
            projects_data.append({
                'project_name': project_name,
                'reporters': reporters,
                'row_data': row.to_dict()
            })
        
        return projects_data
    except Exception as e:
        print(f"Error reading Excel: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def find_user_by_name(db: Session, name: str):
    """根据姓名查找用户"""
    # 精确匹配
    user = db.query(User).filter(User.full_name == name).first()
    if user:
        return user
    
    # 模糊匹配（包含关系）
    users = db.query(User).filter(User.full_name.ilike(f"%{name}%")).all()
    if len(users) == 1:
        return users[0]
    
    return None

def update_project_reporter(db: Session, project: Project, reporter_names: list):
    """更新项目的填报人"""
    if not reporter_names:
        return None
    
    # 尝试匹配第一个填报人
    reporter = None
    for name in reporter_names:
        user = find_user_by_name(db, name)
        if user:
            reporter = user
            break
    
    if reporter:
        project.reporter_id = reporter.id
        print(f"  Matched reporter: {reporter.full_name} ({reporter.username})")
        return reporter
    else:
        print(f"  Warning: Reporter not found: {', '.join(reporter_names)}")
        return None

def identify_category_columns(df):
    """识别Excel中的分类列"""
    category_keywords = ['分类', '类型', '行业', '领域', 'category', 'type', 'industry', 'domain', '项目状态', '项目阶段']
    category_cols = []
    
    for col in df.columns:
        col_str = str(col)
        # 跳过Unnamed列
        if 'Unnamed' in col_str:
            continue
            
        for keyword in category_keywords:
            if keyword in col_str:
                category_cols.append({
                    'column': col,
                    'name': col_str,
                    'keyword': keyword
                })
                break
    
    return category_cols

def get_or_create_category(db: Session, category_type: str, code: str, name: str):
    """获取或创建基础数据分类"""
    category = db.query(BasicDataCategory).filter(
        BasicDataCategory.category_type == category_type,
        BasicDataCategory.code == code
    ).first()
    
    if not category:
        category = BasicDataCategory(
            category_type=category_type,
            code=code,
            name=name,
            is_active=True
        )
        db.add(category)
        db.flush()
        print(f"  Created category: {category_type}/{code} - {name}")
    
    return category

def update_project_categories(db: Session, project: Project, row_data: dict, category_cols: list):
    """更新项目的基础数据分类"""
    updated_count = 0
    
    for cat_info in category_cols:
        col = cat_info['column']
        col_name = cat_info['name']
        
        if col not in row_data:
            continue
        
        value = row_data[col]
        if pd.isna(value) or str(value).strip() == '':
            continue
        
        value_str = str(value).strip()
        
        # 根据列名确定分类类型
        if '项目状态' in col_name or '状态' in col_name:
            category_type = 'project_status'
        elif '项目阶段' in col_name or '阶段' in col_name:
            category_type = 'project_phase'
        elif '行业' in col_name:
            category_type = 'industry'
        elif '领域' in col_name:
            category_type = 'domain'
        elif '类型' in col_name:
            category_type = 'project_type'
        else:
            # 默认使用列名作为分类类型
            category_type = col_name.lower().replace(' ', '_').replace('项目', 'project')
        
        # 创建或获取分类
        # 清理code，移除特殊字符
        code = value_str.lower().replace(' ', '_').replace('/', '_').replace('\\', '_')
        code = ''.join(c for c in code if c.isalnum() or c == '_')
        if not code:
            code = 'unknown'
        
        category = get_or_create_category(db, category_type, code, value_str)
        
        # 检查是否已关联
        existing = db.query(ProjectBasicDataMapping).filter(
            ProjectBasicDataMapping.project_id == project.id,
            ProjectBasicDataMapping.category_id == category.id
        ).first()
        
        if not existing:
            mapping = ProjectBasicDataMapping(
                project_id=project.id,
                category_id=category.id
            )
            db.add(mapping)
            updated_count += 1
            print(f"  Linked category: {category_type}/{value_str}")
    
    return updated_count

def main():
    """主函数"""
    print("=" * 80)
    print("根据Excel更新项目信息")
    print("=" * 80)
    print("")
    
    # 读取Excel数据
    print(f"Reading Excel file: {EXCEL_FILE}")
    projects_data = read_excel_data(EXCEL_FILE)
    
    if not projects_data:
        print("Error: No project data found")
        sys.exit(1)
    
        print(f"Success: Read {len(projects_data)} projects")
    print("")
    
    # 初始化会话工厂（如果需要）
    try:
        from database.src.core.session import init_session_factory
        init_session_factory()
    except:
        pass
    
    # 识别分类列（使用第一个项目的数据）
    if projects_data:
        sample_df = pd.read_excel(EXCEL_FILE, sheet_name=0, header=1)
        category_cols = identify_category_columns(sample_df)
        print(f"Identified {len(category_cols)} category columns:")
        for cat in category_cols:
            print(f"  - {cat['name']}")
        print("")
    
    # 使用上下文管理器获取数据库会话
    try:
        with get_session() as db:
            # 统计
            updated_reporter_count = 0
            updated_category_count = 0
            not_found_count = 0
            
            # 处理每个项目
            print("=" * 80)
            print("开始更新项目信息")
            print("=" * 80)
            print("")
            
            for idx, proj_data in enumerate(projects_data, 1):
                project_name = proj_data['project_name']
                print(f"[{idx}/{len(projects_data)}] Processing project: {project_name}")
                
                # 查找项目（精确匹配或模糊匹配）
                project = db.query(Project).filter(Project.name == project_name).first()
                
                if not project:
                    # 尝试模糊匹配（包含关系）
                    project = db.query(Project).filter(Project.name.ilike(f"%{project_name}%")).first()
                
                if not project:
                    # 尝试反向匹配（项目名称包含Excel中的名称）
                    project = db.query(Project).filter(Project.name.ilike(f"%{project_name.split(chr(10))[0]}%")).first()  # 处理换行符
                
                if not project:
                    print(f"  Warning: Project not found: {project_name}")
                    not_found_count += 1
                    continue
                
                print(f"  Found project: {project.name}")
                
                # 更新填报人
                if proj_data['reporters']:
                    reporter = update_project_reporter(db, project, proj_data['reporters'])
                    if reporter:
                        updated_reporter_count += 1
                
                # 更新分类
                if category_cols:
                    cat_count = update_project_categories(db, project, proj_data['row_data'], category_cols)
                    updated_category_count += cat_count
                
                print("")
            
            print("=" * 80)
            print("Update Statistics")
            print("=" * 80)
            print(f"Updated reporter: {updated_reporter_count} projects")
            print(f"Updated categories: {updated_category_count} mappings")
            print(f"Projects not found: {not_found_count}")
            print("")
            
    except Exception as e:
        print(f"Error: Update failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("=" * 80)
    print("完成！")
    print("=" * 80)

if __name__ == "__main__":
    main()

