# 企业架构平台功能实施方案

## 第四部分：API层与前端层实现

**方案日期**: 2025-12-07  
**目标**: 详细说明API层和前端层的实现

---

## 📋 一、API层实现

### 1.1 组织架构API ⭐

#### 1.1.1 API实现

```python
# metadata-service/src/api/organization_architecture.py

"""
组织架构API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from uuid import UUID

from database.src.core.database import get_db
from database.src.core.neo4j_client import Neo4jClient, get_neo4j_client
from metadata_service.src.services.organization_architecture_service import OrganizationArchitectureService

router = APIRouter(prefix="/api/enterprise-architecture/organizations", tags=["Organization Architecture"])


@router.get("", summary="获取组织列表")
async def get_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    organization_type: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取组织列表"""
    service = OrganizationArchitectureService(db)
    
    query = db.query(OrganizationUnit)
    if organization_type:
        query = query.filter(OrganizationUnit.organization_type == organization_type)
    
    total = query.count()
    organizations = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "organizations": [org_to_dict(org) for org in organizations]
    }


@router.get("/{org_id}", summary="获取组织详情")
async def get_organization(
    org_id: UUID,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取组织详情"""
    service = OrganizationArchitectureService(db)
    org = await service.get_organization_unit(org_id)
    
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")
    
    return org_to_dict(org)


@router.get("/{org_id}/hierarchy", summary="获取组织层级结构")
async def get_organization_hierarchy(
    org_id: UUID,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取组织层级结构"""
    service = OrganizationArchitectureService(db)
    hierarchy = await service.get_organization_hierarchy(org_id)
    
    if not hierarchy:
        raise HTTPException(status_code=404, detail="组织不存在")
    
    return hierarchy


@router.get("/{org_id}/responsibilities", summary="获取组织责任范围")
async def get_organization_responsibilities(
    org_id: UUID,
    db: Session = Depends(get_db),
    neo4j: Neo4jClient = Depends(get_neo4j_client)
) -> Dict[str, Any]:
    """获取组织的责任范围"""
    service = OrganizationArchitectureService(db, neo4j)
    try:
        return await service.get_organization_responsibilities(org_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{org_id}/resources", summary="获取组织IT资源统计")
async def get_organization_resources(
    org_id: UUID,
    db: Session = Depends(get_db),
    neo4j: Neo4jClient = Depends(get_neo4j_client)
) -> Dict[str, Any]:
    """获取组织的IT资源统计"""
    service = OrganizationArchitectureService(db, neo4j)
    try:
        return await service.get_organization_resources(org_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def org_to_dict(org: OrganizationUnit) -> Dict[str, Any]:
    """组织对象转字典"""
    return {
        "id": str(org.id),
        "name": org.name,
        "code": org.code,
        "description": org.description,
        "organization_type": org.organization_type,
        "level": org.level,
        "parent_id": str(org.parent_id) if org.parent_id else None,
        "manager_id": str(org.manager_id) if org.manager_id else None,
        "location": org.location,
        "status": org.status,
        "meta_data": org.meta_data
    }
```

### 1.2 技术实例API ⭐

#### 1.2.1 API实现

