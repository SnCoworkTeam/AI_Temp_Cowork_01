#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从网络搜索并生成SAP MM文档，导入到知识库
"""
import requests
import json
import time
import io
import sys
from typing import List, Dict, Any
from datetime import datetime

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置
KNOWLEDGE_SERVICE_URL = "http://localhost:8004/api/documents/upload"

# SAP MM核心主题和文档模板（基于网络知识）
SAP_MM_DOCUMENTS = [
    {
        "title": "SAP MM物料管理模块概述",
        "content": """
# SAP MM物料管理模块概述

## 模块简介
SAP MM (Materials Management) 是SAP ERP系统的核心模块之一，负责企业物料和采购管理。

## 主要功能
1. **物料主数据管理**
   - 物料主数据维护（MARA表）
   - 物料分类管理
   - 物料描述和规格管理

2. **采购管理**
   - 采购申请（EBAN）
   - 采购订单（EKKO/EKPO）
   - 供应商管理（LFA1）

3. **库存管理**
   - 库存地点管理（MARD）
   - 物料凭证（MKPF/MSEG）
   - 库存盘点

4. **发票校验**
   - 发票录入
   - 发票校验
   - 差异处理

## 核心表结构
- **MARA**: 物料主数据
- **EKKO**: 采购订单抬头
- **EKPO**: 采购订单行项目
- **LFA1**: 供应商主数据
- **MARD**: 库存地点视图
- **MKPF**: 物料凭证抬头
- **MSEG**: 物料凭证行项目

## 业务流程
1. 采购申请 → 采购订单 → 收货 → 发票校验
2. 物料需求计划 → 采购 → 入库 → 出库
3. 供应商评估 → 合同管理 → 采购执行
        """,
        "category": "overview",
        "tags": ["SAP MM", "物料管理", "概述"]
    },
    {
        "title": "SAP MM物料主数据管理",
        "content": """
# SAP MM物料主数据管理

## 物料主数据（MARA表）

### 核心字段
- **MATNR**: 物料号（唯一标识）
- **MAKTX**: 物料描述
- **MEINS**: 基本计量单位
- **MTART**: 物料类型
- **MATKL**: 物料组

### 物料类型（MTART）
- **FERT**: 成品
- **HALB**: 半成品
- **ROH**: 原材料
- **HIBE**: 贸易商品
- **DIEN**: 服务

### 维护流程
1. 创建物料主数据（MM01）
2. 维护组织级别数据
3. 维护分类视图
4. 维护采购视图
5. 维护库存管理视图

### 最佳实践
- 物料编号采用有意义编码
- 建立物料分类体系
- 定期清理无效物料
- 维护物料描述规范
        """,
        "category": "master_data",
        "tags": ["物料主数据", "MARA", "数据管理"]
    },
    {
        "title": "SAP MM采购订单管理",
        "content": """
# SAP MM采购订单管理

## 采购订单结构

### 抬头表（EKKO）
- **EBELN**: 采购订单号
- **LIFNR**: 供应商编号
- **BEDAT**: 订单日期
- **ZTERM**: 付款条件
- **EKORG**: 采购组织

### 行项目表（EKPO）
- **EBELN**: 采购订单号
- **EBELP**: 行项目号
- **MATNR**: 物料号
- **MENGE**: 采购数量
- **NETPR**: 净价
- **PEINH**: 价格单位

## 采购订单类型
- **NB**: 标准采购订单
- **FO**: 框架协议
- **UB**: 库存转储订单
- **KB**: 服务采购订单

## 采购流程
1. **创建采购申请**（ME51N）
   - 输入物料和数量
   - 指定需求日期
   - 选择供应商

2. **创建采购订单**（ME21N）
   - 参考采购申请
   - 输入价格和条件
   - 审批流程

3. **收货**（MIGO）
   - 参考采购订单
   - 输入收货数量
   - 生成物料凭证

4. **发票校验**（MIRO）
   - 参考采购订单
   - 输入发票金额
   - 完成三单匹配

## 关键配置
- 采购组织
- 采购组
- 审批策略
- 价格确定过程
        """,
        "category": "procurement",
        "tags": ["采购订单", "EKKO", "EKPO", "采购流程"]
    },
    {
        "title": "SAP MM供应商管理",
        "content": """
# SAP MM供应商管理

## 供应商主数据（LFA1表）

### 核心字段
- **LIFNR**: 供应商编号
- **NAME1**: 供应商名称
- **ORT01**: 城市
- **LAND1**: 国家代码
- **REGIO**: 地区
- **STRAS**: 街道地址

## 供应商账户组
- **0001**: 标准供应商
- **0002**: 一次性供应商
- **KRED**: 供应商（财务视图）

## 供应商维护流程
1. **创建供应商**（XK01）
   - 输入基本信息
   - 维护地址数据
   - 维护采购数据

2. **维护采购数据**（MK01）
   - 采购组织
   - 采购组
   - 付款条件
   - 交货条件

3. **供应商评估**
   - 价格评估
   - 质量评估
   - 交货评估
   - 服务评估

