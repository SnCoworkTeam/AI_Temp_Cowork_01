"""
采购场景数据采集脚本
用于采集和结构化采购场景的业务活动、实体和映射关系
"""
import json
import os
from datetime import datetime
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "procurement"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def create_procurement_activities():
    """创建采购场景的业务活动数据"""
    activities = [
        {
            "id": "activity:procurement:create_po",
            "name": "创建采购订单",
            "description": "在SAP系统中创建标准采购订单，包括选择供应商、物料、数量、价格等信息",
            "activity_type": "action",
            "business_domain": "procurement",
            "success_criteria": "PO号生成且状态为已保存",
            "prerequisites": ["供应商已存在", "物料主数据已维护", "价格信息已确认"],
            "estimated_time": "5分钟",
            "risk_level": "low",
            "owner_dept": "采购部",
            "source_type": "document",
            "source_id": "sap_mm_manual",
            "vector_entity_uri": "activity://procurement/activity:procurement:create_po",
            "embedding_version": "1.0"
        },
        {
            "id": "activity:procurement:query_po",
            "name": "查询采购订单",
            "description": "根据订单号、供应商、物料、日期等条件查询采购订单信息",
            "activity_type": "query",
            "business_domain": "procurement",
            "success_criteria": "返回符合条件的订单列表",
            "prerequisites": [],
            "estimated_time": "1分钟",
            "risk_level": "low",
            "owner_dept": "采购部",
            "source_type": "document",
            "source_id": "sap_mm_manual",
            "vector_entity_uri": "activity://procurement/activity:procurement:query_po",
            "embedding_version": "1.0"
        },
        {
            "id": "activity:procurement:approve_po",
            "name": "审批采购订单",
            "description": "对已创建的采购订单进行审批，包括金额审批、供应商资质审批等",
            "activity_type": "approval",
            "business_domain": "procurement",
            "success_criteria": "订单状态变为已审批",
            "prerequisites": ["订单已创建", "未审批"],
            "estimated_time": "3分钟",
            "risk_level": "medium",
            "owner_dept": "采购部",
            "source_type": "document",
            "source_id": "approval_workflow",
            "vector_entity_uri": "activity://procurement/activity:procurement:approve_po",
            "embedding_version": "1.0"
        },
        {
            "id": "activity:procurement:handle_exception",
            "name": "处理采购异常",
            "description": "处理采购过程中的异常情况，如订单延迟、供应商问题、物料短缺等",
            "activity_type": "action",
            "business_domain": "procurement",
            "success_criteria": "异常已处理并记录",
            "prerequisites": ["异常已识别"],
            "estimated_time": "15分钟",
            "risk_level": "high",
            "owner_dept": "采购部",
            "source_type": "log",
            "source_id": "exception_log",
            "vector_entity_uri": "activity://procurement/activity:procurement:handle_exception",
            "embedding_version": "1.0"
        },
        {
            "id": "activity:procurement:generate_report",
            "name": "生成采购报告",
            "description": "生成采购相关的统计报告，如月度采购统计、供应商绩效、物料采购趋势等",
            "activity_type": "query",
            "business_domain": "procurement",
            "success_criteria": "报告已生成",
            "prerequisites": ["有采购数据"],
            "estimated_time": "10分钟",
            "risk_level": "low",
            "owner_dept": "采购部",
            "source_type": "document",
            "source_id": "report_template",
            "vector_entity_uri": "activity://procurement/activity:procurement:generate_report",
            "embedding_version": "1.0"
        },
        {
            "id": "activity:procurement:check_inventory",
            "name": "检查库存",
            "description": "检查物料的当前库存情况，包括可用库存、在途库存、预留库存等",
            "activity_type": "query",
            "business_domain": "procurement",
            "success_criteria": "返回库存信息",
            "prerequisites": ["物料编码"],
            "estimated_time": "2分钟",
            "risk_level": "low",
            "owner_dept": "采购部",
            "source_type": "document",
            "source_id": "sap_mm_manual",
            "vector_entity_uri": "activity://procurement/activity:procurement:check_inventory",
            "embedding_version": "1.0"
        },
        {
            "id": "activity:procurement:contact_supplier",
            "name": "联系供应商",
            "description": "与供应商进行沟通，包括询价、催货、问题反馈等",
            "activity_type": "notification",
            "business_domain": "procurement",
            "success_criteria": "供应商已联系并收到回复",
            "prerequisites": ["供应商联系方式"],
            "estimated_time": "5分钟",
            "risk_level": "low",
            "owner_dept": "采购部",
            "source_type": "conversation",
            "source_id": "supplier_contact_log",
            "vector_entity_uri": "activity://procurement/activity:procurement:contact_supplier",
            "embedding_version": "1.0"
        },
        {
            "id": "activity:procurement:update_po",
            "name": "更新采购订单",
            "description": "更新已创建的采购订单信息，如修改数量、价格、交货日期等",
            "activity_type": "action",
            "business_domain": "procurement",
            "success_criteria": "订单信息已更新",
            "prerequisites": ["订单已创建", "未审批或已审批但可修改"],
            "estimated_time": "3分钟",
            "risk_level": "medium",
            "owner_dept": "采购部",
            "source_type": "document",
            "source_id": "sap_mm_manual",
            "vector_entity_uri": "activity://procurement/activity:procurement:update_po",
            "embedding_version": "1.0"
        },
        {
            "id": "activity:procurement:receive_goods",
            "name": "收货确认",
            "description": "确认供应商已交货，包括数量核对、质量检查、入库确认等",
            "activity_type": "action",
            "business_domain": "procurement",
            "success_criteria": "收货已确认并入库",
            "prerequisites": ["订单已审批", "货物已到达"],
            "estimated_time": "10分钟",
            "risk_level": "medium",
            "owner_dept": "仓储部",
            "source_type": "log",
            "source_id": "receiving_log",
            "vector_entity_uri": "activity://procurement/activity:procurement:receive_goods",
            "embedding_version": "1.0"
        },
        {
            "id": "activity:procurement:process_payment",
            "name": "处理付款",
            "description": "处理采购订单的付款流程，包括发票核对、付款申请、付款执行等",
            "activity_type": "action",
            "business_domain": "procurement",
            "success_criteria": "付款已处理",
            "prerequisites": ["收货已确认", "发票已收到"],
            "estimated_time": "5分钟",
            "risk_level": "high",
            "owner_dept": "财务部",
            "source_type": "document",
            "source_id": "payment_workflow",
            "vector_entity_uri": "activity://procurement/activity:procurement:process_payment",
            "embedding_version": "1.0"
        }
    ]
    
    return activities