```python
# metadata-service/src/api/technology_architecture.py

"""
技术架构API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from uuid import UUID

from database.src.core.database import get_db
from database.src.core.neo4j_client import Neo4jClient, get_neo4j_client
from metadata_service.src.services.technology_instance_service import TechnologyInstanceService
from metadata_service.src.services.technology_type_service import TechnologyTypeService

router = APIRouter(prefix="/api/enterprise-architecture/technology", tags=["Technology Architecture"])


@router.get("/instances", summary="获取技术实例列表")
async def get_technology_instances(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    technology_name: Optional[str] = None,
    technology_type: Optional[str] = None,
    system_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取技术实例列表"""
    service = TechnologyInstanceService(db)
    
    query = db.query(TechnologyInstance)
    if technology_name:
        query = query.filter(TechnologyInstance.technology_name == technology_name)
    if technology_type:
        query = query.filter(TechnologyInstance.technology_type == technology_type)
    if system_id:
        query = query.filter(TechnologyInstance.application_system_id == system_id)
    
    total = query.count()
    instances = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "instances": [instance_to_dict(i) for i in instances]
    }


@router.get("/instances/by-system/{system_id}", summary="按系统查询技术实例")
async def get_instances_by_system(
    system_id: UUID,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """按系统查询技术实例"""
    service = TechnologyInstanceService(db)
    instances = await service.get_instances_by_system(system_id)
    
    return [instance_to_dict(i) for i in instances]


@router.post("/instances", summary="创建技术实例")
async def create_technology_instance(
    instance_data: Dict[str, Any],
    db: Session = Depends(get_db),
    neo4j: Neo4jClient = Depends(get_neo4j_client)
) -> Dict[str, Any]:
    """创建技术实例"""
    service = TechnologyInstanceService(db, neo4j)
    
    try:
        instance = await service.create_technology_instance(**instance_data)
        return instance_to_dict(instance)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/instances/import", summary="从Excel导入技术实例")
async def import_technology_instances(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    neo4j: Neo4jClient = Depends(get_neo4j_client)
) -> Dict[str, Any]:
    """从Excel导入技术实例"""
    import tempfile
    import os
    
    service = TechnologyInstanceService(db, neo4j)
    
    # 保存上传的文件
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        result = await service.import_from_excel(tmp_file_path)
        return result
    finally:
        # 删除临时文件
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


@router.get("/types", summary="获取技术类型列表")
async def get_technology_types(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """获取技术类型列表"""
    service = TechnologyTypeService(db)
    types = await service.get_all_technology_types(category)
    
    return [type_to_dict(t) for t in types]


@router.get("/types/{type_id}/instances", summary="获取技术类型的所有实例")
async def get_instances_by_type(
    type_id: UUID,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """获取技术类型的所有实例"""
    service = TechnologyTypeService(db)
    instances = await service.get_instances_by_type(type_id)
    
    return [instance_to_dict(i) for i in instances]


@router.get("/standardization", summary="技术标准化分析")
async def analyze_standardization(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """技术标准化分析"""
    service = TechnologyTypeService(db)
    return await service.analyze_standardization()


def instance_to_dict(instance: TechnologyInstance) -> Dict[str, Any]:
    """技术实例对象转字典"""
    return {
        "id": str(instance.id),
        "name": instance.name,
        "instance_id": instance.instance_id,
        "application_system_id": str(instance.application_system_id) if instance.application_system_id else None,
        "technology_type": instance.technology_type,
        "technology_name": instance.technology_name,
        "technology_type_id": str(instance.technology_type_id) if instance.technology_type_id else None,
        "vendor": instance.vendor,
        "version": instance.version,
        "deployment_type": instance.deployment_type,
        "host": instance.host,
        "port": instance.port,
        "location": instance.location,
        "capacity": instance.capacity,
        "status": instance.status,
        "lifecycle_status": instance.lifecycle_status
    }


def type_to_dict(tech_type: TechnologyType) -> Dict[str, Any]:
    """技术类型对象转字典"""
    return {
        "id": str(tech_type.id),
        "name": tech_type.name,
        "category": tech_type.category,
        "description": tech_type.description,
        "standard_version": tech_type.standard_version,
        "recommended_version": tech_type.recommended_version,
        "lifecycle_status": tech_type.lifecycle_status,
        "owner_team": tech_type.owner_team,
        "governance_status": tech_type.governance_status,
        "instance_count": tech_type.instance_count
    }
```

### 1.3 增强的业务架构API

#### 1.3.1 API实现

