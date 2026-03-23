#!/usr/bin/env python3
"""
验证基础数据分类
"""
import sys
from pathlib import Path

project_root = Path('/app')
sys.path.insert(0, str(project_root.parent / 'database' / 'src'))
sys.path.insert(0, str(project_root.parent / 'project-management' / 'src'))

from database.src.core.session import get_session, init_session_factory
from database.src.models.project_models import Project
from database.src.models.basic_data_models import BasicDataCategory

init_session_factory()

with get_session() as db:
    print("=" * 80)
    print("项目阶段 (project_phase)")
    print("=" * 80)
    phases = db.query(BasicDataCategory).filter(
        BasicDataCategory.category_type == "project_phase"
    ).order_by(BasicDataCategory.sort_order, BasicDataCategory.code).all()
    
    for phase in phases:
        print(f"  {phase.code}: {phase.name} (排序: {phase.sort_order})")
    
    print("")
    print("=" * 80)
    print("阶段状态 (phase_status)")
    print("=" * 80)
    statuses = db.query(BasicDataCategory).filter(
        BasicDataCategory.category_type == "phase_status"
    ).order_by(BasicDataCategory.sort_order, BasicDataCategory.code).all()
    
    for status in statuses:
        print(f"  {status.code}: {status.name} (排序: {status.sort_order})")
    
    print("")
    print("=" * 80)
    print("完成")
    print("=" * 80)


