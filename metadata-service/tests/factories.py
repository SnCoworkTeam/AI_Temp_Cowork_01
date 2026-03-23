"""
测试数据工厂
用于创建测试数据
"""
from datetime import datetime
from typing import Dict, Any, Optional


class WorkflowMetadataFactory:
    """工作流元数据工厂"""
    
    @staticmethod
    def create(
        workflow_id: Optional[str] = None,
        name: Optional[str] = None,
        version: str = "v1.0",
        definition: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """创建工作流元数据字典"""
        if workflow_id is None:
            workflow_id = f"test_workflow_{datetime.now().timestamp()}"
        
        if name is None:
            name = f"Test Workflow {workflow_id}"
        
        if definition is None:
            definition = {"nodes": [], "connections": []}
        
        return {
            "workflow_id": workflow_id,
            "name": name,
            "display_name": f"Test Workflow Display {workflow_id}",
            "description": "Test workflow description",
            "status": "active",
            "version": version,
            "category": "TEST",
            "workflow_type": "STANDARD",
            "definition": definition,
            "input_schema": {},
            "output_schema": {},
            "execution_count": 0,
            "last_execution_time": None,
            "average_execution_time": None,
            "success_rate": None,
            "dependencies": {},
            "data_sources": [],
            "data_sinks": [],
            "business_owner": "test_business_owner",
            "technical_owner": "test_technical_owner",
            "tags": ["test"],
            "use_cases": ["testing"],
            "metadata": {},
            **kwargs
        }


class WorkflowVersionFactory:
    """工作流版本工厂"""
    
    @staticmethod
    def create(
        workflow_id: str,
        version: Optional[str] = None,
        version_number: Optional[int] = None,
        definition: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """创建工作流版本字典"""
        if version is None:
            version = "v1.0"
        
        if version_number is None:
            version_number = 1
        
        if definition is None:
            definition = {"nodes": [{"id": "node1", "type": "start"}], "connections": []}
        
        return {
            "workflow_id": workflow_id,
            "version": version,
            "version_number": version_number,
            "description": "Test version",
            "change_summary": "Test changes",
            "definition": definition,
            "changes": {"added_nodes": ["node1"]},
            "created_by": "test_user",
            **kwargs
        }