def create_procurement_entities():
    """创建采购场景的业务实体数据"""
    entities = [
        {
            "id": "entity:procurement:purchase_order",
            "name": "采购订单",
            "description": "采购订单是采购部门向供应商发出的正式采购请求",
            "entity_type": "document",
            "business_domain": "procurement",
            "attributes": ["订单号", "供应商", "物料", "数量", "价格", "交货日期", "状态"],
            "source_type": "document",
            "source_id": "sap_mm_manual"
        },
        {
            "id": "entity:procurement:supplier",
            "name": "供应商",
            "description": "提供物料或服务的供应商信息",
            "entity_type": "master_data",
            "business_domain": "procurement",
            "attributes": ["供应商编码", "供应商名称", "联系方式", "资质信息", "绩效评级"],
            "source_type": "document",
            "source_id": "supplier_master"
        },
        {
            "id": "entity:procurement:material",
            "name": "物料",
            "description": "采购的物料主数据信息",
            "entity_type": "master_data",
            "business_domain": "procurement",
            "attributes": ["物料编码", "物料名称", "规格", "单位", "价格"],
            "source_type": "document",
            "source_id": "material_master"
        },
        {
            "id": "entity:procurement:department",
            "name": "采购部门",
            "description": "负责采购业务的部门",
            "entity_type": "organization",
            "business_domain": "procurement",
            "attributes": ["部门编码", "部门名称", "负责人", "职责范围"],
            "source_type": "document",
            "source_id": "org_structure"
        },
        {
            "id": "entity:procurement:approval_workflow",
            "name": "审批流程",
            "description": "采购订单的审批流程定义",
            "entity_type": "process",
            "business_domain": "procurement",
            "attributes": ["流程名称", "审批节点", "审批人", "审批条件"],
            "source_type": "document",
            "source_id": "workflow_definition"
        }
    ]
    
    return entities