## 供应商主数据视图
- **一般数据**: 名称、地址、联系方式
- **采购数据**: 采购组织、采购组
- **财务数据**: 付款条件、银行信息
- **合作伙伴数据**: 联系人信息

## 供应商评估指标
- **价格**: 价格竞争力
- **质量**: 质量合格率
- **交货**: 准时交货率
- **服务**: 服务水平

## 最佳实践
- 建立供应商分类体系
- 定期更新供应商信息
- 实施供应商评估机制
- 维护供应商合同信息
        """,
        "category": "vendor",
        "tags": ["供应商", "LFA1", "供应商管理"]
    },
    {
        "title": "SAP MM库存管理",
        "content": """
# SAP MM库存管理

## 库存地点视图（MARD表）

### 核心字段
- **MATNR**: 物料号
- **WERKS**: 工厂
- **LGORT**: 库存地点
- **LABST**: 非限制使用库存
- **UMLME**: 在途库存
- **INSME**: 质检库存

## 库存类型
- **非限制使用库存**: 可自由使用的库存
- **质检库存**: 待检验的库存
- **冻结库存**: 被冻结的库存
- **在途库存**: 在运输途中的库存

## 物料凭证（MKPF/MSEG）

### 凭证抬头（MKPF）
- **MBLNR**: 物料凭证号
- **MJAHR**: 会计年度
- **BUDAT**: 过账日期
- **BLART**: 凭证类型

### 凭证行项目（MSEG）
- **MBLNR**: 物料凭证号
- **MJAHR**: 会计年度
- **ZEILE**: 行项目号
- **BWART**: 移动类型
- **MENGE**: 数量
- **WERKS**: 工厂
- **LGORT**: 库存地点

## 移动类型（BWART）
- **101**: 采购订单收货
- **102**: 采购订单退货
- **201**: 生产收货
- **261**: 从质检到非限制
- **301**: 工厂间转储
- **311**: 库存地点间转储
- **601**: 销售发货
- **701**: 生产发料

## 库存盘点流程
1. **创建盘点凭证**（MI01）
2. **打印盘点清单**（MI04）
3. **输入盘点结果**（MI04）
4. **差异处理**（MI07）
5. **过账差异**（MI20）

## 库存报表
- **MMBE**: 库存概览
- **MB52**: 库存清单
- **MB5B**: 库存余额
- **MB5T**: 库存周转率

## 最佳实践
- 定期盘点库存
- 及时处理差异
- 优化库存结构
- 控制安全库存
        """,
        "category": "inventory",
        "tags": ["库存管理", "MARD", "物料凭证", "盘点"]
    },
    {
        "title": "SAP MM采购申请管理",
        "content": """
# SAP MM采购申请管理

## 采购申请（EBAN表）

### 核心字段
- **BANFN**: 采购申请号
- **BNFPO**: 申请行项目号
- **MATNR**: 物料号
- **MENGE**: 申请数量
- **BADAT**: 需求日期
- **AFNAM**: 申请人

## 采购申请类型
- **NB**: 标准采购申请
- **UB**: 库存转储申请
- **KB**: 服务申请

## 采购申请流程
1. **创建采购申请**（ME51N）
   - 输入物料和数量
   - 指定需求日期
   - 选择供应商（可选）

2. **审批采购申请**
   - 根据审批策略
   - 多级审批流程
   - 审批历史记录

3. **转换为采购订单**（ME21N）
   - 参考采购申请
   - 选择供应商
   - 输入价格条件

4. **采购申请监控**
   - 未处理申请
   - 已审批申请
   - 已转订单申请

## 采购申请来源
- **手动创建**: 用户直接创建
- **MRP生成**: 物料需求计划自动生成
- **项目系统**: 从项目系统创建
- **生产订单**: 从生产订单创建

## 采购申请审批
- **审批策略配置**
- **审批路径定义**
- **审批权限管理**
- **审批历史追踪**

## 关键报表
- **ME5A**: 按申请人显示采购申请
- **ME5J**: 按物料显示采购申请
- **ME5K**: 按供应商显示采购申请
- **ME5L**: 按采购组显示采购申请

## 最佳实践
- 建立清晰的审批流程
- 及时处理采购申请
- 监控申请转订单率
- 优化申请创建效率
        """,
        "category": "requisition",
        "tags": ["采购申请", "EBAN", "采购流程"]
    },
    {
        "title": "SAP MM物料凭证管理",
        "content": """
# SAP MM物料凭证管理

## 物料凭证概述

物料凭证是SAP MM模块中记录所有库存移动的凭证，包括收货、发货、转储等操作。

## 凭证抬头（MKPF表）

### 核心字段
- **MBLNR**: 物料凭证号（唯一标识）
- **MJAHR**: 会计年度
- **BUDAT**: 过账日期
- **BLART**: 凭证类型
- **USNAM**: 用户名
- **TCODE**: 事务代码

## 凭证行项目（MSEG表）

