#!/usr/bin/env python3
"""
初始化权限和角色数据脚本
用于在数据库中创建默认的权限和角色
根据整个平台的功能模块，生成详细完整的权限列表
"""

import sys
import os

# 添加auth-service的src目录到Python路径
auth_service_path = os.path.join(os.path.dirname(__file__), 'auth-service', 'src')
sys.path.insert(0, auth_service_path)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量获取数据库URL
def get_db_url():
    """获取数据库连接URL"""
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'ai_platform')
    db_user = os.getenv('DB_USER', 'ai_user')
    db_password = os.getenv('DB_PASSWORD', 'ai_password')
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# 详细完整的权限列表 - 根据平台所有功能模块生成
DEFAULT_PERMISSIONS = [
    # ==================== 用户管理权限 ====================
    {'code': 'user:read', 'name': '查看用户', 'resource': 'user', 'action': 'read', 'description': '查看用户信息'},
    {'code': 'user:create', 'name': '创建用户', 'resource': 'user', 'action': 'create', 'description': '创建新用户'},
    {'code': 'user:update', 'name': '更新用户', 'resource': 'user', 'action': 'update', 'description': '更新用户信息'},
    {'code': 'user:delete', 'name': '删除用户', 'resource': 'user', 'action': 'delete', 'description': '删除用户'},
    {'code': 'user:manage', 'name': '管理用户', 'resource': 'user', 'action': 'admin', 'description': '用户管理权限'},
    
    # ==================== 角色管理权限 ====================
    {'code': 'role:read', 'name': '查看角色', 'resource': 'role', 'action': 'read', 'description': '查看角色信息'},
    {'code': 'role:create', 'name': '创建角色', 'resource': 'role', 'action': 'create', 'description': '创建新角色'},
    {'code': 'role:update', 'name': '更新角色', 'resource': 'role', 'action': 'update', 'description': '更新角色信息'},
    {'code': 'role:delete', 'name': '删除角色', 'resource': 'role', 'action': 'delete', 'description': '删除角色'},
    {'code': 'role:manage', 'name': '管理角色', 'resource': 'role', 'action': 'admin', 'description': '角色管理权限'},
    
    # ==================== 权限管理权限 ====================
    {'code': 'permission:read', 'name': '查看权限', 'resource': 'permission', 'action': 'read', 'description': '查看权限信息'},
    {'code': 'permission:create', 'name': '创建权限', 'resource': 'permission', 'action': 'create', 'description': '创建新权限'},
    {'code': 'permission:update', 'name': '更新权限', 'resource': 'permission', 'action': 'update', 'description': '更新权限信息'},
    {'code': 'permission:delete', 'name': '删除权限', 'resource': 'permission', 'action': 'delete', 'description': '删除权限'},
    {'code': 'permission:manage', 'name': '管理权限', 'resource': 'permission', 'action': 'admin', 'description': '权限管理权限'},
    
    # ==================== 菜单权限管理 ====================
    {'code': 'menu:read', 'name': '查看菜单', 'resource': 'menu', 'action': 'read', 'description': '查看菜单权限配置'},
    {'code': 'menu:update', 'name': '更新菜单', 'resource': 'menu', 'action': 'update', 'description': '更新菜单权限配置'},
    {'code': 'menu:manage', 'name': '管理菜单', 'resource': 'menu', 'action': 'admin', 'description': '菜单权限管理'},
    
    # ==================== 项目管理权限 ====================
    {'code': 'project:read', 'name': '查看项目', 'resource': 'project', 'action': 'read', 'description': '查看项目信息'},
    {'code': 'project:create', 'name': '创建项目', 'resource': 'project', 'action': 'create', 'description': '创建新项目'},
    {'code': 'project:update', 'name': '更新项目', 'resource': 'project', 'action': 'update', 'description': '更新项目信息'},
    {'code': 'project:delete', 'name': '删除项目', 'resource': 'project', 'action': 'delete', 'description': '删除项目'},
    {'code': 'project:import', 'name': '导入项目', 'resource': 'project', 'action': 'execute', 'description': '批量导入项目'},
    {'code': 'project:export', 'name': '导出项目', 'resource': 'project', 'action': 'execute', 'description': '导出项目数据'},
    {'code': 'project:dashboard', 'name': '项目仪表盘', 'resource': 'project', 'action': 'read', 'description': '查看项目仪表盘'},
    
    # ==================== 项目任务权限 ====================
    {'code': 'project_task:read', 'name': '查看任务', 'resource': 'project_task', 'action': 'read', 'description': '查看项目任务'},
    {'code': 'project_task:create', 'name': '创建任务', 'resource': 'project_task', 'action': 'create', 'description': '创建项目任务'},
    {'code': 'project_task:update', 'name': '更新任务', 'resource': 'project_task', 'action': 'update', 'description': '更新项目任务'},
    {'code': 'project_task:delete', 'name': '删除任务', 'resource': 'project_task', 'action': 'delete', 'description': '删除项目任务'},
    {'code': 'project_task:assign', 'name': '分配任务', 'resource': 'project_task', 'action': 'execute', 'description': '分配任务给成员'},
    
    # ==================== 项目里程碑权限 ====================
    {'code': 'milestone:read', 'name': '查看里程碑', 'resource': 'milestone', 'action': 'read', 'description': '查看项目里程碑'},
    {'code': 'milestone:create', 'name': '创建里程碑', 'resource': 'milestone', 'action': 'create', 'description': '创建项目里程碑'},
    {'code': 'milestone:update', 'name': '更新里程碑', 'resource': 'milestone', 'action': 'update', 'description': '更新项目里程碑'},
    {'code': 'milestone:delete', 'name': '删除里程碑', 'resource': 'milestone', 'action': 'delete', 'description': '删除项目里程碑'},
    
    # ==================== 项目阶段权限 ====================
    {'code': 'project_phase:read', 'name': '查看项目阶段', 'resource': 'project_phase', 'action': 'read', 'description': '查看项目阶段信息'},
    {'code': 'project_phase:create', 'name': '创建项目阶段', 'resource': 'project_phase', 'action': 'create', 'description': '创建项目阶段'},
    {'code': 'project_phase:update', 'name': '更新项目阶段', 'resource': 'project_phase', 'action': 'update', 'description': '更新项目阶段'},
    {'code': 'project_phase:delete', 'name': '删除项目阶段', 'resource': 'project_phase', 'action': 'delete', 'description': '删除项目阶段'},
    
    # ==================== 周报管理权限 ====================
    {'code': 'weekly_report:read', 'name': '查看周报', 'resource': 'weekly_report', 'action': 'read', 'description': '查看项目周报'},
    {'code': 'weekly_report:create', 'name': '创建周报', 'resource': 'weekly_report', 'action': 'create', 'description': '创建项目周报'},
    {'code': 'weekly_report:update', 'name': '更新周报', 'resource': 'weekly_report', 'action': 'update', 'description': '更新项目周报'},
    {'code': 'weekly_report:delete', 'name': '删除周报', 'resource': 'weekly_report', 'action': 'delete', 'description': '删除项目周报'},
    {'code': 'weekly_report:export', 'name': '导出周报', 'resource': 'weekly_report', 'action': 'execute', 'description': '导出周报数据'},
    
    # ==================== 月报管理权限 ====================
    {'code': 'monthly_report:read', 'name': '查看月报', 'resource': 'monthly_report', 'action': 'read', 'description': '查看项目月报'},
    {'code': 'monthly_report:create', 'name': '创建月报', 'resource': 'monthly_report', 'action': 'create', 'description': '创建项目月报'},
    {'code': 'monthly_report:update', 'name': '更新月报', 'resource': 'monthly_report', 'action': 'update', 'description': '更新项目月报'},
    {'code': 'monthly_report:delete', 'name': '删除月报', 'resource': 'monthly_report', 'action': 'delete', 'description': '删除项目月报'},
    {'code': 'monthly_report:export', 'name': '导出月报', 'resource': 'monthly_report', 'action': 'execute', 'description': '导出月报数据'},
    
    # ==================== 进度报告权限 ====================
    {'code': 'progress_report:read', 'name': '查看进度报告', 'resource': 'progress_report', 'action': 'read', 'description': '查看项目进度报告'},
    {'code': 'progress_report:create', 'name': '创建进度报告', 'resource': 'progress_report', 'action': 'create', 'description': '创建项目进度报告'},
    {'code': 'progress_report:update', 'name': '更新进度报告', 'resource': 'progress_report', 'action': 'update', 'description': '更新项目进度报告'},
    {'code': 'progress_report:export', 'name': '导出进度报告', 'resource': 'progress_report', 'action': 'execute', 'description': '导出进度报告'},
    
    # ==================== 风险管理权限 ====================
    {'code': 'risk:read', 'name': '查看风险', 'resource': 'risk', 'action': 'read', 'description': '查看项目风险'},
    {'code': 'risk:create', 'name': '创建风险', 'resource': 'risk', 'action': 'create', 'description': '创建项目风险'},
    {'code': 'risk:update', 'name': '更新风险', 'resource': 'risk', 'action': 'update', 'description': '更新项目风险'},
    {'code': 'risk:delete', 'name': '删除风险', 'resource': 'risk', 'action': 'delete', 'description': '删除项目风险'},
    
    # ==================== 待办事项权限 ====================
    {'code': 'todo:read', 'name': '查看待办', 'resource': 'todo', 'action': 'read', 'description': '查看待办事项'},
    {'code': 'todo:create', 'name': '创建待办', 'resource': 'todo', 'action': 'create', 'description': '创建待办事项'},
    {'code': 'todo:update', 'name': '更新待办', 'resource': 'todo', 'action': 'update', 'description': '更新待办事项'},
    {'code': 'todo:delete', 'name': '删除待办', 'resource': 'todo', 'action': 'delete', 'description': '删除待办事项'},
    {'code': 'todo:complete', 'name': '完成待办', 'resource': 'todo', 'action': 'execute', 'description': '标记待办为已完成'},
    {'code': 'todo:assign', 'name': '分配待办', 'resource': 'todo', 'action': 'execute', 'description': '分配待办给其他用户'},
    
    # ==================== 基础数据权限 ====================
    {'code': 'basic_data:read', 'name': '查看基础数据', 'resource': 'basic_data', 'action': 'read', 'description': '查看基础数据分类'},
    {'code': 'basic_data:create', 'name': '创建基础数据', 'resource': 'basic_data', 'action': 'create', 'description': '创建基础数据分类'},
    {'code': 'basic_data:update', 'name': '更新基础数据', 'resource': 'basic_data', 'action': 'update', 'description': '更新基础数据分类'},
    {'code': 'basic_data:delete', 'name': '删除基础数据', 'resource': 'basic_data', 'action': 'delete', 'description': '删除基础数据分类'},
    
    # ==================== 项目成员权限 ====================
    {'code': 'project_member:read', 'name': '查看项目成员', 'resource': 'project_member', 'action': 'read', 'description': '查看项目成员列表'},
    {'code': 'project_member:create', 'name': '添加项目成员', 'resource': 'project_member', 'action': 'create', 'description': '添加项目成员'},
    {'code': 'project_member:update', 'name': '更新项目成员', 'resource': 'project_member', 'action': 'update', 'description': '更新项目成员角色'},
    {'code': 'project_member:delete', 'name': '移除项目成员', 'resource': 'project_member', 'action': 'delete', 'description': '移除项目成员'},
    
    # ==================== AI助手权限 ====================
    {'code': 'chat:read', 'name': '查看对话', 'resource': 'chat', 'action': 'read', 'description': '查看AI助手对话历史'},
    {'code': 'chat:create', 'name': '创建对话', 'resource': 'chat', 'action': 'create', 'description': '创建新的AI助手对话'},
    {'code': 'chat:execute', 'name': '执行对话', 'resource': 'chat', 'action': 'execute', 'description': '与AI助手进行对话'},
    {'code': 'chat:delete', 'name': '删除对话', 'resource': 'chat', 'action': 'delete', 'description': '删除对话历史'},
    
    # ==================== 智能体权限 ====================
    {'code': 'agent:read', 'name': '查看智能体', 'resource': 'agent', 'action': 'read', 'description': '查看智能体信息'},
    {'code': 'agent:create', 'name': '创建智能体', 'resource': 'agent', 'action': 'create', 'description': '创建新智能体'},
    {'code': 'agent:update', 'name': '更新智能体', 'resource': 'agent', 'action': 'update', 'description': '更新智能体配置'},
    {'code': 'agent:delete', 'name': '删除智能体', 'resource': 'agent', 'action': 'delete', 'description': '删除智能体'},
    {'code': 'agent:execute', 'name': '执行智能体', 'resource': 'agent', 'action': 'execute', 'description': '执行智能体任务'},
    
    # ==================== 知识库权限 ====================
    {'code': 'knowledge_base:read', 'name': '查看知识库', 'resource': 'knowledge_base', 'action': 'read', 'description': '查看知识库信息'},
    {'code': 'knowledge_base:create', 'name': '创建知识库', 'resource': 'knowledge_base', 'action': 'create', 'description': '创建新知识库'},
    {'code': 'knowledge_base:update', 'name': '更新知识库', 'resource': 'knowledge_base', 'action': 'update', 'description': '更新知识库信息'},
    {'code': 'knowledge_base:delete', 'name': '删除知识库', 'resource': 'knowledge_base', 'action': 'delete', 'description': '删除知识库'},
    {'code': 'knowledge_base:upload', 'name': '上传文档', 'resource': 'knowledge_base', 'action': 'execute', 'description': '向知识库上传文档'},
    {'code': 'knowledge_base:search', 'name': '搜索知识库', 'resource': 'knowledge_base', 'action': 'read', 'description': '搜索知识库内容'},
    
    # ==================== 知识图谱权限 ====================
    {'code': 'knowledge_graph:read', 'name': '查看知识图谱', 'resource': 'knowledge_graph', 'action': 'read', 'description': '查看知识图谱'},
    {'code': 'knowledge_graph:create', 'name': '创建知识图谱', 'resource': 'knowledge_graph', 'action': 'create', 'description': '创建知识图谱节点'},
    {'code': 'knowledge_graph:update', 'name': '更新知识图谱', 'resource': 'knowledge_graph', 'action': 'update', 'description': '更新知识图谱'},
    {'code': 'knowledge_graph:delete', 'name': '删除知识图谱', 'resource': 'knowledge_graph', 'action': 'delete', 'description': '删除知识图谱节点'},
    {'code': 'knowledge_graph:query', 'name': '查询知识图谱', 'resource': 'knowledge_graph', 'action': 'read', 'description': '查询知识图谱关系'},
    
    # ==================== 对话历史权限 ====================
    {'code': 'conversation:read', 'name': '查看对话历史', 'resource': 'conversation', 'action': 'read', 'description': '查看对话历史记录'},
    {'code': 'conversation:delete', 'name': '删除对话历史', 'resource': 'conversation', 'action': 'delete', 'description': '删除对话历史记录'},
    
    # ==================== 工作流权限 ====================
    {'code': 'workflow:read', 'name': '查看工作流', 'resource': 'workflow', 'action': 'read', 'description': '查看工作流信息'},
    {'code': 'workflow:create', 'name': '创建工作流', 'resource': 'workflow', 'action': 'create', 'description': '创建新工作流'},
    {'code': 'workflow:update', 'name': '更新工作流', 'resource': 'workflow', 'action': 'update', 'description': '更新工作流信息'},
    {'code': 'workflow:delete', 'name': '删除工作流', 'resource': 'workflow', 'action': 'delete', 'description': '删除工作流'},
    {'code': 'workflow:execute', 'name': '执行工作流', 'resource': 'workflow', 'action': 'execute', 'description': '执行工作流'},
    {'code': 'workflow:design', 'name': '设计工作流', 'resource': 'workflow', 'action': 'execute', 'description': '使用工作流设计器'},
    {'code': 'workflow:manage', 'name': '管理工作流', 'resource': 'workflow', 'action': 'admin', 'description': '工作流管理权限'},
    
    # ==================== 企业架构权限 ====================
    {'code': 'enterprise_architecture:read', 'name': '查看企业架构', 'resource': 'enterprise_architecture', 'action': 'read', 'description': '查看企业架构总览'},
    
    # 组织架构权限
    {'code': 'organization:read', 'name': '查看组织架构', 'resource': 'organization', 'action': 'read', 'description': '查看组织架构'},
    {'code': 'organization:create', 'name': '创建组织架构', 'resource': 'organization', 'action': 'create', 'description': '创建组织架构节点'},
    {'code': 'organization:update', 'name': '更新组织架构', 'resource': 'organization', 'action': 'update', 'description': '更新组织架构'},
    {'code': 'organization:delete', 'name': '删除组织架构', 'resource': 'organization', 'action': 'delete', 'description': '删除组织架构节点'},
    
    # 业务架构权限
    {'code': 'business_architecture:read', 'name': '查看业务架构', 'resource': 'business_architecture', 'action': 'read', 'description': '查看业务架构'},
    {'code': 'business_architecture:create', 'name': '创建业务架构', 'resource': 'business_architecture', 'action': 'create', 'description': '创建业务架构'},
    {'code': 'business_architecture:update', 'name': '更新业务架构', 'resource': 'business_architecture', 'action': 'update', 'description': '更新业务架构'},
    {'code': 'business_architecture:delete', 'name': '删除业务架构', 'resource': 'business_architecture', 'action': 'delete', 'description': '删除业务架构'},
    
    # 应用架构权限
    {'code': 'application_architecture:read', 'name': '查看应用架构', 'resource': 'application_architecture', 'action': 'read', 'description': '查看应用架构'},
    {'code': 'application_architecture:create', 'name': '创建应用架构', 'resource': 'application_architecture', 'action': 'create', 'description': '创建应用架构'},
    {'code': 'application_architecture:update', 'name': '更新应用架构', 'resource': 'application_architecture', 'action': 'update', 'description': '更新应用架构'},
    {'code': 'application_architecture:delete', 'name': '删除应用架构', 'resource': 'application_architecture', 'action': 'delete', 'description': '删除应用架构'},
    
    # 数据架构权限
    {'code': 'data_architecture:read', 'name': '查看数据架构', 'resource': 'data_architecture', 'action': 'read', 'description': '查看数据架构'},
    {'code': 'data_architecture:create', 'name': '创建数据架构', 'resource': 'data_architecture', 'action': 'create', 'description': '创建数据架构'},
    {'code': 'data_architecture:update', 'name': '更新数据架构', 'resource': 'data_architecture', 'action': 'update', 'description': '更新数据架构'},
    {'code': 'data_architecture:delete', 'name': '删除数据架构', 'resource': 'data_architecture', 'action': 'delete', 'description': '删除数据架构'},
    
    # 技术架构权限
    {'code': 'technology_architecture:read', 'name': '查看技术架构', 'resource': 'technology_architecture', 'action': 'read', 'description': '查看技术架构'},
    {'code': 'technology_architecture:create', 'name': '创建技术架构', 'resource': 'technology_architecture', 'action': 'create', 'description': '创建技术架构'},
    {'code': 'technology_architecture:update', 'name': '更新技术架构', 'resource': 'technology_architecture', 'action': 'update', 'description': '更新技术架构'},
    {'code': 'technology_architecture:delete', 'name': '删除技术架构', 'resource': 'technology_architecture', 'action': 'delete', 'description': '删除技术架构'},
    {'code': 'technology_instance:read', 'name': '查看技术实例', 'resource': 'technology_instance', 'action': 'read', 'description': '查看技术实例'},
    {'code': 'technology_instance:create', 'name': '创建技术实例', 'resource': 'technology_instance', 'action': 'create', 'description': '创建技术实例'},
    {'code': 'technology_instance:update', 'name': '更新技术实例', 'resource': 'technology_instance', 'action': 'update', 'description': '更新技术实例'},
    {'code': 'technology_instance:delete', 'name': '删除技术实例', 'resource': 'technology_instance', 'action': 'delete', 'description': '删除技术实例'},
    {'code': 'technology_standardization:read', 'name': '查看技术标准化', 'resource': 'technology_standardization', 'action': 'read', 'description': '查看技术标准化分析'},
    
    # 架构关系图权限
    {'code': 'architecture_relationship:read', 'name': '查看架构关系', 'resource': 'architecture_relationship', 'action': 'read', 'description': '查看架构关系图'},
    {'code': 'architecture_relationship:create', 'name': '创建架构关系', 'resource': 'architecture_relationship', 'action': 'create', 'description': '创建架构关系'},
    {'code': 'architecture_relationship:update', 'name': '更新架构关系', 'resource': 'architecture_relationship', 'action': 'update', 'description': '更新架构关系'},
    {'code': 'architecture_relationship:delete', 'name': '删除架构关系', 'resource': 'architecture_relationship', 'action': 'delete', 'description': '删除架构关系'},
    
    # ==================== 工具管理权限 ====================
    {'code': 'tool:read', 'name': '查看工具', 'resource': 'tool', 'action': 'read', 'description': '查看工具信息'},
    {'code': 'tool:create', 'name': '创建工具', 'resource': 'tool', 'action': 'create', 'description': '创建新工具'},
    {'code': 'tool:update', 'name': '更新工具', 'resource': 'tool', 'action': 'update', 'description': '更新工具信息'},
    {'code': 'tool:delete', 'name': '删除工具', 'resource': 'tool', 'action': 'delete', 'description': '删除工具'},
    {'code': 'tool:execute', 'name': '执行工具', 'resource': 'tool', 'action': 'execute', 'description': '执行工具'},
    {'code': 'tool:manage', 'name': '管理工具', 'resource': 'tool', 'action': 'admin', 'description': '工具管理权限'},
    
    # ==================== 提示词管理权限 ====================
    {'code': 'prompt:read', 'name': '查看提示词', 'resource': 'prompt', 'action': 'read', 'description': '查看提示词模板'},
    {'code': 'prompt:create', 'name': '创建提示词', 'resource': 'prompt', 'action': 'create', 'description': '创建提示词模板'},
    {'code': 'prompt:update', 'name': '更新提示词', 'resource': 'prompt', 'action': 'update', 'description': '更新提示词模板'},
    {'code': 'prompt:delete', 'name': '删除提示词', 'resource': 'prompt', 'action': 'delete', 'description': '删除提示词模板'},
    {'code': 'prompt:execute', 'name': '使用提示词', 'resource': 'prompt', 'action': 'execute', 'description': '使用提示词模板'},
    
    # ==================== 元数据管理权限 ====================
    {'code': 'metadata:read', 'name': '查看元数据', 'resource': 'metadata', 'action': 'read', 'description': '查看元数据信息'},
    {'code': 'metadata:create', 'name': '创建元数据', 'resource': 'metadata', 'action': 'create', 'description': '创建元数据'},
    {'code': 'metadata:update', 'name': '更新元数据', 'resource': 'metadata', 'action': 'update', 'description': '更新元数据'},
    {'code': 'metadata:delete', 'name': '删除元数据', 'resource': 'metadata', 'action': 'delete', 'description': '删除元数据'},
    {'code': 'metadata:manage', 'name': '管理元数据', 'resource': 'metadata', 'action': 'admin', 'description': '元数据管理权限'},
    
    # ==================== 系统监控权限 ====================
    {'code': 'monitoring:read', 'name': '查看监控', 'resource': 'monitoring', 'action': 'read', 'description': '查看系统监控信息'},
    {'code': 'monitoring:service', 'name': '服务监控', 'resource': 'monitoring', 'action': 'read', 'description': '查看服务监控'},
    {'code': 'monitoring:log', 'name': '日志查看', 'resource': 'monitoring', 'action': 'read', 'description': '查看系统日志'},
    {'code': 'monitoring:manage', 'name': '管理监控', 'resource': 'monitoring', 'action': 'admin', 'description': '系统监控管理权限'},
    
    # ==================== 数据库管理权限 ====================
    {'code': 'database:read', 'name': '查看数据库', 'resource': 'database', 'action': 'read', 'description': '查看数据库信息'},
    {'code': 'database:table', 'name': '表管理', 'resource': 'database', 'action': 'read', 'description': '查看数据库表'},
    {'code': 'database:performance', 'name': '性能监控', 'resource': 'database', 'action': 'read', 'description': '查看数据库性能'},
    {'code': 'database:backup', 'name': '备份管理', 'resource': 'database', 'action': 'execute', 'description': '数据库备份和恢复'},
    {'code': 'database:neo4j', 'name': 'Neo4j管理', 'resource': 'database', 'action': 'read', 'description': '查看Neo4j图数据库'},
    {'code': 'database:manage', 'name': '管理数据库', 'resource': 'database', 'action': 'admin', 'description': '数据库管理权限'},
    
    # ==================== 系统权限 ====================
    {'code': 'system:read', 'name': '查看系统', 'resource': 'system', 'action': 'read', 'description': '查看系统信息'},
    {'code': 'system:update', 'name': '更新系统', 'resource': 'system', 'action': 'update', 'description': '更新系统配置'},
    {'code': 'system:monitor', 'name': '监控系统', 'resource': 'system', 'action': 'monitor', 'description': '监控系统状态'},
    {'code': 'system:admin', 'name': '系统管理', 'resource': 'system', 'action': 'admin', 'description': '系统管理权限'},
    
    # ==================== 其他功能权限 ====================
    {'code': 'component:read', 'name': '查看组件', 'resource': 'component', 'action': 'read', 'description': '查看组件库'},
    {'code': 'help:read', 'name': '查看帮助', 'resource': 'help', 'action': 'read', 'description': '查看帮助中心'},
    {'code': 'announcement:read', 'name': '查看公告', 'resource': 'announcement', 'action': 'read', 'description': '查看系统公告'},
    {'code': 'announcement:create', 'name': '创建公告', 'resource': 'announcement', 'action': 'create', 'description': '创建系统公告'},
    {'code': 'announcement:update', 'name': '更新公告', 'resource': 'announcement', 'action': 'update', 'description': '更新系统公告'},
    {'code': 'announcement:delete', 'name': '删除公告', 'resource': 'announcement', 'action': 'delete', 'description': '删除系统公告'},
    {'code': 'dashboard:read', 'name': '查看仪表盘', 'resource': 'dashboard', 'action': 'read', 'description': '查看数据看板'},
]