```python
# metadata-service/src/api/enterprise_architecture.py

# 在现有API基础上增强

@router.get("/business/processes/pain-points", summary="查询有痛点的业务流程")
async def get_processes_with_pain_points(
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """查询有痛点的业务流程"""
    service = EnterpriseArchitectureService(db)
    processes = await service.get_business_processes_with_pain_points()
    return processes


@router.get("/business/processes/by-organization/{org_id}", summary="按组织查询业务流程")
async def get_processes_by_organization(
    org_id: UUID,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """按组织查询业务流程"""
    service = EnterpriseArchitectureService(db)
    processes = await service.get_business_processes_by_organization(org_id)
    return processes


@router.get("/application/systems/by-category/{category}", summary="按分类查询应用系统")
async def get_systems_by_category(
    category: str,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """按分类查询应用系统"""
    service = EnterpriseArchitectureService(db)
    systems = await service.get_application_systems_by_category(category)
    return systems


@router.get("/application/systems/{system_id}/technologies", summary="获取系统的技术栈")
async def get_system_technologies(
    system_id: UUID,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取系统的技术栈"""
    service = EnterpriseArchitectureService(db)
    return await service.get_system_technologies(system_id)
```

---

## 🎨 二、前端层实现

### 2.1 组织架构页面 ⭐

#### 2.1.1 页面实现