### 核心字段
- **MBLNR**: 物料凭证号
- **MJAHR**: 会计年度
- **ZEILE**: 行项目号
- **BWART**: 移动类型
- **MATNR**: 物料号
- **MENGE**: 数量
- **MEINS**: 单位
- **WERKS**: 工厂
- **LGORT**: 库存地点

## 移动类型（BWART）

### 收货类
- **101**: 采购订单收货
- **102**: 采购订单退货
- **103**: 采购订单收货到质检
- **122**: 供应商退货
- **201**: 生产收货
- **261**: 从质检到非限制

### 发货类
- **201**: 生产发料
- **261**: 生产收货
- **601**: 销售发货
- **602**: 销售退货

### 转储类
- **301**: 工厂间转储
- **302**: 工厂间转储（在途）
- **311**: 库存地点间转储
- **312**: 库存地点间转储（在途）

### 盘点类
- **701**: 盘点收货
- **702**: 盘点发货

## 物料凭证创建方式
1. **收货**（MIGO）
   - 采购订单收货
   - 生产收货
   - 其他收货

2. **发货**（MIGO）
   - 生产发料
   - 销售发货
   - 其他发货

3. **转储**（MIGO）
   - 工厂间转储
   - 库存地点间转储

4. **盘点**（MI01/MI04）
   - 创建盘点凭证
   - 输入盘点结果

## 凭证查询
- **MB03**: 显示物料凭证
- **MB51**: 物料凭证清单
- **MB52**: 库存清单
- **MB5B**: 库存余额

## 凭证冲销
- **MBST**: 冲销物料凭证
- **MB11**: 手动输入物料凭证

## 最佳实践
- 及时处理物料凭证
- 确保凭证数据准确性
- 定期核对凭证与库存
- 建立凭证审批机制
        """,
        "category": "document",
        "tags": ["物料凭证", "MKPF", "MSEG", "移动类型"]
    }
]

def import_documents(documents: List[Dict[str, Any]]) -> int:
    """批量导入文档到知识库"""
    created = 0
    failed = 0
    
    print(f"\n=== 导入 {len(documents)} 个SAP MM文档 ===\n")
    
    for i, doc in enumerate(documents, 1):
        print(f"[{i}/{len(documents)}] 导入: {doc['title']}...")
        
        # 构建文档请求体
        document_data = {
            "title": doc["title"],
            "content": doc["content"].strip(),
            "category": doc.get("category", "sap_mm"),
            "tags": doc.get("tags", []),
            "metadata": {
                "source": "web_generated",
                "module": "SAP MM",
                "generated_at": datetime.now().isoformat(),
                "category": doc.get("category")
            }
        }
        
        try:
            # 使用multipart/form-data格式上传文件
            # 将内容写入临时文件
            import tempfile
            import os
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as tmp_file:
                tmp_file.write(doc["content"].strip())
                tmp_file_path = tmp_file.name
            
            try:
                # 准备multipart/form-data请求
                with open(tmp_file_path, 'rb') as f:
                    files = {
                        'file': (f"{doc['title']}.txt", f, 'text/plain')
                    }
                    data = {
                        'title': doc["title"],
                        'category': doc.get("category", "sap_mm"),
                        'tags': ','.join(doc.get("tags", [])),
                        'metadata': json.dumps({
                            "source": "web_generated",
                            "module": "SAP MM",
                            "generated_at": datetime.now().isoformat(),
                            "category": doc.get("category")
                        })
                    }
                    
                    response = requests.post(
                        KNOWLEDGE_SERVICE_URL,
                        files=files,
                        data=data,
                        timeout=60
                    )
            finally:
                # 删除临时文件
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
            
            if response.status_code in [200, 201]:
                result = response.json()
                doc_id = result.get('id', 'N/A')
                print(f"   ✅ 成功 (ID: {doc_id})")
                created += 1
            elif response.status_code == 409:
                print(f"   ⚠️  已存在")
            else:
                print(f"   ❌ 失败: HTTP {response.status_code}")
                if response.text:
                    print(f"      错误信息: {response.text[:200]}")
                failed += 1
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            failed += 1
        
        time.sleep(0.5)  # 避免请求过快
    
    print(f"\n=== 导入完成 ===")
    print(f"✅ 成功: {created}")
    print(f"❌ 失败: {failed}")
    
    return created

def main():
    """主函数"""
    print("=" * 60)
    print("SAP MM知识库文档生成（基于网络知识）")
    print("=" * 60)
    print()
    
    print(f"📚 准备 {len(SAP_MM_DOCUMENTS)} 个SAP MM文档...")
    
    # 导入文档
    created = import_documents(SAP_MM_DOCUMENTS)
    
    if created > 0:
        print(f"\n🎉 成功导入了 {created} 个SAP MM文档！")
        print("\n下一步:")
        print("1. 执行文档向量化（自动）")
        print("2. 建立文档-实体关联: python link_sap_mm_documents.py")
    else:
        print("\n⚠️  未导入任何文档，请检查服务状态")

if __name__ == "__main__":
    main()