# 默认角色列表
DEFAULT_ROLES = [
    {'code': 'admin', 'name': '超级管理员', 'description': '拥有所有权限的系统管理员', 'is_system': True},
    {'code': 'user', 'name': '普通用户', 'description': '普通用户角色，可以查看和使用基本功能', 'is_system': True},
    {'code': 'project_manager', 'name': '项目经理', 'description': '项目经理角色，可以管理项目相关功能', 'is_system': False},
    {'code': 'developer', 'name': '开发者', 'description': '开发者角色，可以管理工作流和工具', 'is_system': False},
    {'code': 'viewer', 'name': '查看者', 'description': '只读权限的查看者角色', 'is_system': False},
    {'code': 'architect', 'name': '架构师', 'description': '企业架构师角色，可以管理企业架构相关功能', 'is_system': False},
]

def init_permissions_and_roles():
    """初始化权限和角色数据"""
    try:
        # 获取数据库URL
        db_url = get_db_url()
        if not db_url:
            print("错误: 无法获取数据库URL，请检查环境变量配置")
            return False
        
        print(f"连接到数据库: {db_url.split('@')[1] if '@' in db_url else '***'}")
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # 创建权限
            print("\n开始创建权限...")
            permission_map = {}
            for perm_data in DEFAULT_PERMISSIONS:
                # 检查权限是否已存在
                existing = db.execute(
                    text("SELECT id FROM permissions WHERE code = :code"),
                    {"code": perm_data['code']}
                ).fetchone()
                
                if existing:
                    print(f"  权限 {perm_data['code']} 已存在，跳过")
                    permission_map[perm_data['code']] = existing[0]
                else:
                    perm_id = str(uuid.uuid4())
                    db.execute(
                        text("""
                            INSERT INTO permissions (id, code, name, resource, action, description, created_at, updated_at)
                            VALUES (:id, :code, :name, :resource, :action, :description, :created_at, :updated_at)
                        """),
                        {
                            "id": perm_id,
                            "code": perm_data['code'],
                            "name": perm_data['name'],
                            "resource": perm_data['resource'],
                            "action": perm_data['action'],
                            "description": perm_data['description'],
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow(),
                        }
                    )
                    permission_map[perm_data['code']] = perm_id
                    print(f"  ✓ 创建权限: {perm_data['code']} - {perm_data['name']}")
            
            db.commit()
            print(f"\n权限创建完成，共 {len(permission_map)} 个权限")
            
            # 创建角色
            print("\n开始创建角色...")
            role_map = {}
            for role_data in DEFAULT_ROLES:
                # 检查角色是否已存在
                existing = db.execute(
                    text("SELECT id FROM roles WHERE code = :code"),
                    {"code": role_data['code']}
                ).fetchone()
                
                if existing:
                    print(f"  角色 {role_data['code']} 已存在，跳过")
                    role_map[role_data['code']] = existing[0]
                else:
                    role_id = str(uuid.uuid4())
                    db.execute(
                        text("""
                            INSERT INTO roles (id, code, name, description, is_system, created_at, updated_at)
                            VALUES (:id, :code, :name, :description, :is_system, :created_at, :updated_at)
                        """),
                        {
                            "id": role_id,
                            "code": role_data['code'],
                            "name": role_data['name'],
                            "description": role_data['description'],
                            "is_system": role_data['is_system'],
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow(),
                        }
                    )
                    role_map[role_data['code']] = role_id
                    print(f"  ✓ 创建角色: {role_data['code']} - {role_data['name']}")
            
            db.commit()
            print(f"\n角色创建完成，共 {len(role_map)} 个角色")
            
            # 为角色分配权限
            print("\n开始为角色分配权限...")
            
            # 超级管理员拥有所有权限
            if 'admin' in role_map:
                admin_role_id = role_map['admin']
                for perm_code, perm_id in permission_map.items():
                    # 检查是否已存在
                    existing = db.execute(
                        text("SELECT 1 FROM role_permissions WHERE role_id = :role_id AND permission_id = :permission_id"),
                        {"role_id": admin_role_id, "permission_id": perm_id}
                    ).fetchone()
                    
                    if not existing:
                        db.execute(
                            text("INSERT INTO role_permissions (role_id, permission_id, created_at) VALUES (:role_id, :permission_id, :created_at)"),
                            {"role_id": admin_role_id, "permission_id": perm_id, "created_at": datetime.utcnow()}
                        )
                print(f"  ✓ 为超级管理员分配了所有权限 ({len(permission_map)} 个)")
            
            # 普通用户权限（基本查看和执行权限）
            if 'user' in role_map:
                user_role_id = role_map['user']
                user_permissions = [
                    # 基本查看权限
                    'user:read', 'project:read', 'project:dashboard',
                    'project_task:read', 'milestone:read', 'project_phase:read',
                    'weekly_report:read', 'monthly_report:read', 'progress_report:read',
                    'risk:read', 'todo:read', 'basic_data:read',
                    # AI功能
                    'chat:read', 'chat:create', 'chat:execute',
                    'agent:read', 'agent:execute',
                    'knowledge_base:read', 'knowledge_base:search',
                    'knowledge_graph:read', 'knowledge_graph:query',
                    'conversation:read',
                    # 工作流
                    'workflow:read', 'workflow:execute',
                    # 企业架构查看
                    'enterprise_architecture:read',
                    'organization:read', 'business_architecture:read',
                    'application_architecture:read', 'data_architecture:read',
                    'technology_architecture:read', 'technology_instance:read',
                    'technology_standardization:read', 'architecture_relationship:read',
                    # 工具
                    'tool:read', 'tool:execute',
                    # 其他
                    'component:read', 'help:read', 'announcement:read', 'dashboard:read',
                ]
                for perm_code in user_permissions:
                    if perm_code in permission_map:
                        perm_id = permission_map[perm_code]
                        existing = db.execute(
                            text("SELECT 1 FROM role_permissions WHERE role_id = :role_id AND permission_id = :permission_id"),
                            {"role_id": user_role_id, "permission_id": perm_id}
                        ).fetchone()
                        
                        if not existing:
                            db.execute(
                                text("INSERT INTO role_permissions (role_id, permission_id, created_at) VALUES (:role_id, :permission_id, :created_at)"),
                                {"role_id": user_role_id, "permission_id": perm_id, "created_at": datetime.utcnow()}
                            )
                print(f"  ✓ 为普通用户分配了基本权限")
            
            # 项目经理权限
            if 'project_manager' in role_map:
                project_manager_role_id = role_map['project_manager']
                project_manager_permissions = [
                    # 项目相关所有权限
                    'project:read', 'project:create', 'project:update', 'project:delete', 'project:import', 'project:export', 'project:dashboard',
                    'project_task:read', 'project_task:create', 'project_task:update', 'project_task:delete', 'project_task:assign',
                    'milestone:read', 'milestone:create', 'milestone:update', 'milestone:delete',
                    'project_phase:read', 'project_phase:create', 'project_phase:update', 'project_phase:delete',
                    'weekly_report:read', 'weekly_report:create', 'weekly_report:update', 'weekly_report:delete', 'weekly_report:export',
                    'monthly_report:read', 'monthly_report:create', 'monthly_report:update', 'monthly_report:delete', 'monthly_report:export',
                    'progress_report:read', 'progress_report:create', 'progress_report:update', 'progress_report:export',
                    'risk:read', 'risk:create', 'risk:update', 'risk:delete',
                    'todo:read', 'todo:create', 'todo:update', 'todo:delete', 'todo:complete', 'todo:assign',
                    'basic_data:read', 'basic_data:create', 'basic_data:update', 'basic_data:delete',
                    'project_member:read', 'project_member:create', 'project_member:update', 'project_member:delete',
                    # 基本查看权限
                    'user:read', 'chat:read', 'chat:create', 'chat:execute',
                    'knowledge_base:read', 'knowledge_base:search',
                    'workflow:read', 'workflow:execute',
                ]
                for perm_code in project_manager_permissions:
                    if perm_code in permission_map:
                        perm_id = permission_map[perm_code]
                        existing = db.execute(
                            text("SELECT 1 FROM role_permissions WHERE role_id = :role_id AND permission_id = :permission_id"),
                            {"role_id": project_manager_role_id, "permission_id": perm_id}
                        ).fetchone()
                        
                        if not existing:
                            db.execute(
                                text("INSERT INTO role_permissions (role_id, permission_id, created_at) VALUES (:role_id, :permission_id, :created_at)"),
                                {"role_id": project_manager_role_id, "permission_id": perm_id, "created_at": datetime.utcnow()}
                            )
                print(f"  ✓ 为项目经理分配了权限")
            
            # 开发者权限
            if 'developer' in role_map:
                developer_role_id = role_map['developer']
                developer_permissions = [
                    'user:read',
                    'workflow:read', 'workflow:create', 'workflow:update', 'workflow:execute', 'workflow:design',
                    'knowledge_base:read', 'knowledge_base:create', 'knowledge_base:update', 'knowledge_base:upload', 'knowledge_base:search',
                    'tool:read', 'tool:create', 'tool:update', 'tool:execute',
                    'agent:read', 'agent:create', 'agent:update', 'agent:execute',
                    'project:read', 'project:create', 'project:update',
                    'chat:read', 'chat:create', 'chat:execute',
                    'prompt:read', 'prompt:create', 'prompt:update', 'prompt:execute',
                ]
                for perm_code in developer_permissions:
                    if perm_code in permission_map:
                        perm_id = permission_map[perm_code]
                        existing = db.execute(
                            text("SELECT 1 FROM role_permissions WHERE role_id = :role_id AND permission_id = :permission_id"),
                            {"role_id": developer_role_id, "permission_id": perm_id}
                        ).fetchone()
                        
                        if not existing:
                            db.execute(
                                text("INSERT INTO role_permissions (role_id, permission_id, created_at) VALUES (:role_id, :permission_id, :created_at)"),
                                {"role_id": developer_role_id, "permission_id": perm_id, "created_at": datetime.utcnow()}
                            )
                print(f"  ✓ 为开发者分配了权限")
            
            # 架构师权限
            if 'architect' in role_map:
                architect_role_id = role_map['architect']
                architect_permissions = [
                    # 企业架构所有权限
                    'enterprise_architecture:read',
                    'organization:read', 'organization:create', 'organization:update', 'organization:delete',
                    'business_architecture:read', 'business_architecture:create', 'business_architecture:update', 'business_architecture:delete',
                    'application_architecture:read', 'application_architecture:create', 'application_architecture:update', 'application_architecture:delete',
                    'data_architecture:read', 'data_architecture:create', 'data_architecture:update', 'data_architecture:delete',
                    'technology_architecture:read', 'technology_architecture:create', 'technology_architecture:update', 'technology_architecture:delete',
                    'technology_instance:read', 'technology_instance:create', 'technology_instance:update', 'technology_instance:delete',
                    'technology_standardization:read',
                    'architecture_relationship:read', 'architecture_relationship:create', 'architecture_relationship:update', 'architecture_relationship:delete',
                    # 基本查看权限
                    'user:read', 'project:read',
                    'chat:read', 'chat:create', 'chat:execute',
                    'knowledge_base:read', 'knowledge_base:search',
                ]
                for perm_code in architect_permissions:
                    if perm_code in permission_map:
                        perm_id = permission_map[perm_code]
                        existing = db.execute(
                            text("SELECT 1 FROM role_permissions WHERE role_id = :role_id AND permission_id = :permission_id"),
                            {"role_id": architect_role_id, "permission_id": perm_id}
                        ).fetchone()
                        
                        if not existing:
                            db.execute(
                                text("INSERT INTO role_permissions (role_id, permission_id, created_at) VALUES (:role_id, :permission_id, :created_at)"),
                                {"role_id": architect_role_id, "permission_id": perm_id, "created_at": datetime.utcnow()}
                            )
                print(f"  ✓ 为架构师分配了权限")
            
            # 查看者权限（只读）
            if 'viewer' in role_map:
                viewer_role_id = role_map['viewer']
                for perm_code, perm_id in permission_map.items():
                    if perm_code.endswith(':read'):
                        existing = db.execute(
                            text("SELECT 1 FROM role_permissions WHERE role_id = :role_id AND permission_id = :permission_id"),
                            {"role_id": viewer_role_id, "permission_id": perm_id}
                        ).fetchone()
                        
                        if not existing:
                            db.execute(
                                text("INSERT INTO role_permissions (role_id, permission_id, created_at) VALUES (:role_id, :permission_id, :created_at)"),
                                {"role_id": viewer_role_id, "permission_id": perm_id, "created_at": datetime.utcnow()}
                            )
                print(f"  ✓ 为查看者分配了只读权限")
            
            db.commit()
            print("\n✓ 权限和角色初始化完成！")
            return True
            
        except Exception as e:
            db.rollback()
            print(f"\n错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            db.close()
            
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("权限和角色初始化脚本")
    print("=" * 60)
    
    success = init_permissions_and_roles()
    
    if success:
        print("\n✓ 初始化成功！")
        sys.exit(0)
    else:
        print("\n✗ 初始化失败！")
        sys.exit(1)