```typescript
// web-ui/src/app/enterprise-architecture/organizations/page.tsx

"use client";

import { useState, useEffect } from "react";
import { Card, Table, Tree, Button, Space, Tag, Statistic, Row, Col } from "antd";
import { OrganizationUnitOutlined, TeamOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";

interface Organization {
  id: string;
  name: string;
  code: string;
  organization_type: string;
  level: number;
  parent_id?: string;
  status: string;
}

interface OrganizationResponsibilities {
  organization: {
    id: string;
    name: string;
  };
  capabilities: Array<{ id: string; name: string }>;
  processes: Array<{ id: string; name: string; criticality?: string }>;
  systems: Array<{ id: string; name: string; system_category?: string }>;
  technologies: Array<{ id: string; name: string; technology_name: string }>;
}

export default function OrganizationsPage() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<string | null>(null);
  const [responsibilities, setResponsibilities] = useState<OrganizationResponsibilities | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrg) {
      fetchResponsibilities(selectedOrg);
    }
  }, [selectedOrg]);

  const fetchOrganizations = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/enterprise-architecture/organizations");
      const data = await response.json();
      setOrganizations(data.organizations || []);
    } catch (error) {
      console.error("Failed to fetch organizations:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchResponsibilities = async (orgId: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/enterprise-architecture/organizations/${orgId}/responsibilities`);
      const data = await response.json();
      setResponsibilities(data);
    } catch (error) {
      console.error("Failed to fetch responsibilities:", error);
    } finally {
      setLoading(false);
    }
  };

  const columns: ColumnsType<Organization> = [
    {
      title: "组织名称",
      dataIndex: "name",
      key: "name",
      render: (text, record) => (
        <Button
          type="link"
          onClick={() => setSelectedOrg(record.id)}
        >
          {text}
        </Button>
      ),
    },
    {
      title: "组织编码",
      dataIndex: "code",
      key: "code",
    },
    {
      title: "组织类型",
      dataIndex: "organization_type",
      key: "organization_type",
      render: (type) => <Tag>{type}</Tag>,
    },
    {
      title: "层级",
      dataIndex: "level",
      key: "level",
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (status) => (
        <Tag color={status === "active" ? "green" : "red"}>{status}</Tag>
      ),
    },
  ];

  return (
    <div style={{ padding: "24px" }}>
      <Card title="组织架构管理" style={{ marginBottom: "24px" }}>
        <Table
          columns={columns}
          dataSource={organizations}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      {selectedOrg && responsibilities && (
        <Card title={`${responsibilities.organization.name} - 责任范围`}>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="业务能力"
                value={responsibilities.capabilities.length}
                prefix={<TeamOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="业务流程"
                value={responsibilities.processes.length}
                prefix={<OrganizationUnitOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="应用系统"
                value={responsibilities.systems.length}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="技术实例"
                value={responsibilities.technologies.length}
              />
            </Col>
          </Row>

          <div style={{ marginTop: "24px" }}>
            <h3>业务能力</h3>
            <Space wrap>
              {responsibilities.capabilities.map((cap) => (
                <Tag key={cap.id}>{cap.name}</Tag>
              ))}
            </Space>

            <h3 style={{ marginTop: "16px" }}>业务流程</h3>
            <Space wrap>
              {responsibilities.processes.map((proc) => (
                <Tag key={proc.id} color={proc.criticality === "高" ? "red" : "blue"}>
                  {proc.name}
                </Tag>
              ))}
            </Space>

            <h3 style={{ marginTop: "16px" }}>应用系统</h3>
            <Space wrap>
              {responsibilities.systems.map((sys) => (
                <Tag key={sys.id} color={sys.system_category === "Core" ? "red" : "blue"}>
                  {sys.name}
                </Tag>
              ))}
            </Space>
          </div>
        </Card>
      )}
    </div>
  );
}
```

### 2.2 技术实例管理页面 ⭐

#### 2.2.1 页面实现

```typescript
// web-ui/src/app/enterprise-architecture/technology/instances/page.tsx

"use client";

import { useState, useEffect } from "react";
import { Card, Table, Button, Space, Tag, Select, Upload, message } from "antd";
import { UploadOutlined, DownloadOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";

interface TechnologyInstance {
  id: string;
  name: string;
  instance_id?: string;
  application_system_id?: string;
  technology_type: string;
  technology_name: string;
  version?: string;
  vendor?: string;
  deployment_type: string;
  host?: string;
  port?: number;
  location?: string;
  capacity?: string;
  status: string;
}

export default function TechnologyInstancesPage() {
  const [instances, setInstances] = useState<TechnologyInstance[]>([]);
  const [loading, setLoading] = useState(false);
  const [systemFilter, setSystemFilter] = useState<string | undefined>();
  const [technologyFilter, setTechnologyFilter] = useState<string | undefined>();

  useEffect(() => {
    fetchInstances();
  }, [systemFilter, technologyFilter]);

  const fetchInstances = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (systemFilter) params.append("system_id", systemFilter);
      if (technologyFilter) params.append("technology_name", technologyFilter);
      
      const response = await fetch(
        `/api/enterprise-architecture/technology/instances?${params.toString()}`
      );
      const data = await response.json();
      setInstances(data.instances || []);
    } catch (error) {
      console.error("Failed to fetch instances:", error);
      message.error("获取技术实例失败");
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(
        "/api/enterprise-architecture/technology/instances/import",
        {
          method: "POST",
          body: formData,
        }
      );
      const result = await response.json();
      
      if (result.success > 0) {
        message.success(`成功导入 ${result.success} 条记录`);
        fetchInstances();
      } else {
        message.error(`导入失败: ${result.errors?.join(", ") || "未知错误"}`);
      }
    } catch (error) {
      message.error("导入失败");
    }
  };

  const columns: ColumnsType<TechnologyInstance> = [
    {
      title: "实例名称",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "技术类型",
      dataIndex: "technology_type",
      key: "technology_type",
      render: (type) => <Tag>{type}</Tag>,
    },
    {
      title: "技术名称",
      dataIndex: "technology_name",
      key: "technology_name",
    },
    {
      title: "版本",
      dataIndex: "version",
      key: "version",
    },
    {
      title: "部署类型",
      dataIndex: "deployment_type",
      key: "deployment_type",
      render: (type) => (
        <Tag color={type === "independent" ? "blue" : "green"}>{type}</Tag>
      ),
    },
    {
      title: "位置",
      dataIndex: "location",
      key: "location",
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (status) => (
        <Tag color={status === "active" ? "green" : "red"}>{status}</Tag>
      ),
    },
  ];

  return (
    <div style={{ padding: "24px" }}>
      <Card
        title="技术实例管理"
        extra={
          <Space>
            <Upload
              accept=".xlsx,.xls"
              beforeUpload={(file) => {
                handleImport(file);
                return false;
              }}
              showUploadList={false}
            >
              <Button icon={<UploadOutlined />}>导入Excel</Button>
            </Upload>
            <Button icon={<DownloadOutlined />}>下载模板</Button>
          </Space>
        }
      >
        <Space style={{ marginBottom: "16px" }}>
          <Select
            placeholder="筛选系统"
            style={{ width: 200 }}
            allowClear
            onChange={setSystemFilter}
          >
            {/* 从API获取系统列表 */}
          </Select>
          <Select
            placeholder="筛选技术"
            style={{ width: 200 }}
            allowClear
            onChange={setTechnologyFilter}
          >
            {/* 从API获取技术列表 */}
          </Select>
        </Space>

        <Table
          columns={columns}
          dataSource={instances}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      </Card>
    </div>
  );
}
```

### 2.3 技术标准化分析页面 ⭐

#### 2.3.1 页面实现

```typescript
// web-ui/src/app/enterprise-architecture/technology/standardization/page.tsx

