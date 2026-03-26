#!/usr/bin/env python3
"""
从Excel文件导入基础数据到数据库
"""
import pandas as pd
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "database" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "project-management" / "src"))

from sqlalchemy.orm import Session
from database.src.core.session import get_db
from database.src.models.basic_data_models import BasicDataCategory

EXCEL_FILE = "2025项目周月进度报告.xlsx"
SHEET_NAME = "基础数据"

# 分类类型映射
CATEGORY_TYPE_MAPPING = {
    "行业线": "industry_line",
    "业务单元/业务元": "business_unit",
    "项目阶段": "project_phase",
    "阶段状态": "phase_status",
    "应用领域": "application_domain",
    "项目类型": "project_type",
    "项目负责人": "project_manager",
    "月份": "month",
}

def parse_code_name(value):
    """解析编码和名称，格式如：01-中间体"""
    if pd.isna(value) or value == "":
        return None, None
    
    value_str = str(value).strip()
    if "-" in value_str:
        parts = value_str.split("-", 1)
        code = parts[0].strip()
        name = parts[1].strip() if len(parts) > 1 else ""
        return code, name
    else:
        return None, value_str

def import_basic_data():
    """导入基础数据"""
    print("=" * 80)
    print("从Excel导入基础数据")
    print("=" * 80)
    
    # 读取Excel
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
        print(f"成功读取Excel文件，共 {len(df)} 行数据")
    except Exception as e:
        print(f"读取Excel文件失败: {e}")
        return
    
    # 获取数据库会话
    db: Session = next(get_db())
    
    try:
        total_imported = 0
        
        # 遍历每一列（除了项目负责人和月份）
        for col_name in df.columns:
            if col_name not in CATEGORY_TYPE_MAPPING:
                continue
            
            category_type = CATEGORY_TYPE_MAPPING[col_name]
            print(f"\n处理分类类型: {col_name} -> {category_type}")
            
            # 获取唯一值
            unique_values = df[col_name].dropna().unique()
            print(f"  找到 {len(unique_values)} 个唯一值")
            
            sort_order = 0
            for value in unique_values:
                if pd.isna(value) or str(value).strip() == "":
                    continue
                
                code, name = parse_code_name(value)
                
                # 如果没有编码，使用值作为编码和名称
                if code is None:
                    code = str(value).strip()
                    name = code
                
                # 检查是否已存在
                existing = db.query(BasicDataCategory).filter(
                    BasicDataCategory.category_type == category_type,
                    BasicDataCategory.code == code
                ).first()
                
                if existing:
                    print(f"  跳过已存在的: {code} - {name}")
                    continue
                
                # 创建分类
                category = BasicDataCategory(
                    category_type=category_type,
                    code=code,
                    name=name,
                    description=f"{col_name}分类",
                    sort_order=sort_order,
                    is_active=True
                )
                
                db.add(category)
                sort_order += 1
                total_imported += 1
                print(f"  ✓ 导入: {code} - {name}")
        
        # 提交
        db.commit()
        print(f"\n✅ 导入完成！共导入 {total_imported} 条基础数据")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    import_basic_data()