def create_activity_capability_mappings():
    """创建活动-能力映射关系"""
    mappings = [
        {
            "id": "mapping:procurement:create_po:sap_create_po",
            "activity_id": "activity:procurement:create_po",
            "capability_id": "component:sap:create_po",
            "mapping_type": "primary",
            "confidence": 0.95,
            "description": "创建采购订单主要使用SAP创建PO组件"
        },
        {
            "id": "mapping:procurement:query_po:sap_query_po",
            "activity_id": "activity:procurement:query_po",
            "capability_id": "component:sap:query_po",
            "mapping_type": "primary",
            "confidence": 0.95,
            "description": "查询采购订单使用SAP查询PO组件"
        },
        {
            "id": "mapping:procurement:approve_po:workflow_approve",
            "activity_id": "activity:procurement:approve_po",
            "capability_id": "component:workflow:approve_po",
            "mapping_type": "primary",
            "confidence": 0.90,
            "description": "审批采购订单使用工作流审批组件"
        },
        {
            "id": "mapping:procurement:handle_exception:notification_send",
            "activity_id": "activity:procurement:handle_exception",
            "capability_id": "component:notification:send_alert",
            "mapping_type": "primary",
            "confidence": 0.85,
            "description": "处理异常需要发送通知"
        },
        {
            "id": "mapping:procurement:generate_report:report_generator",
            "activity_id": "activity:procurement:generate_report",
            "capability_id": "component:report:generate",
            "mapping_type": "primary",
            "confidence": 0.90,
            "description": "生成报告使用报告生成组件"
        },
        {
            "id": "mapping:procurement:check_inventory:sap_query_inventory",
            "activity_id": "activity:procurement:check_inventory",
            "capability_id": "component:sap:query_inventory",
            "mapping_type": "primary",
            "confidence": 0.95,
            "description": "检查库存使用SAP查询库存组件"
        },
        {
            "id": "mapping:procurement:contact_supplier:email_send",
            "activity_id": "activity:procurement:contact_supplier",
            "capability_id": "component:email:send",
            "mapping_type": "primary",
            "confidence": 0.90,
            "description": "联系供应商使用邮件发送组件"
        },
        {
            "id": "mapping:procurement:update_po:sap_update_po",
            "activity_id": "activity:procurement:update_po",
            "capability_id": "component:sap:update_po",
            "mapping_type": "primary",
            "confidence": 0.95,
            "description": "更新采购订单使用SAP更新PO组件"
        },
        {
            "id": "mapping:procurement:receive_goods:sap_receive_goods",
            "activity_id": "activity:procurement:receive_goods",
            "capability_id": "component:sap:receive_goods",
            "mapping_type": "primary",
            "confidence": 0.90,
            "description": "收货确认使用SAP收货组件"
        },
        {
            "id": "mapping:procurement:process_payment:payment_processor",
            "activity_id": "activity:procurement:process_payment",
            "capability_id": "component:payment:process",
            "mapping_type": "primary",
            "confidence": 0.85,
            "description": "处理付款使用付款处理组件"
        }
    ]
    
    return mappings


def save_data(data, filename):
    """保存数据到JSON文件"""
    filepath = DATA_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] 已保存: {filepath}")


def main():
    """主函数"""
    print("=" * 60)
    print("采购场景数据采集")
    print("=" * 60)
    print()
    
    # 创建业务活动数据
    print("[INFO] 创建业务活动数据...")
    activities = create_procurement_activities()
    save_data(activities, "activities.json")
    print(f"   创建了 {len(activities)} 个业务活动")
    print()
    
    # 创建业务实体数据
    print("[INFO] 创建业务实体数据...")
    entities = create_procurement_entities()
    save_data(entities, "entities.json")
    print(f"   创建了 {len(entities)} 个业务实体")
    print()
    
    # 创建活动-能力映射数据
    print("[INFO] 创建活动-能力映射数据...")
    mappings = create_activity_capability_mappings()
    save_data(mappings, "mappings.json")
    print(f"   创建了 {len(mappings)} 个映射关系")
    print()
    
    # 创建汇总信息
    summary = {
        "created_at": datetime.now().isoformat(),
        "total_activities": len(activities),
        "total_entities": len(entities),
        "total_mappings": len(mappings),
        "business_domain": "procurement"
    }
    save_data(summary, "summary.json")
    
    print("=" * 60)
    print("[OK] 数据采集完成！")
    print("=" * 60)
    print()
    print(f"[SUMMARY] 汇总:")
    print(f"   - 业务活动: {len(activities)} 个")
    print(f"   - 业务实体: {len(entities)} 个")
    print(f"   - 映射关系: {len(mappings)} 个")
    print()
    print(f"[INFO] 数据保存位置: {DATA_DIR}")


if __name__ == "__main__":
    main()