"use client";

import { useState, useEffect } from "react";
import { Card, Table, Progress, Tag, Statistic, Row, Col } from "antd";
import type { ColumnsType } from "antd/es/table";

interface StandardizationResult {
  technology: string;
  category: string;
  standard_version?: string;
  total_instances: number;
  compliant_instances: number;
  non_compliant_instances: number;
  compliance_rate: number;
  versions_in_use: Record<string, number>;
  lifecycle_status: string;
}

export default function TechnologyStandardizationPage() {
  const [data, setData] = useState<StandardizationResult[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStandardization();
  }, []);

  const fetchStandardization = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        "/api/enterprise-architecture/technology/standardization"
      );
      const result = await response.json();
      setData(result.technologies || []);
    } catch (error) {
      console.error("Failed to fetch standardization:", error);
    } finally {
      setLoading(false);
    }
  };

  const columns: ColumnsType<StandardizationResult> = [
    {
      title: "技术名称",
      dataIndex: "technology",
      key: "technology",
    },
    {
      title: "类别",
      dataIndex: "category",
      key: "category",
      render: (category) => <Tag>{category}</Tag>,
    },
    {
      title: "标准版本",
      dataIndex: "standard_version",
      key: "standard_version",
    },
    {
      title: "实例总数",
      dataIndex: "total_instances",
      key: "total_instances",
    },
    {
      title: "合规率",
      dataIndex: "compliance_rate",
      key: "compliance_rate",
      render: (rate) => (
        <Progress
          percent={rate}
          status={rate >= 80 ? "success" : rate >= 60 ? "normal" : "exception"}
        />
      ),
    },
    {
      title: "版本分布",
      dataIndex: "versions_in_use",
      key: "versions_in_use",
      render: (versions) => (
        <Space wrap>
          {Object.entries(versions).map(([version, count]) => (
            <Tag key={version}>
              {version}: {count}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: "生命周期",
      dataIndex: "lifecycle_status",
      key: "lifecycle_status",
      render: (status) => (
        <Tag color={status === "strategic" ? "green" : "orange"}>
          {status}
        </Tag>
      ),
    },
  ];

  const totalTechnologies = data.length;
  const avgComplianceRate =
    data.length > 0
      ? data.reduce((sum, item) => sum + item.compliance_rate, 0) / data.length
      : 0;

  return (
    <div style={{ padding: "24px" }}>
      <Card title="技术标准化分析" style={{ marginBottom: "24px" }}>
        <Row gutter={16}>
          <Col span={8}>
            <Statistic
              title="技术总数"
              value={totalTechnologies}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="平均合规率"
              value={avgComplianceRate.toFixed(2)}
              suffix="%"
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="高合规率技术"
              value={data.filter((d) => d.compliance_rate >= 80).length}
            />
          </Col>
        </Row>
      </Card>

      <Card>
        <Table
          columns={columns}
          dataSource={data}
          rowKey="technology"
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      </Card>
    </div>
  );
}
```

---

## ✅ 三、实施检查清单

### 3.1 API层检查

```yaml
- [ ] 组织架构API完成
- [ ] 技术实例API完成
- [ ] 技术类型API完成
- [ ] 技术标准化API完成
- [ ] 业务架构API增强完成
- [ ] 应用架构API增强完成
- [ ] API文档更新完成
```

### 3.2 前端层检查

```yaml
- [ ] 组织架构页面完成
- [ ] 技术实例管理页面完成
- [ ] 技术标准化分析页面完成
- [ ] 业务架构页面增强完成
- [ ] 应用架构页面增强完成
- [ ] 路由配置完成
- [ ] 组件测试完成
```

---

**第四部分完成**  
**所有功能实施方案完成**

