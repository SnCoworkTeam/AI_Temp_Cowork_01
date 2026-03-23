-- 导入项目管理数据
-- 项目数据


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('4a114d7f-e721-4984-8eaf-5ca9e63275a7', '基设信创和202512', '信创和正版化
2024&2025', '来自Sheet: 基设网安', 'active', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('5564f45f-33db-47db-a064-2d2977a9c481', '基设标准化202512', '标准化桌面推广', '来自Sheet: 基设网安', 'active', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('12d6055d-9268-4ae7-bccc-bf73f23b71b5', '基设其他交202512', '其他交办事宜（资产租赁、资产转移等）', '来自Sheet: 基设网安', 'planning', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('3278e570-4105-4fac-8b4f-55f66ad9812c', '基设AI项202512', 'AI项目', '来自Sheet: 基设网安', 'planning', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('672a749c-703b-4892-87a7-d305b4ed6be5', '基设扬州科202512', '扬州科创中心和泰兴基地弱电智能化方案', '来自Sheet: 基设网安', 'planning', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('df04b7c9-0e67-452d-a8fa-e9ebea22697e', '基设蔚蓝行202512', '蔚蓝行动2025', '来自Sheet: 基设网安', 'planning', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('394425d3-cd8f-44f8-9d54-edbddc28af00', '基设中间体202512', '中间体5G网络建设', '来自Sheet: 基设网安', 'active', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('10f7968c-53fa-45c9-8860-2a99ca8314e1', '基设视频A202512', '视频AI应用推广', '来自Sheet: 基设网安', 'active', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('0c5d8eb0-3caa-4ec0-b61a-75f6e8aee5c1', '业务产业链202512', '产业链CRM一期&二期（含物流）', '来自Sheet: 业务经营', 'active', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('6e9cdcf5-f302-4c88-97e2-0ffe5b21b909', '业务总部S202512', '总部SRM优化', '来自Sheet: 业务经营', 'active', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('e06f83d8-394f-46bc-ba68-41db36c378a4', '业务添加剂202512', '添加剂ERP升级', '来自Sheet: 业务经营', 'planning', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('2814b54f-8b75-4c51-8b44-c5229e6bdc15', '业务信用风202512', '信用风险大数据', '来自Sheet: 业务经营', 'active', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('8372e93c-3c5b-4760-a0ae-ab416b512351', '业务南通星202512', '南通星辰项目管理系统', '来自Sheet: 业务经营', 'active', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('2c56aaaf-dc85-42c8-a206-043d70489c5b', '业务博科E202512', '博科ERP 二期优化', '来自Sheet: 业务经营', 'active', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('e18e42cf-ce9b-41a6-aa47-eb049524163e', '业务海波龙202512', '海波龙', '来自Sheet: 业务经营', 'active', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('742f4b75-e54e-48be-a04d-aac4ab474f43', '业务精准维202512', '精准维修', '来自Sheet: 业务经营', 'active', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('3fa3475e-0798-4481-974f-bd7e86e32e28', '业务其他202512', '其他', '来自Sheet: 业务经营', 'active', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('708c2359-c90c-460e-819c-42f7e3afea62', '管理经营计202512', '经营计划求解平台
二期&三期', '来自Sheet: 管理应用', 'active', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('ea19c4ca-d0a0-4f5c-b823-efcc5f1fac6b', '管理统一H202512', '统一HR系统
一期&二期', '来自Sheet: 管理应用', 'active', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('007059ca-30d7-48e4-a38b-face7b242de9', '管理研发和202512', '研发和产业链LIMS', '来自Sheet: 管理应用', 'active', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('2b8d41e7-617b-4a99-bfe8-8d4c35421652', '管理业财穿202512', '业财穿透一体化经营管理平台', '来自Sheet: 管理应用', 'planning', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('a0c3af85-acfc-4963-b444-ab479a285fcf', '管理OA整202512', 'OA整合三期', '来自Sheet: 管理应用', 'planning', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('3e5c7bca-e96a-4343-b459-b562973ae0a0', '管理审计监202512', '审计监督引擎', '来自Sheet: 管理应用', 'planning', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('682b3d0a-af6c-4755-914f-8fdd204dc9b1', '生产化工事202512', '化工事业部：研发管理平台建设（工塑研发检测、高纤研发项目管理）', '来自Sheet: 生产运营', 'planning', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('6063dbaf-e380-434d-905f-c57f8e961244', '生产集团H202512', '集团HSE系统建设2026', '来自Sheet: 生产运营', 'planning', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('0ca3d3b6-5f91-4533-aa80-71eb05a97938', '生产中间体202512', '中间体MES二期&三期：瑞祥&瑞泰', '来自Sheet: 生产运营', 'active', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('ee224945-e3e7-4518-83a9-a10b814f31f5', '生产生产运202512', '生产运营信息系统统一运维体系建设', '来自Sheet: 生产运营', 'planning', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('becd9827-09df-4fbe-85d9-0cb76bbba8dd', '生产霍尼M202512', '霍尼MES优化2026', '来自Sheet: 生产运营', 'planning', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('642b485d-7a5e-499b-bd8e-5688488f4c3d', '生产HSE202512', 'HSE-应用质量提升', '来自Sheet: 生产运营', 'active', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('4e04b576-9974-4a84-9d28-8818b8c0c06b', '生产连云港202512', '连云港储罐智慧管理二期', '来自Sheet: 生产运营', 'active', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('e480a569-4981-483e-a7bf-86deee8a784e', '生产跟踪A202512', '跟踪AI大模型工业应用', '来自Sheet: 生产运营', 'planning', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('8cc6aba4-94d1-4c69-ab02-b1e6b54e8011', '生产应上202512', '【应上尽上】化工事业部 工艺报警系统-总部统筹9家（不跟踪）', '来自Sheet: 生产运营', 'active', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('94119feb-441d-4da7-a200-8c57d01356c8', '生产中化河202512', '中化河北MES系统项目（不跟踪）', '来自Sheet: 生产运营', 'planning', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('9b206bb1-7376-479f-a47c-9890d5db4f27', '生产南通星202512', '南通星辰生产综合管理平台设备与质量建设（下月不跟踪）', '来自Sheet: 生产运营', 'planning', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('0f869d7b-921b-4409-b282-9a8db2fa19af', '瑞恒洪强202512', '洪强', '来自Sheet: 瑞恒基地', 'planning', 'medium', NULL, NULL, 0.0, NULL, '{}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('c97d959e-148a-4966-91cf-295ba6c89af0', 'PRJ-0004', '江苏瑞兆科', '05-N/A', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"reporter": "顾涛", "weekly_reports": [{"week": "五月", "content": "一、项目总体进展\n（一）核心成果\n1. 《AI能力建设项目立项报告》初稿已完成，涵盖需求分析、技术方案及实施规划。\n2. 框架合同附件《场景描述》初稿编制完成。\n\n（二）关键要素\n预算概况：项目整体预估费用38万元（毛估，不含智能会议助手模块）\n实施周期：2-3个月\n\n二、模块分项进展\n1.规章制度智能问答模块\n费用及周期：预估费用8万元，预估实施周期1.5至2个月\n\n2.运维知识问答模块\n费用及周期：预估费用总计15万元（工单系统对接费用+智能体搭建），实施周期1.5至2个月\n\n3.智能会议预定模块\n费用及周期：预估费用15万元（OA系统对接费用+智能体搭建），实施周期2个月"}, {"week": "六月", "content": "上周主要是针对新的5篇规章制度进行的POC验证，明确了AI智能规章制度问答对应学习时间及应用的可行性，测试人张乐敏，已通过验证。\n\n从签约到落地推广预计总工期为2.5个月，具体如下：\n签约-确定合作意向，完成合同签署\n项目部署30天完成知识库内容收集与搭建\nUAT测试15天选定UAT测试对象并协助完成测试，验证系统功能可用性，记录相关测试问题，并及时解决 \n项目试点15天选定试点范围并完成测试，优化系统实际适配性\n推广培训15天配合完成推广与培训，推动系统全面落地应用"}, {"week": "七月", "content": "关于化工事业部智能问答当前进展如下：\n1. 已完成在中化AI平台的生产环境搭建的化工事业部智能问答智能体应用;\n2. 各规章制度共计 357 篇，其中扫描影印件约122篇，已完成全部文档的上传和解析工作;\n3. 本周将进行UAT测试，将由中化信息牵头，与张乐敏等老师针对内容进行逐一测试，记录相关问题进行修正，测试周期预计3周;\n4. 预计整体上线时间点在8月底9月初，届时可进行试点相关工作。"}, {"week": "八月", "content": "目前正在UAT阶段，用户张乐敏正在安排人员测试，暂无实质性进展"}]}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('3130a219-16f7-438c-9adc-fea886e05735', 'PRJ-0003', '宁夏瑞泰', '04-基设网安', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"weekly_reports": [{"week": "四月", "content": "1、腾讯会议：待4月初总部授权后发起腾讯会议询比价采购流程。计划采购：300方会议室*9、1000方会议室*1、企业版账号*100、H.323会议室连接器*10，现官网原价为134580元，具体优惠折扣与供应商谈判后确定。\n2、资产租赁进度：资产租赁进度，已完成资产租赁流程信息收集将需求提供至OA运维组，完成框架协议前期沟通及法务预审"}, {"week": "五月", "content": "1.蔚蓝行动2025前期准备工作启动,根据集团邮件通知,5月初将开始由外部攻击队组织的内部攻防演练,演练标准参照正式演习同步进行\n2.邮件系统切换准备工作启动,根据集团统一规划,启动邮件系统切换准备工作,本周需要完成非HR系统人员邮件账号信息梳理工作,需要各单位全力配合\n3.腾讯会议中化信息内部立项和报价,预计5月底前开通腾讯企业账号\n4.公司网络网络专线优化调整方案,和关总完成汇报,准备网络优化立项报告\n5.SAP HANA测试环境服务器准备,完成中化信息HANA服务器和基础设施服务合同签署"}, {"week": "九月", "content": "SAP HR服务器搬迁"}, {"week": "重要里程碑", "content": "2024/8"}]}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('5c168ab0-df2a-4e7f-8ab7-4d06e2d289cd', 'PRJ-0008', '山东圣奥', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"phase": "03-实施", "reporter": "董俊/陶云飞", "weekly_reports": [{"week": "十二月", "content": "1.中化釜鼎，中化滏恒，中化鑫宝，扬农瑞祥，山东圣奥，泰安圣奥，完成对接和算法优化\n2.安徽圣奥，扬农锦湖，南通星辰和中化高纤启动对接"}, {"week": "一月", "content": "1、中化高纤，扬农锦湖和安徽圣奥，完成AI对接\n2、各对接系统完成调优，与集团AI平台上传稳定正常，春节之前完成"}, {"week": "二月", "content": "各地对接全部完成，各地视频AI持续优化中，有新建工厂可以推广使用事业部统建系统，不再跟踪。"}], "original_status": "02-正常进行"}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('3ac65e32-3295-4a24-86fd-645fb83b10f7', 'PRJ-0006', '圣奥化学', '', 'cancelled', 'medium', NULL, NULL, 0.0, NULL, '{"reporter": "黄亮", "weekly_reports": [{"week": "五月", "content": "前往靶标单位（安徽圣奥）实地检查"}, {"week": "六月", "content": "本周梳理了化工事业部开展内部攻防成果，共发现6家单位（中化国际、中化塑料、宁夏锂电、扬农化工集团、南通星辰、扬州锂电）系统存在漏洞，其中从攻击队资源中成功获取中化国际联想网盘0day漏洞防护方法，并在内网环境中发现域证书服务器存在证书配置漏洞，影响中化国际域控安全包括域内2595台主机。以及其他弱密码及中高危漏洞29个。本周开始通知各单位开始修复漏洞"}]}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('4755cd9b-3a46-4fd9-a91e-39d1dfcef173', 'PRJ-0009', '泰安圣奥', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"phase": "03-实施", "original_status": "3-正常进行"}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('6fdaa9be-7af9-4820-afa5-b1327964606e', 'PRJ-0010', '连云港圣奥', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"phase": "03-实施", "original_status": "3-正常进行"}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('50f7c3cd-57ba-406b-92a1-2738c4f9ec0f', 'PRJ-0012', '南通星辰', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"reporter": "马天明+徐立辉+卢天慧"}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('9a60e0ba-c679-47d6-bc21-38589195c80d', 'PRJ-0016', '中化滏鼎', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"phase": "03-实施", "reporter": "孙沛峰", "weekly_reports": [{"week": "十二月", "content": "其他模块继续开发中"}, {"week": "一月", "content": "管线打开模块这周开始开发，\n统计分析和变更管理随后开发，争取月底前完成"}, {"week": "重要里程碑", "content": "2024-03-01 00:00:00"}], "original_status": "02-正常进行"}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('855a52cd-4fa0-4c7f-8135-d150c6c28b8e', 'PRJ-0017', '中化鑫宝', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"phase": "05-收尾", "reporter": "赵佳", "weekly_reports": [{"week": "十二月", "content": "1. 锦湖设备主数据维保业务等主数据收集并上传至系统；\n2.   SAP、OA相关接口开发；\n3. 网络开通、VPN账号收集、申请。"}, {"week": "一月", "content": "1.SAP、OA相关接口开发\n2.项目试运行"}, {"week": "三月", "content": "项目验收"}], "original_status": "02-正常进行"}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('d018edb6-6374-46d7-9feb-19ebd875fb04', 'PRJ-0018', '中化高纤', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"reporter": "赵佳", "weekly_reports": [{"week": "十二月", "content": "1、主数据已接收ERP推送\n2、培训、练习\n3、中蓝质量数据维护\n4、上线过渡阶段策略沟通\n5、COA报告打印\n1、上线检查清单\n2、上线应急策略\n3、设备模块上线\n4、中蓝质量数据维护"}, {"week": "一月", "content": "1、建立紧急联系机制（电话、微信/微信群），先处理问题后保留问题记录\n2、问题收集，优化建议在线文档\n3、中蓝质量1.6号下午再开展一次培训\n4、用户手册提交用户\n5、正式环境设备模块存在问题需要处理\n6、1~7业务数据补录"}, {"week": "二月", "content": "1、系统上线问题处理\n2、生产、设备、质量相关报表开发"}, {"week": "三月", "content": "1.ERP月末结算价对接\n2.设备工单成本报表继续开发\n3.物料凭证同步，在和化数仓对接"}, {"week": "四月", "content": "1.物料凭证同步，在和化数仓对接完成\n2.验收准备"}, {"week": "五月", "content": "1.验收及转运维阶段"}, {"week": "重要里程碑", "content": "2025-10-15 00:00:00"}]}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('8d4e2284-40b0-4ead-b0cb-1dc5354679da', 'PRJ-0020', '宁波润沃', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"phase": "03-实施", "reporter": "卢天慧", "weekly_reports": [{"week": "五月", "content": "瑞祥：\n1、DCS数据接入的服务器资源协调；\n2、进行项目验收会的前期沟通；\n3、进行基建、电气等设备台账完善\n瑞泰：\n1、进行项目验收会的前期沟通；\n2、进行检修流程优化调整；"}, {"week": "重要里程碑", "content": "瑞祥：2024/6/15\n瑞泰：2024/7/15"}], "original_status": "02-正常进行"}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('8437f2eb-a7a8-4180-9d58-18026c615073', 'PRJ-0021', '扬州锂电', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"phase": "03-实施", "reporter": "姜丽丽/卢天慧", "weekly_reports": [{"week": "五月", "content": "1、进行数据迁移工具开发，预计进展90%；\n2、完成升级方案全量测试；\n3、完成诊断中心数据迁移测试；\n4、进行报警业务数据迁移工具开发，预计进展90%。"}, {"week": "六月", "content": "1、进行系统切换升级方案制定并发布；\n2、进行圣奥化学服务器结构部署调整与新老服务器数据传输；\n3、进行系统正式切换的准备与线上系统培训工作。"}, {"week": "七月", "content": "1、进行系统功能监护运行；\n2、提交上线安全检查材料；"}, {"week": "八月", "content": "1、跟进漏洞修复相关工作。"}, {"week": "重要里程碑", "content": "2025-03-31 00:00:00"}], "original_status": "02-正常进行"}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('971eee5d-6f7c-4c25-b533-2e8e88ffff89', 'PRJ-0022', '淮安骏盛', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"phase": "03-实施", "reporter": "丁翔", "weekly_reports": [{"week": "十二月", "content": "承包商-已完成统建系统的建设，待集团发布标准完成自建系统的数据对接\nBD-已完成所有企业年度任务，核实、上报项目进度\n固废-配合集团调研"}, {"week": "一月", "content": "承包商-已完成统建系统的建设，待集团发布标准完成自建系统的数据对接\nBD-已完成所有企业年度任务，核实、上报项目进度\n固废-配合集团调研，完成基础信息收集表"}, {"week": "二月", "content": "承包商-已完成统建系统的建设，沟通自建系统数据上报事宜\nBD-按照集团要求，和各企业沟通确认2025年建设内容\n固废-配合中化信息进行系统试运行"}, {"week": "三月", "content": "承包商-按照集团计划，推进自建系统数据接入\nBD-按照集团要求，推进系统完善\n固废-配合中化信息进行系统试运行"}, {"week": "四月", "content": "承包商-按照集团计划，推进自建系统数据接入\nBD-按照集团要求，推进系统完善\n固废-配合中化信息进行系统试运行"}, {"week": "五月", "content": "承包商-按照集团计划，推进自建系统数据接入\nBD-按照集团要求，推进系统完善\n固废-配合中化信息进行系统试运行"}, {"week": "六月", "content": "承包商-按照集团计划，推进自建系统数据接入\nBD-按照集团要求，推进系统完善\n固废-配合中化信息进行系统试运行"}, {"week": "七月", "content": "承包商-按照集团计划，推进自建系统数据接入\nBD-按照集团要求，推进系统完善\n固废-关注固废系统正式版运行情况，收集相关问题"}, {"week": "八月", "content": "承包商-按照集团计划，推进自建系统数据接入\nBD-已完成年度计划，不再跟踪\n固废-关注固废系统正式版运行情况，收集相关问题"}, {"week": "九月", "content": "暂不跟踪"}, {"week": "十月", "content": "暂不跟踪"}, {"week": "十一月", "content": "暂不跟踪"}, {"week": "重要里程碑", "content": "2024-05-01 00:00:00"}], "original_status": "02-正常进行"}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('80db9432-84d2-441b-b497-c867a8308b65', 'PRJ-0013', '星辰芮城', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"phase": "04-交付", "reporter": "张志敏", "weekly_reports": [{"week": "十二月", "content": "1、上线检查材料准备；\n2、物料管理流程梳理及集成沟通；\n3、移动审批事项跟进；\n4、HSE接口调试；\n5、PHD扩容事项跟进；\n6、电力系统数据接入事项跟进；\n7、T1、T2会议试用；\n8、上线试运行支持。"}, {"week": "一月", "content": "1、生产成本报表优化；\n2、2025年年计划录入；\n3、卓越运营模块使用推进；\n4、ERP、WMS、事前算赢系统集成推进；\n5、PHD扩容事项跟进；\n6、电力数据接入；\n7、渗透测试、基线检查；\n8、移动端试用及优化；\n9、上线试运行支持。\n1、ERP系统集成推进；\n2、WMS系统集成推进；\n3、事前算赢系统集成推进；\n4、T3会议组态；\n5、电力系统接入推进；\n6、上线试运行支持。"}, {"week": "二月", "content": "1、生产成本功能优化；\n2、卓越运营模块使用推进；\n3、ERP、WMS、OA系统集成推进；\n4、上线前安全检查漏洞修复；\n5、项目剩余事项梳理；\n6、功能清单梳理；\n7、问题清单梳理；\n8、属地汇报准备；\n9、交付物准备；\n10、运维机制建立。"}, {"week": "重要里程碑", "content": "2024-07-04 00:00:00"}], "original_status": "02-正常进行"}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('02c9021f-3555-46ca-84e7-d136aa03b012', 'PRJ-0005', '扬农锦湖', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"reporter": "陶云飞", "weekly_reports": [{"week": "二月", "content": "1.把设计院对中化康源相关设计，提交集团海康和大华集采供应商，获得相关方案和报价\n2.网络和安全设备，比配集团华为集采型号设备和深信服相关报价。"}, {"week": "三月", "content": "1.跟踪科创中心设计情况，配合确定弱电方案\n2.泰兴基地方案讨论"}, {"week": "四月", "content": "1.科创中心设计方案定稿\n2.泰兴基地启动详细设计方案"}, {"week": "五月", "content": "1.科创中心设计方案定稿\n2.泰兴基地启动详细设计方案"}, {"week": "六月", "content": "1.科创中心设计方案定稿"}, {"week": "七月", "content": "1..科创中心设计方案定稿"}, {"week": "八月", "content": "1.科创中心方案提交中化商务招标"}, {"week": "九月", "content": "等待科创中心招标结果后，确定方案"}, {"week": "十月", "content": "泰州基地和科创中心弱电都已经招标，相关修改内容已经告知，等待实施时候再配合供应商和当地IT进行配置和支持"}]}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('d1009270-2263-404c-a39b-0a98cd0b8845', 'PRJ-0007', '安徽圣奥', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"phase": "02-正常进行", "reporter": "陈圣", "weekly_reports": [{"week": "十二月", "content": "1、扬农总部无线网络方案沟通和确认，准备设备采购方案和清单。\n2、瑞泰5G准备合同和单一来源采购申请，连云港瑞恒5G反馈室内不太急，准备现有合同变更。\n3、完成扬农总部网络改造方案审批，准备机房迁移和改造方案"}, {"week": "一月", "content": "1、收集瑞恒5G防爆手机终端数量，完成5G卡的正式发放\n2、完成瑞恒的现有网络改造和中化国际与连云港电信的5G合同签署（瑞恒原合同终止）\n3、瑞泰5G网络完成合同签署，等待供应商备货完成项目实施\n4、与瑞祥5G网络供应商对存在问题的IP地址进行修改和处理，满足交付要求\n5、评估5G网络接入安全风险，对部分5G方案进行安全加固（瑞恒、瑞祥）"}, {"week": "二月", "content": "1、收集瑞恒5G防爆手机终端数量，完成5G卡的正式发放\n2、完成瑞恒的现有网络改造和中化国际与连云港电信的5G合同签署（瑞恒原合同终止）\n3、瑞泰5G网络完成合同签署，等待供应商备货完成项目实施\n4、与瑞祥5G网络供应商对存在问题的IP地址进行修改和处理，满足交付要求\n5、评估5G网络接入安全风险，对部分5G方案进行安全加固（瑞恒、瑞祥）"}, {"week": "三月", "content": "1、收集瑞恒5G防爆手机终端数量，完成5G卡的正式发放（完成)\n2、完成瑞恒的现有网络改造和中化国际与连云港电信的5G合同签署（瑞恒原合同终止)完成\n3、瑞泰5G网络完成合同签署，完成项目实施\n4、完成瑞祥5G网络供应商对存在问题的IP地址进行修改满足交付要求\n5、评估5G网络接入安全风险，对部分5G方案进行安全加固（瑞恒、瑞祥）"}, {"week": "五月", "content": "1.目前在等待开卡测试，在准备走开卡流程"}, {"week": "六月", "content": "已完成"}, {"week": "八月", "content": "已完成"}, {"week": "重要里程碑", "content": "2024-07-20 00:00:00"}], "original_status": "02-正常进行"}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('2abd6d04-c2e8-4284-9477-fc7f1bb7f67c', 'PRJ-0011', '江苏富比亚', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"reporter": "马天明+徐立辉+宋迪+贺荣荣", "weekly_reports": [{"week": "十二月", "content": "编制采购方案\n准备两家候选供应商谈判\n初步计划12-30这周谈判，等待瑞恒领导决策。"}, {"week": "一月", "content": "提交OA采购申请审批流程；\n召开采购谈判会议；\n公示采购结果；"}, {"week": "三月", "content": "探讨建设中间体事业部的先进控制团队。"}, {"week": "四月", "content": "1、瑞恒APC按计划实施；\n2、瑞祥APC按计划实施；\n3、瑞泰APC开展项目可研"}, {"week": "六月", "content": "瑞恒：酚酮装置APC：●●继续开展酚酮车间、环氧丙烷车间和丙烷脱氢车间基础自动化提升工作。●●继续投运调试苯酚精馏塔APC控制器。●●继续投运调试原料苯酚塔APC控制器。●●继续投运调试原料分离塔APC控制器。●●继续投运调试丙酮塔APC控制器。●●搭建异丙苯单元APC控制器。\n瑞祥：软硬件采购和安装；DCS组态编辑；APC建模及组态。\n瑞泰：开展采购寻源。"}, {"week": "重要里程碑", "content": "2025-02-21 00:00:00"}]}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('931ff23f-ac64-436c-825f-9015293f7e33', 'PRJ-0023', '连云港园区（罐区码头）', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"weekly_reports": [{"week": "顾涛", "content": "陈璞"}]}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('553cb673-ae98-4eec-b017-6a0c28808542', 'PRJ-0002', '江苏瑞恒', '03-管理应用', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"phase": "01-准备/可研", "reporter": "陈圣", "weekly_reports": [{"week": "十二月", "content": "1、完成标准化工作的立项审批 (兰海) \n2、继续修改扬农无线网络覆盖点位的方案\n3、桌面标准化总计完成56台设备，本周继续实施"}, {"week": "一月", "content": "1、梳理瑞恒现有办公电脑和IT资产信息，形成办公电脑资产台账\n2、安排网络工程师对现场网络设备进行梳理，形成网络设备台账\n3、根据现场IT资产梳理情况配置运维堡垒机\n4、安排总部桌面工程师前往现场提供桌面标准化实施培训和支持"}, {"week": "三月", "content": "1、开展对生产运营部、设备维保部、纪检部、职业与健康部、综合部、党群部、的电脑标准化工作，同步进行电脑资产台账梳理工作，输出IT资产台账\n2、根据标签规范，对生产运营部、设备维保部、打印黏贴资产标签"}, {"week": "四月", "content": "招采流程正常进行中"}, {"week": "五月", "content": "1.寻源已完成，合同签订中，预计本周合同结束，进厂进行任务计划排布。总共约450台，计划每天至少完成10台\n2.于扬农集团领导沟通合同签署问题"}, {"week": "六月", "content": "持续实施中"}, {"week": "七月", "content": "下周继续实施，整体计划不变，南通星辰7月底完成，扬农8月底完成"}, {"week": "八月", "content": "1、南通星辰：对剩余请休假、出差的用户电脑进行陆续补充实施\n2、扬农按原计划继续实施"}, {"week": "九月", "content": "1、开始做文件服务器迁移的准备工作"}, {"week": "重要里程碑", "content": "2024/8"}], "original_status": "02-正常进行"}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('95372a85-07fc-4547-8b3e-7150dc978975', 'PRJ-0029', 'N/A', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"weekly_reports": [{"week": "顾涛", "content": "姚晓龙"}]}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('0f20a971-b51b-4773-ab71-e08691ee7d68', 'PRJ-0014', '扬州ABS', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"phase": "03-实施", "reporter": "姜丽丽", "weekly_reports": [{"week": "十二月", "content": "商务部分：\n1、芮城支付软件费用\n2、霍尼韦尔软件支付准备\n属地准备：\n1、芮城：推进网闸采购工作\n2、添加剂：\n   安徽圣奥：12.3计划组织用户培训\n   山东圣奥：报警点位组态，层级组态，权限配置\n   泰安圣奥：报警点位组态，层级组态，权限配置\n   富比亚：软件授权采购谈判\n   淮河化工：报警点位组态，层级组态，权限配置\n   河北三家：网闸，服务器，授权采购中，预计12.10到货\n3、事业部：\n1、推进多因子集成开发\n2、芮城网页访问测试"}, {"week": "一月", "content": "属地准备：\n   安徽圣奥：用户上线试用，部分乱码显示乱问问题正在处理\n   山东圣奥：用户上线试用\n   泰安圣奥：用户上线试用\n   富比亚： 用户上线试用，用户现场培训\n   淮河化工：用户上线试用\n   芮城：用户试用中，用户无法登录多因子，联系配置\n   河北三家：用户试用中，数据采集核对，报警点位整理及优化\n事业部：\n1、上线前测试，基础架构团队负责，目前已提交所有材料，测试预计一周\n2、上线报告准备审查\n3、各家提供报警优先级对应关系"}, {"week": "重要里程碑", "content": "2024-08-01 00:00:00"}], "original_status": "02-正常进行"}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('d3a57d0c-9692-493b-a0df-aa634da5c727', 'PRJ-0024', '淮河化工', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"weekly_reports": [{"week": "顾涛", "content": "马天明"}]}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('f1277119-8f97-4810-9d43-441236cafe05', 'PRJ-0025', '中卫锂电', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"weekly_reports": [{"week": "顾涛", "content": "丁骞"}]}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('5c4cf2b3-dc97-4c1c-8d52-83274ac0eec5', 'PRJ-0026', '中化国际', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"weekly_reports": [{"week": "顾涛", "content": "梁诚"}]}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('a13acb78-58fd-451b-9cf7-cb5e266c13d7', 'PRJ-0027', '产业资源', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"weekly_reports": [{"week": "顾涛", "content": "黄云"}]}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('a926e889-469c-4b37-9841-178f7ab83f6f', 'PRJ-0028', '科创中心', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"weekly_reports": [{"week": "顾涛", "content": "丁翔"}]}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('fc05067c-a99d-4a30-97d5-38f047e3b9ef', 'PRJ-0001', '马天明', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"phase": "01-准备/可研", "reporter": "陈圣", "weekly_reports": [{"week": "十二月", "content": "1、完成剩余条线的信创工作计划和等保情况说明。\n2、完成2024年信创改造立项报告审批，并启动相关工作\n3、完成2024年第四季度信创工作总结，提交兰总审批"}, {"week": "一月", "content": "1、持续跟踪信创合同审批流程\n2、持续跟踪AspenPlus软件立项流程审批情况"}, {"week": "三月", "content": "1，评估碳管家系统信创服务器资源的费用，与供应商协商压降实施费用\n2，评估EAM系统信创服务器资源的费用以及改造实施的费用\n3，梳理出加密软件服务器资源清单并计算出资源费用"}, {"week": "四月", "content": "待关总审阅后发起立项流程"}, {"week": "五月", "content": "与兰总对信创改造工作的报价进行优化讨论,确定2025年信创立项方案"}, {"week": "六月", "content": "起草合同初稿"}, {"week": "七月", "content": "4个系统信创改造持续推进，汇报服务器资源申请情况和信创软件部署情况"}, {"week": "八月", "content": "4个系统信创改造持续推进中"}, {"week": "九月", "content": "1、网盘提交服务器资源申请流程\n2、信用风险大数据：针对查询慢的功能点进行优化\n3、碳管家：开展信创生产环境迁移，对信创生产环境与现有生产环境数据核对。"}], "original_status": "02-正常进行"}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('da24b04f-9d2f-408b-af24-d4475bba5313', 'PRJ-0015', '中化滏恒', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"phase": "02-寻源", "reporter": "孙沛峰", "weekly_reports": [{"week": "十二月", "content": "1、 质量原始记录模版组态\n2、物料管理的组态\n3、 能源管理组态\n4、用户台账测试\n5、 产品出厂流程测试\n6、滏鼎报警事件数据采集测试"}, {"week": "一月", "content": "1、装置计量组态，能源管理组态，下周完成\n2、设备动态监视，安装完成，系统组态调试\n3、色谱仪数据采集调试\n4、HSE接口调试，上周未完成工作\n5、地磅接口调试，上周未完成工作\n6、Uniformance insight 动态图更新。\n7、质检模块试运行（全数据录入）\n8、多因子登录mes测试"}, {"week": "二月", "content": "系统测试"}, {"week": "三月", "content": "1、采购到厂：自动同步SAP，采购订单，按照实际业务创建到厂计划\n2、产品发货：自动同步SAP外向交货单，按照实际业务创建到厂计划\n3、生产排程：自动同步SAP生产订单，每天按照实际业务备货，排程\n4、生产任务执行：每天按照实际生产订订单下线量，贴码，扫码。\n5、产品入库：每天按照实际业务确认产品入库数量\n6、产品拣配：桶装扫码发货，其他按照数量发货\n7、质量检验：原料自动触发送检、质量检验；产品发货自动送检，生成COA；生产下线自动送检，产品检验\n8、交接班日志：初馏、精制、仓管每班填写交接班日志\n9、装置计量：每班确认装置计量消耗和库存数据，每班提交\n10、能源计量：每班填写能源计量数据"}, {"week": "四月", "content": "继续对各功能模块进行实操并收集发现的问题及时处置。做好问题跟踪，继续优化进出厂流程"}, {"week": "重要里程碑", "content": "2024-08-15 00:00:00"}], "original_status": "03-实施"}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('fead739a-d955-480a-a304-3e5d2c1f60a0', 'PRJ-0019', '成都新材', '', 'active', 'medium', NULL, NULL, 0.0, NULL, '{"phase": "04-交付", "reporter": "卢天慧", "weekly_reports": [{"week": "十二月", "content": "1、提交立项审批流程，并约供应商进行价格谈判。"}, {"week": "一月", "content": "瑞祥：1、进行移动端的测试；2、进行第二轮系统培训\n瑞泰：1、进行VPN申请；2、进行系统培训\n总体：采购谈判"}, {"week": "三月", "content": "瑞恒：\n1、准备剩余模块的上线工作；\n2、调研委外检修流程在OA审批还是在EAM审批的相关需求；\n3、明确完成时间。\n瑞祥：\n1、推进系统功能上线运行\n2、专项设备、特种设备台账导入、检定计划制定\n3、台账、ITPM计划等各基础资料新增及更新\n4、进行固资台账绑定设备台账导入\n5、密封腐蚀台账完善导入，腐蚀计划制定\n瑞泰：\n1、推进点检标准完善，推进系统功能上线；\n3、电气相关功能沟通、制定电气相关业务审批流 ；\n3、进行固资台账绑定设备台账导入；\n4、缺陷管理、检修计划、风险管理模块与清云系统业务如何切割需要进行讨论；\n5、组织集团确定报警区分方式；\n6、讨论固定资产与SAP集成的需求；\n圣奥：\n1、进行商务合同相关流程；\n2、技术协议进行最终确认。"}, {"week": "四月", "content": "瑞恒：\n1、确认项目验收交付文档；\n2、沟通建立系统运维机制；\n瑞祥：\n1、推进系统功能上线运行；\n2、风险管理功能模块推进上线使用；\n3、进行OPC数据接入；\n瑞泰：\n1、压力容器，压力管道检验计划全面启动上线运行；\n2、进行每日执行数据情况统计（PPM+检修）\n3、风险管理功能持续推进上线使用；\n圣奥：\n1、开展项目启动会。"}, {"week": "五月", "content": "1、完善各模块流程制度，点检标准、润滑标准要求明确，车间主任签字确认，指定人员进行周期性检查，根据情况进行考核；\n2、进行项目验收会的前期沟通。"}, {"week": "重要里程碑", "content": "2024-04-15 00:00:00"}], "original_status": "02-正常进行"}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();

-- 任务数据


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('7f0c99f6-dc8e-4207-b90f-5c45ef484baf', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '待办事项: 正版化发现安装盗版软件问题，要将违规人员通报相关主管领导，信创方案确认是否需要完成5个项目，尽快落实', '正版化发现安装盗版软件问题，要将违规人员通报相关主管领导，信创方案确认是否需要完成5个项目，尽快落实后续的项目的确认（设备管理系统）统计可能采购需求', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('3cfafdd3-a828-4d8c-bff2-0895bfff62eb', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '十二月: 1、完成剩余条线的信创工作计划和等保情况说明。
2、完成2024年信创改造立项报告审批，并启动相关工', '1、完成剩余条线的信创工作计划和等保情况说明。
2、完成2024年信创改造立项报告审批，并启动相关工作
3、完成2024年第四季度信创工作总结，提交兰总审批', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('5e22b512-f978-4926-bd0f-53bbf8de4439', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '一月: 1、持续跟踪信创合同审批流程
2、持续跟踪AspenPlus软件立项流程审批情况', '1、持续跟踪信创合同审批流程
2、持续跟踪AspenPlus软件立项流程审批情况', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ca995fb1-ec68-445a-b27c-c3c3a7114a7b', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '三月: 1，评估碳管家系统信创服务器资源的费用，与供应商协商压降实施费用
2，评估EAM系统信创服务器资源的', '1，评估碳管家系统信创服务器资源的费用，与供应商协商压降实施费用
2，评估EAM系统信创服务器资源的费用以及改造实施的费用
3，梳理出加密软件服务器资源清单并计算出资源费用', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9906d5f0-09e5-49f0-8f54-218c8d62abd4', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '四月: 待关总审阅后发起立项流程', '待关总审阅后发起立项流程', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('c9ee74a8-c5b7-4fc9-9a38-54b3eb2bebaf', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '五月: 与兰总对信创改造工作的报价进行优化讨论,确定2025年信创立项方案', '与兰总对信创改造工作的报价进行优化讨论,确定2025年信创立项方案', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d9f7744c-7947-49f7-972d-b80554df1866', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '六月: 起草合同初稿', '起草合同初稿', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('97146e27-bbec-4a0a-9349-287568e16fbe', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '七月: 4个系统信创改造持续推进，汇报服务器资源申请情况和信创软件部署情况', '4个系统信创改造持续推进，汇报服务器资源申请情况和信创软件部署情况', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('cabb54db-bd31-4c6b-b815-a8c64fd03874', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '八月: 4个系统信创改造持续推进中', '4个系统信创改造持续推进中', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('145c2ad6-d558-419f-bb16-a329e84c7dc6', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '九月: 1、网盘提交服务器资源申请流程
2、信用风险大数据：针对查询慢的功能点进行优化
3、碳管家：开展信创', '1、网盘提交服务器资源申请流程
2、信用风险大数据：针对查询慢的功能点进行优化
3、碳管家：开展信创生产环境迁移，对信创生产环境与现有生产环境数据核对。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('c8c29634-f4f7-4998-8cb0-07f75ef5e64f', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '待办事项: 工单系统包含标准化运维服务', '工单系统包含标准化运维服务', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('15803030-9a05-4e6d-a1b6-39ee402d3416', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '十二月: 1、完成标准化工作的立项审批 (兰海) 
2、继续修改扬农无线网络覆盖点位的方案
3、桌面标准化总计', '1、完成标准化工作的立项审批 (兰海) 
2、继续修改扬农无线网络覆盖点位的方案
3、桌面标准化总计完成56台设备，本周继续实施', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9370db0b-272e-4e33-98fd-ea1ec1fc3d18', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '一月: 1、梳理瑞恒现有办公电脑和IT资产信息，形成办公电脑资产台账
2、安排网络工程师对现场网络设备进行梳', '1、梳理瑞恒现有办公电脑和IT资产信息，形成办公电脑资产台账
2、安排网络工程师对现场网络设备进行梳理，形成网络设备台账
3、根据现场IT资产梳理情况配置运维堡垒机
4、安排总部桌面工程师前往现场提供桌面标准化实施培训和支持', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('2d5a71e2-8fbe-499b-88e3-454233a9957e', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '三月: 1、开展对生产运营部、设备维保部、纪检部、职业与健康部、综合部、党群部、的电脑标准化工作，同步进行电', '1、开展对生产运营部、设备维保部、纪检部、职业与健康部、综合部、党群部、的电脑标准化工作，同步进行电脑资产台账梳理工作，输出IT资产台账
2、根据标签规范，对生产运营部、设备维保部、打印黏贴资产标签', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('578dad31-2437-433f-add4-085c94df154b', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '四月: 招采流程正常进行中', '招采流程正常进行中', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9cb7f676-d3a8-4506-9211-4f2709661bc1', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '五月: 1.寻源已完成，合同签订中，预计本周合同结束，进厂进行任务计划排布。总共约450台，计划每天至少完成', '1.寻源已完成，合同签订中，预计本周合同结束，进厂进行任务计划排布。总共约450台，计划每天至少完成10台
2.于扬农集团领导沟通合同签署问题', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('2f3e3a2d-3d28-4f2e-8535-392036d7ea5e', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '六月: 持续实施中', '持续实施中', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('38a03e23-2460-49a5-b574-5fc34bc85e33', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '七月: 下周继续实施，整体计划不变，南通星辰7月底完成，扬农8月底完成', '下周继续实施，整体计划不变，南通星辰7月底完成，扬农8月底完成', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('210e53e3-5f23-45bc-9841-d99ba797c47c', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '八月: 1、南通星辰：对剩余请休假、出差的用户电脑进行陆续补充实施
2、扬农按原计划继续实施', '1、南通星辰：对剩余请休假、出差的用户电脑进行陆续补充实施
2、扬农按原计划继续实施', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('62a5a7ab-0b0e-467e-8ceb-f67e076c8ccf', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '九月: 1、开始做文件服务器迁移的准备工作', '1、开始做文件服务器迁移的准备工作', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('63f99d14-597f-44c0-8b13-49123dfeeb53', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '重要里程碑: 2024/8', '2024/8', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a7739a19-7c54-43dc-914b-417a3e9ca2e9', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '待办事项: 瑞泰网络情况梳理；标准化工作调研摸底（高纤、锦湖）；移动套餐评估；连云港机房消防；AI;圣奥HSE协', '瑞泰网络情况梳理；标准化工作调研摸底（高纤、锦湖）；移动套餐评估；连云港机房消防；AI;圣奥HSE协议变更;', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('1bccf3f4-dbac-43db-bcd1-485dc024511e', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '待办事项: 建议不作为靶标单位', '建议不作为靶标单位', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('3e614899-ccae-4ea0-bede-4369ed1b172e', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '五月: 前往靶标单位（安徽圣奥）实地检查', '前往靶标单位（安徽圣奥）实地检查', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('7005b462-1b90-4332-a7ba-fd94b3861871', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '四月: 1、腾讯会议：待4月初总部授权后发起腾讯会议询比价采购流程。计划采购：300方会议室*9、1000方', '1、腾讯会议：待4月初总部授权后发起腾讯会议询比价采购流程。计划采购：300方会议室*9、1000方会议室*1、企业版账号*100、H.323会议室连接器*10，现官网原价为134580元，具体优惠折扣与供应商谈判后确定。
2、资产租赁进度：资产租赁进度，已完成资产租赁流程信息收集将需求提供至OA运维组，完成框架协议前期沟通及法务预审', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('8292e0eb-1af9-4136-a79c-aa9d82468490', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '五月: 1.蔚蓝行动2025前期准备工作启动,根据集团邮件通知,5月初将开始由外部攻击队组织的内部攻防演练,', '1.蔚蓝行动2025前期准备工作启动,根据集团邮件通知,5月初将开始由外部攻击队组织的内部攻防演练,演练标准参照正式演习同步进行
2.邮件系统切换准备工作启动,根据集团统一规划,启动邮件系统切换准备工作,本周需要完成非HR系统人员邮件账号信息梳理工作,需要各单位全力配合
3.腾讯会议中化信息内部立项和报价,预计5月底前开通腾讯企业账号
4.公司网络网络专线优化调整方案,和关总完成汇报,准备网络优化立项报告
5.SAP HANA测试环境服务器准备,完成中化信息HANA服务器和基础设施服务合同签署', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('b43bb182-29d7-4fa8-8cb1-c6472609b8ac', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '九月: SAP HR服务器搬迁', 'SAP HR服务器搬迁', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('067a92a0-8cf9-4239-b0b6-bddc44ab809f', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '重要里程碑: 2024/8', '2024/8', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('f81d303e-957b-472f-965f-a4577b0dcc79', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '待办事项: 10月20日周会更新系统应用成果', '10月20日周会更新系统应用成果', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('885e91eb-ef90-480c-a5ef-52c1235f9052', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '五月: 一、项目总体进展
（一）核心成果
1. 《AI能力建设项目立项报告》初稿已完成，涵盖需求分析、技术方', '一、项目总体进展
（一）核心成果
1. 《AI能力建设项目立项报告》初稿已完成，涵盖需求分析、技术方案及实施规划。
2. 框架合同附件《场景描述》初稿编制完成。

（二）关键要素
预算概况：项目整体预估费用38万元（毛估，不含智能会议助手模块）
实施周期：2-3个月

二、模块分项进展
1.规章制度智能问答模块
费用及周期：预估费用8万元，预估实施周期1.5至2个月

2.运维知识问答模块
费用及周期：预估费用总计15万元（工单系统对接费用+智能体搭建），实施周期1.5至2个月

3.智能会议预定模块
费用及周期：预估费用15万元（OA系统对接费用+智能体搭建），实施周期2个月', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('50f429d5-30a0-4b6e-a469-a42820fab69f', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '六月: 上周主要是针对新的5篇规章制度进行的POC验证，明确了AI智能规章制度问答对应学习时间及应用的可行性', '上周主要是针对新的5篇规章制度进行的POC验证，明确了AI智能规章制度问答对应学习时间及应用的可行性，测试人张乐敏，已通过验证。

从签约到落地推广预计总工期为2.5个月，具体如下：
签约-确定合作意向，完成合同签署
项目部署30天完成知识库内容收集与搭建
UAT测试15天选定UAT测试对象并协助完成测试，验证系统功能可用性，记录相关测试问题，并及时解决 
项目试点15天选定试点范围并完成测试，优化系统实际适配性
推广培训15天配合完成推广与培训，推动系统全面落地应用', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('f9713d50-d9b0-4f40-8d44-b5c048c4e3ae', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '七月: 关于化工事业部智能问答当前进展如下：
1. 已完成在中化AI平台的生产环境搭建的化工事业部智能问答智', '关于化工事业部智能问答当前进展如下：
1. 已完成在中化AI平台的生产环境搭建的化工事业部智能问答智能体应用;
2. 各规章制度共计 357 篇，其中扫描影印件约122篇，已完成全部文档的上传和解析工作;
3. 本周将进行UAT测试，将由中化信息牵头，与张乐敏等老师针对内容进行逐一测试，记录相关问题进行修正，测试周期预计3周;
4. 预计整体上线时间点在8月底9月初，届时可进行试点相关工作。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ae4b6b82-e6cc-409c-b864-feeaf6be88e8', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '八月: 目前正在UAT阶段，用户张乐敏正在安排人员测试，暂无实质性进展', '目前正在UAT阶段，用户张乐敏正在安排人员测试，暂无实质性进展', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('bb107291-fbec-486b-9607-4c66353fb760', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '待办事项: 抓紧补充计划及沟通难点，跟踪反馈结果', '抓紧补充计划及沟通难点，跟踪反馈结果', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a159568f-2fc1-483e-a65a-2560a7a58fe0', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '二月: 1.把设计院对中化康源相关设计，提交集团海康和大华集采供应商，获得相关方案和报价
2.网络和安全设备', '1.把设计院对中化康源相关设计，提交集团海康和大华集采供应商，获得相关方案和报价
2.网络和安全设备，比配集团华为集采型号设备和深信服相关报价。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('e9fd8e90-a0a5-4c2e-8039-9bc750630837', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '三月: 1.跟踪科创中心设计情况，配合确定弱电方案
2.泰兴基地方案讨论', '1.跟踪科创中心设计情况，配合确定弱电方案
2.泰兴基地方案讨论', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('f5fc781b-c3c7-4158-b64f-ea5fce17267f', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '四月: 1.科创中心设计方案定稿
2.泰兴基地启动详细设计方案', '1.科创中心设计方案定稿
2.泰兴基地启动详细设计方案', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('23c428c2-0584-4cf6-ab9d-af9d8ada6493', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '五月: 1.科创中心设计方案定稿
2.泰兴基地启动详细设计方案', '1.科创中心设计方案定稿
2.泰兴基地启动详细设计方案', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ece80e1e-3162-4442-a984-7736e6489038', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '六月: 1.科创中心设计方案定稿', '1.科创中心设计方案定稿', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('60cc8bc9-4644-4662-a365-055c0a187ec1', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '七月: 1..科创中心设计方案定稿', '1..科创中心设计方案定稿', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('f00c5b62-b338-4429-aab7-ba9f3d7944d0', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '八月: 1.科创中心方案提交中化商务招标', '1.科创中心方案提交中化商务招标', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('7a173e6f-936e-4570-8680-1426b29efae8', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '九月: 等待科创中心招标结果后，确定方案', '等待科创中心招标结果后，确定方案', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('8b46ff7f-0c01-4b51-a7f2-c0abff6d6702', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '十月: 泰州基地和科创中心弱电都已经招标，相关修改内容已经告知，等待实施时候再配合供应商和当地IT进行配置和', '泰州基地和科创中心弱电都已经招标，相关修改内容已经告知，等待实施时候再配合供应商和当地IT进行配置和支持', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('3a375388-1ed9-4219-9b5a-ec7309497076', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '六月: 本周梳理了化工事业部开展内部攻防成果，共发现6家单位（中化国际、中化塑料、宁夏锂电、扬农化工集团、南', '本周梳理了化工事业部开展内部攻防成果，共发现6家单位（中化国际、中化塑料、宁夏锂电、扬农化工集团、南通星辰、扬州锂电）系统存在漏洞，其中从攻击队资源中成功获取中化国际联想网盘0day漏洞防护方法，并在内网环境中发现域证书服务器存在证书配置漏洞，影响中化国际域控安全包括域内2595台主机。以及其他弱密码及中高危漏洞29个。本周开始通知各单位开始修复漏洞', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('8b1f4a39-8fcc-4773-ae35-466a9f4a584c', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '待办事项: 保障瑞恒EAM正常上线', '保障瑞恒EAM正常上线', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('4109a217-f59b-4952-94e6-62a62c8c9f60', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '十二月: 1、扬农总部无线网络方案沟通和确认，准备设备采购方案和清单。
2、瑞泰5G准备合同和单一来源采购申请', '1、扬农总部无线网络方案沟通和确认，准备设备采购方案和清单。
2、瑞泰5G准备合同和单一来源采购申请，连云港瑞恒5G反馈室内不太急，准备现有合同变更。
3、完成扬农总部网络改造方案审批，准备机房迁移和改造方案', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('8ce0572e-9461-42f5-a9c3-7715c036b881', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '一月: 1、收集瑞恒5G防爆手机终端数量，完成5G卡的正式发放
2、完成瑞恒的现有网络改造和中化国际与连云港', '1、收集瑞恒5G防爆手机终端数量，完成5G卡的正式发放
2、完成瑞恒的现有网络改造和中化国际与连云港电信的5G合同签署（瑞恒原合同终止）
3、瑞泰5G网络完成合同签署，等待供应商备货完成项目实施
4、与瑞祥5G网络供应商对存在问题的IP地址进行修改和处理，满足交付要求
5、评估5G网络接入安全风险，对部分5G方案进行安全加固（瑞恒、瑞祥）', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('4ea1e75a-1f48-487f-965b-f55413507a03', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '二月: 1、收集瑞恒5G防爆手机终端数量，完成5G卡的正式发放
2、完成瑞恒的现有网络改造和中化国际与连云港', '1、收集瑞恒5G防爆手机终端数量，完成5G卡的正式发放
2、完成瑞恒的现有网络改造和中化国际与连云港电信的5G合同签署（瑞恒原合同终止）
3、瑞泰5G网络完成合同签署，等待供应商备货完成项目实施
4、与瑞祥5G网络供应商对存在问题的IP地址进行修改和处理，满足交付要求
5、评估5G网络接入安全风险，对部分5G方案进行安全加固（瑞恒、瑞祥）', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('7b3f76ca-0588-4d95-93a7-cbaa8db814c3', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '三月: 1、收集瑞恒5G防爆手机终端数量，完成5G卡的正式发放（完成)
2、完成瑞恒的现有网络改造和中化国际', '1、收集瑞恒5G防爆手机终端数量，完成5G卡的正式发放（完成)
2、完成瑞恒的现有网络改造和中化国际与连云港电信的5G合同签署（瑞恒原合同终止)完成
3、瑞泰5G网络完成合同签署，完成项目实施
4、完成瑞祥5G网络供应商对存在问题的IP地址进行修改满足交付要求
5、评估5G网络接入安全风险，对部分5G方案进行安全加固（瑞恒、瑞祥）', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('6b892ce0-1955-401c-99ff-df728b58c0de', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '五月: 1.目前在等待开卡测试，在准备走开卡流程', '1.目前在等待开卡测试，在准备走开卡流程', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('7389c5aa-8cc1-4a16-8632-302470daa5ed', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '六月: 已完成', '已完成', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d5ea9d8c-dc36-47d4-aefd-28baaf9100be', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '八月: 已完成', '已完成', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('dd4ab7b7-0e9c-4292-8a70-d861031af1ea', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '重要里程碑: 2024-07-20 00:00:00', '2024-07-20 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('4eec4277-31fc-426b-8609-ce702e7a382b', '5c168ab0-df2a-4e7f-8ab7-4d06e2d289cd', NULL, NULL, '十二月: 1.中化釜鼎，中化滏恒，中化鑫宝，扬农瑞祥，山东圣奥，泰安圣奥，完成对接和算法优化
2.安徽圣奥，扬', '1.中化釜鼎，中化滏恒，中化鑫宝，扬农瑞祥，山东圣奥，泰安圣奥，完成对接和算法优化
2.安徽圣奥，扬农锦湖，南通星辰和中化高纤启动对接', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('6c8f2e29-5a2c-49aa-ac9c-effb8e9458d8', '5c168ab0-df2a-4e7f-8ab7-4d06e2d289cd', NULL, NULL, '一月: 1、中化高纤，扬农锦湖和安徽圣奥，完成AI对接
2、各对接系统完成调优，与集团AI平台上传稳定正常，', '1、中化高纤，扬农锦湖和安徽圣奥，完成AI对接
2、各对接系统完成调优，与集团AI平台上传稳定正常，春节之前完成', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('06b4c51a-89d8-4d29-8eda-c0cfe592af1d', '5c168ab0-df2a-4e7f-8ab7-4d06e2d289cd', NULL, NULL, '二月: 各地对接全部完成，各地视频AI持续优化中，有新建工厂可以推广使用事业部统建系统，不再跟踪。', '各地对接全部完成，各地视频AI持续优化中，有新建工厂可以推广使用事业部统建系统，不再跟踪。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('c61e8e5a-8876-472f-b706-e244a45f3186', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '待办事项: 补充AI的情况', '补充AI的情况', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('b76ed081-8971-4f55-8603-f5d4d5f811ed', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '十二月: 1.环氧产业链二期功能开发、用户UAT测试以及瑞恒锦湖上线试运行支持
2.工塑产业链二期功能开发以及', '1.环氧产业链二期功能开发、用户UAT测试以及瑞恒锦湖上线试运行支持
2.工塑产业链二期功能开发以及用户UAT测试
3.中化高纤上线支持
4.淮化上线切换
5.中化河北功能实施
6.中间体功能实施', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ecee4644-3a4c-49ed-89c2-5a6cf0a16743', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '一月: 1.环氧产业链二期功能开发、数据补录，上线切换
2.工塑产业链二期功能开发、数据补录，上线切换
3.', '1.环氧产业链二期功能开发、数据补录，上线切换
2.工塑产业链二期功能开发、数据补录，上线切换
3.中化高纤上线支持
4.淮化上线支持
5.中化河北一期功能上线支持
6.完成中间体项目合同签署，系统功能建设（销售合同对接）
7.预计1月中旬，进行添加剂事业部CRM需求调研，梳理初步方案
8.预计1月中旬，进行CRM等保定级相关事项', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d086a28c-3434-42df-b1e4-ecec34263a10', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '二月: 1.环氧产业链上线支持
2.工塑产业链上线试运行支持
3.中化高纤上线支持
4.淮化上线支持
5.中', '1.环氧产业链上线支持
2.工塑产业链上线试运行支持
3.中化高纤上线支持
4.淮化上线支持
5.中化河北完成一期功能上线试运行支持
6.南通星辰CRM物流功能优化项目上线试运行支持
7.准备系统上线安全材料', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('16577658-3bcb-4fcf-9200-80508de8a28b', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '九月: 上周，我们识别出了存在查询速度缓慢问题的功能点。本周，我们正式针对这些功能点展开优化工作 。', '上周，我们识别出了存在查询速度缓慢问题的功能点。本周，我们正式针对这些功能点展开优化工作 。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('c34ef888-eec7-403e-9786-0f73f4538a03', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '三月: 1.环氧产业链上线支持
2.工塑产业链上线试运行支持
3.中化高纤上线支持
4.淮化上线支持
5.中', '1.环氧产业链上线支持
2.工塑产业链上线试运行支持
3.中化高纤上线支持
4.淮化上线支持
5.中化河北上线支持
6.中间体系统功能搭建：销售合同接口;库存对接库位方案沟通;日报、周报表系统表单建设
7.南通星辰CRM物流功能优化项目上线试运行支持(线上手工单功能开发、业务冲销功能开发)
8.圣奥CRM需求方案内部沟通
9.提交化工事业部1立项材料', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('63629862-2225-425c-9b75-0bca3dd8450f', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '四月: 1.环氧产业链上线支持
2.工塑产业链上线试运行支持
3.中化高纤上线支持
4.淮化上线支持
5.中', '1.环氧产业链上线支持
2.工塑产业链上线试运行支持
3.中化高纤上线支持
4.淮化上线支持
5.中化河北上线支持
6.中间体系统功能切换上线（MDM接口集成暂停，等待MDM资源。）
7.南通星辰CRM物流功能优化项目上线试运行支持(业务冲销功能测试)
2025年CRM需求进展：
8.进行中化河北二期需求评估
9.进行环氧产业链的三期需求评估
10.圣奥CRM方案按照张浩总要求更新。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('924ead28-ce15-4724-8839-dfed30eb764a', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '五月: 1上线支持
2.中间体系统功能切换上线（MDM接口集成暂停，等待MDM资源。）
2025年CRM需求', '1上线支持
2.中间体系统功能切换上线（MDM接口集成暂停，等待MDM资源。）
2025年CRM需求进展：
3.圣奥CRM方案汇报，确认项目范围
4.瑞恒物流方案材料准备，预计中旬进行方案汇报确认
5.完成2025年化工事业部CRM项目立项材料初稿', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9bfe9d36-c7e1-4291-8dae-d546ddd8e76d', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '六月: 1上线支持
2025年CRM需求进展：
2.圣奥CRM方案汇报
3.锦湖物流调度系统功能演示
4.完', '1上线支持
2025年CRM需求进展：
2.圣奥CRM方案汇报
3.锦湖物流调度系统功能演示
4.完成2025年化工事业部CRM项目立项材料
5.CRM与电商集成方案对接', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ac9af8b9-5dd3-4972-9049-49914e78f5d7', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '七月: 1上线支持
2.中间体合同变更事项推进
2025年CRM需求进展：
3.圣奥CRM细节需求调研以及蓝', '1上线支持
2.中间体合同变更事项推进
2025年CRM需求进展：
3.圣奥CRM细节需求调研以及蓝图编制
4.锦湖物流调度系统功能演示，待环氧树脂事业部储运部协调确认时间
5.CRM与电商集成建设
6.瑞恒TMS系统建设，、预约一卡通接口集成
7.立项材料调整（周一完成）', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('22f4c4e0-da52-4776-84f0-20f0d8bd5300', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '八月: 1上线支持
2025年CRM需求进展：
3.圣奥CRM系统建设
4.瑞恒TMS系统上线试运行
5.锦', '1上线支持
2025年CRM需求进展：
3.圣奥CRM系统建设
4.瑞恒TMS系统上线试运行
5.锦湖TMS方案跟进
6.中化高纤上线支持
7.中间体TMS方案，与中间体沟通后续如何推进方案评估
8.立项申请审批', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a67718a3-f90c-49c5-ab17-2337037cf700', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '九月: 1.2024年项目上线支持
2025年CRM需求进展：
2.圣奥CRM集成测试以及完成蓝图确认
3.', '1.2024年项目上线支持
2025年CRM需求进展：
2.圣奥CRM集成测试以及完成蓝图确认
3.瑞恒TMS系统上线试运行，问题整改（完成与一卡通集成相关问题整改，推动瑞恒双酚A业务切换上线）
4.中化高纤上线支持
5.CRM基线安全检查，问题整改
6.中化河北项目启动准备', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('7e98ed66-f233-468c-bca3-0f7065b1cdb0', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '十一月: 1.2024年项目上线支持
2025年CRM需求进展：
2.圣奥CRM上线支持
3.瑞恒TMS系统上', '1.2024年项目上线支持
2025年CRM需求进展：
2.圣奥CRM上线支持
3.瑞恒TMS系统上线支持
4.中化高纤上线支持
5.环氧CRM优化项目合同签署
6.中化河北项目细致需求调研
7.锦湖TMS项目展开业务细致调研
8.工塑CRM合同签署，AI功能沟通', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('128b3f6a-96ac-49d6-8760-539ed1d45b2b', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '十二月: 2025年CRM项目进展：
1.圣奥CRM上线支持
2.瑞恒TMS系统上线支持
3.中化高纤上线支持', '2025年CRM项目进展：
1.圣奥CRM上线支持
2.瑞恒TMS系统上线支持
3.中化高纤上线支持
4.中化河北功能单元测试
5.锦湖TMS项目与SAP进行接口集成计划沟通
7.CRM AI 方案推进跟踪
8.中间体TMS 合同事宜推进
9.工塑CRM三期优化功能实施中', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('074310b3-20cd-4162-80b0-4d341eb33e3b', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '重要里程碑: 2024-07-01 00:00:00', '2024-07-01 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('2df71e66-cac7-441c-a620-dce7518d05cb', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '待办事项: 考虑信创', '考虑信创', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('500364e3-d726-4f2c-8c69-f9cd6ce923a1', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '十二月: 1）商务方式尽可能确认
2）按照实施计划开展可行的交流和开发工作
风险：集团的第三方开发人员尚未到位', '1）商务方式尽可能确认
2）按照实施计划开展可行的交流和开发工作
风险：集团的第三方开发人员尚未到位。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('60f7c42c-555c-4d87-8d27-777e536d3824', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '一月: 1）商务谈判
2）按照实施计划开展开发工作，按照进度，1月下旬上线；
模型表：初步完成清洗', '1）商务谈判
2）按照实施计划开展开发工作，按照进度，1月下旬上线；
模型表：初步完成清洗', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ab8d8167-d126-4706-8399-15aa5cc38469', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '二月: 1）价格还是偏高，继续谈判', '1）价格还是偏高，继续谈判', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('24ce99eb-abc6-4c4e-8f3b-5e29df7fe53a', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '三月: 1）完成合同 
2）做上线准备工作', '1）完成合同 
2）做上线准备工作', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('1e237f23-abc9-470b-b1d1-c5f39dca1b03', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '四月: 1)已经成功上线', '1)已经成功上线', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('22e79938-fe31-4ed0-808a-6690230b64a2', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '五月: 1）租户方案研讨 
2）准备租户和优化立项材料', '1）租户方案研讨 
2）准备租户和优化立项材料', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('039fa8b1-a0e7-49d7-b0aa-4785988c8dd0', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '六月: 1）进行价格谈判，并更新立项报告', '1）进行价格谈判，并更新立项报告', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('7b27ae2d-f108-4bad-83af-3d3f3e2f0a07', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '七月: 1）讨论设计方案，并调整项目计划，计划租户合并10月初上线', '1）讨论设计方案，并调整项目计划，计划租户合并10月初上线', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a3723be4-a0f6-4c10-9bed-b7ed2cf5a153', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '十月: 已经切换完毕，转入运维', '已经切换完毕，转入运维', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('3e9f8994-a796-468d-af15-1ae588a4f9ec', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '重要里程碑: 2024-09-01 00:00:00', '2024-09-01 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('46a1932b-589b-4848-8825-a86151f450eb', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '八月: 添加剂升级：
1）采购需求提报整体流程测试验证（主材包材、备品备件、固定资产、费用化、项目采购）；
', '添加剂升级：
1）采购需求提报整体流程测试验证（主材包材、备品备件、固定资产、费用化、项目采购）；
2）寻源流程测试验证（包括询价单发布审批、寻源结果审批）；
3）合格供应商审批验证；
4）SAP接口（订单接口开发、供应商扩展接口、预算校验接口、其它基础数据同步接口等）；
5）OA接口开发字段调整（需求计划、寻源单审批）；
寻源、订单模块界面改造调整；
租户合并
1）租户合并流程差异梳理；
25年优化：
1）物流供应商竞价用户测试确认；
2）物流供应商数据收集；
3）鑫方盛电商平台对接；
4）超量寻源需求测试；
5）紧急&零星采购需求开发；
6）电商优化外部系统对接开发；
7）寻源优化开发；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a3cff393-0cd9-4e14-892c-a820832ae1e6', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '九月: 1、添加剂升级：
1）供应商扩展同步SAP接口开发调整:集团级拓展方案；
2）父子订单逻辑开发：物流', '1、添加剂升级：
1）供应商扩展同步SAP接口开发调整:集团级拓展方案；
2）父子订单逻辑开发：物流联动逻辑
3）寄售逻辑开发调整；
4）电商WMS系统对接沟通；
5）OA关闭流程改造测试；
6）采购订单联调测试；
7）测试环境用户测试准备；
8）目录化、电商业务流程联调测试；
9）顾问侧全流程系统联调测试；
10）用户操作手册准备；

2、25年优化：
1）产业链优化以及供应商优化方案评审
2）调查表统一模板沟通以及整理
3）供应商绩效考评管理需求收集
4）25年优化升级功能用户验证（年度需求、专家抽取、电商优化、超量寻源、紧急&零星采购、工作台指引、寻源优化）

3、租户合并：
1）基础数据合并梳理与确认。
2）采购申请业务表数据梳理。
3）测试环境数据覆盖dev。
4）业务流程ppt整理', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('5a6d041d-cdcc-474b-a4dd-7968fc1f5d23', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '十月: 1）添加剂升级：
寄售业务与中控联调测试；
电商WMS系统对接沟通：京东、震坤行沟通
配合用户第四轮', '1）添加剂升级：
寄售业务与中控联调测试；
电商WMS系统对接沟通：京东、震坤行沟通
配合用户第四轮测试；
用户测试问题跟进；
添加剂上线数据切换策略确认；
SAP付款数据、基础数据同步接口测试调整；
S4单据编号问题处理；
添加剂测试优化需求功能设计以及开发；
电商自动收货同步ERP接口开发测试；
2）25年优化：
产业链优化以及供应商分类优化方案评审；
跟进添加剂用户测试电商优化流程；
添加剂测试过程问题以及需求反馈沟通；
跟进优化需求对接外部系统开发,目前正在和外部系统沟通，尚未开始开发；
3）租户合并
租户合并二开功能调整方案沟通与确认。
租户合并方案签字。
外部系统接口安排事项输出与确认。
输出测试脚本。
供应商&商城&寻源数据合并脚本整理。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('fca8b240-6b73-43bd-8162-dfd901a3d3e9', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '十一月: 1、添加剂升级：
上线支持，上线问题处理；
期初补录单据跟进； 
交付文档整理；
2、25年优化：
', '1、添加剂升级：
上线支持，上线问题处理；
期初补录单据跟进； 
交付文档整理；
2、25年优化：
寄售业务京东对接安排；
产业链优化以及供应商分类优化功能设计整理；
SCM附件对接和单点登录验证以及发版；
25年优化上线支持；
3、租户合并：
完成页面个性化、自动填单、业务规则、配置表等配置。
测试验证部分系统功能。
功能迁移处理（第三周），增加技术资源投入。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a97569fe-a4ea-41b8-b0a6-6c460bbb584d', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '十二月: 1、25年优化：
寄售业务京东对接安排；
产业链优化以及供应商分类优化功能设计整理；
产业链优化以及', '1、25年优化：
寄售业务京东对接安排；
产业链优化以及供应商分类优化功能设计整理；
产业链优化以及供应商分类优化功能设计确认；
产业链优化开发清单确认；
25年优化上线支持；
SRM上周工作情况汇报如下：
2、租户合并
测试环境数据问题验证。
测试环境脚本测试。
测试环境接口联调测试。
配合测试环境流程测试。
梳理业务配置数据迁移生产的脚本处理。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('979d4fe4-9db7-4dee-91c0-3d4bb4b4d2bd', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '重要里程碑: 2024-09-01 00:00:00', '2024-09-01 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('63ff5be1-7a09-426e-9dba-498111f5339e', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '待办事项: 跟进财司票据事项；集团蓝图需要审核', '跟进财司票据事项；集团蓝图需要审核', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('7535b47b-6ec9-45a8-b1e8-6a1f112db4ec', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '三月: 1、完成立项审批
 2、完成招标准备工作，进入招标流程 
3、项目开始准备工作，例如项目组织确定等', '1、完成立项审批
 2、完成招标准备工作，进入招标流程 
3、项目开始准备工作，例如项目组织确定等', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('cb95a0d0-b1c2-46e8-b7d6-4b6ebb70b5b6', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '四月: 1、完成招标流程
2、敦促中化信息完成软硬件部署相关事宜
3、项目启动会议相关准备', '1、完成招标流程
2、敦促中化信息完成软硬件部署相关事宜
3、项目启动会议相关准备', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('7c8fbfa6-54ed-40af-ae79-98df29681626', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '五月: 1、召开项目启动会议
2、按计划开展项目调研
3、培训：S4升级功能培训
4、项目准备：VPN权限和', '1、召开项目启动会议
2、按计划开展项目调研
3、培训：S4升级功能培训
4、项目准备：VPN权限和网络事宜
5、相关合同事宜：ERP合同、HFM报表合并改造、添加剂总体合同、保密协议等', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('f8d398c7-ba15-435f-8aa7-27467feb5b97', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '六月: 1、现状调研报告完善和确认，专题讨论
2、蓝图讨论和流程绘制；
3、合同情况跟踪；', '1、现状调研报告完善和确认，专题讨论
2、蓝图讨论和流程绘制；
3、合同情况跟踪；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('b8334cf9-ed01-4224-a962-81b8d5056554', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '七月: 1、各模块蓝图确认，进一步就生产排程和出库流程确认完成方案；
2、MENDIX：已确认mendix和', '1、各模块蓝图确认，进一步就生产排程和出库流程确认完成方案；
2、MENDIX：已确认mendix和SAP的接口方式为直连，需要学习SAP-ODATA接口发布和实施及CDS View的使用。
3、跟踪相关问题和测试环境准备事宜', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('96ed5a87-a5a1-4f7e-baf1-c6e3081f6802', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '待办事项: 优化事项优先级更高，河北方案先准备立项（可以包含在四期）；瑞恒主导从财务变更到运营主导', '优化事项优先级更高，河北方案先准备立项（可以包含在四期）；瑞恒主导从财务变更到运营主导', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('618dc865-9116-4109-8622-ed47546c6035', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '八月: 1、FICO模块：付款平台改造并对接付款平台接口；海波龙接口开发、验证未清项数据及6月交易数据准备；', '1、FICO模块：付款平台改造并对接付款平台接口；海波龙接口开发、验证未清项数据及6月交易数据准备；启动与MDM对接工作；继续与生产协同相关成本测试，完成SA04工厂成本月结；继续与销售协同获利相关测试；开始准备资产操作手册。
PP模块：测试采购计划审批及传SRM功能优化情况；AOP动态平衡表及排产功能的测试；采购需求变更业务的的测试脚本编写及测试数据准备；和财务模块一起测试生产订单成本结算。
MM模块：完成与WMS相关接口的对接；完成财务共享相关接口字段的调整确认；完成采购订单创建接口的开发和联调；完成收发货过账接口字段的核对和程序开发；与MDM的对接物料主数据、供应商主数据；对蓝图汇报时提出的关税等应该维护到采购订单的附加费进行专项讨论；WMS/AOP/财务共享接口字段对接。
SD模块：销售模块主数据类接口卡片编写，开展主数据接口对接；编写交货单、主数据接口FS；组织销售模块关键用户进行D系统单元测试；销售模块与ERP开发顾问对接交货单接口开发；销售订单接口顾问自测及与对应外围系统联调测试；销售模块主数据类接口卡片编写及与对应外围系统确认；蓝图WORD文档签署。
2、MENDIX：细化工作清单：需要多少基础数据接口，需创建什么数据实体，创建什么交互页面等
作业明确分工：需保证我和黄云同时能接触并实操medix操作及sap接口
统一命名规则，约定代码同步时间，目前暂用一套SVN进行代码同步
3、同SAP协商lisence报价', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d0165a67-a14f-4687-ab04-87e0167f6f76', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '九月: 1、开发系统切换到Q系统、准备测试数据，各系统顾问联测并用户培训，具体如下：FICO模块：付款平台功', '1、开发系统切换到Q系统、准备测试数据，各系统顾问联测并用户培训，具体如下：FICO模块：付款平台功能扩大测试并调整相关功能，完成与档案系统相关的联调测试，支持HFM数据相关功能调整，继续推进后勤相关的替代校验。准备QAS系统，展开第一轮集成测试。
PP模块：测试物料需求计划提报OA审批完成返回接口，测试WMS生产订单收、发过账接口，初始化测试系统，批导集成测试数据执行第一轮集成测试。
MM模块：集成测试数据准备，顾问集成测试，关键用户培训，采购报表相关FS编写。
SD模块：SAP测试环境配置传输及检查，SAP测试环境静态数据准备，组织关键用户进行测试系统培训，包括：订单集成、发货及运输集成，开票集成，记录测试系统关键用户培训、顾问集成测试中问题并处理，批量开票功能、泰国形式发票、packinglist打印测试，与CDS/共享系统客户主数据分发联调测试。
2、MENDIX：Mendix针对没有业务接口都需要单独引入
设计开发公用的Odata接口支持多个接口
根据细化需求继续完善权限工作流及页面', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a0f5346e-2c61-4bf5-8653-cb2dad1515dd', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '十一月: FICO模块：计划完成海波龙报表数据初始化核对。后勤业务与共享业务的结果检查与确认。权限调整，支持用', 'FICO模块：计划完成海波龙报表数据初始化核对。后勤业务与共享业务的结果检查与确认。权限调整，支持用户权限调整与优化，付款平台业务，支持新旧系统间的衔接问题，解决用户提出的其他问题。
PP模块：上线后用户问题收集及处理，根据上线问题情况，安排针对性的培训，知识转移文档的整理与交接。
MM模块：上线问题处理。
SD模块：生产机将国内未清业务单据补录完成并核对，生产机库存开账后，补录销售出库过账，上线后支持，收集问题并解决对应问题。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('783244ce-7a70-4a3a-94a7-bbad0c2fec31', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '十二月: 1、首月及月结情况总结；
2、持续支持和系统问题总结', '1、首月及月结情况总结；
2、持续支持和系统问题总结', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('e3273ab5-3c2f-4461-becb-a81dabff4579', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '重要里程碑: 2025-05-08 00:00:00', '2025-05-08 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9ef64e17-8d1e-4270-9727-6a8626f4f2e1', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '待办事项: 评估信创', '评估信创', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('b5b31694-5bc1-4dab-84b3-d68cd7bb356e', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '十二月: 1）商务方式尽可能确认
2）按照实施计划开展可行的交流和开发工作
风险：集团的第三方开发人员尚未到位', '1）商务方式尽可能确认
2）按照实施计划开展可行的交流和开发工作
风险：集团的第三方开发人员尚未到位。
1）1月1日切换上线，届时将与ERP项目组根据上线策略共同完成配置和补录工作。
2）信创工作：等候信创小组进一步安排', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('e79c55c9-5b8e-4161-a307-cb617ffc62f1', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '一月: 1）按照上线计划，定于1月1日正式启用,1月7日开始配合CRM补录订单数据
2)信创评估已经完成，等', '1）按照上线计划，定于1月1日正式启用,1月7日开始配合CRM补录订单数据
2)信创评估已经完成，等待信创小组立项完毕', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('124110ae-c3e7-4174-8c2c-322c5e42242d', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '二月: 1)信创评估已经完成，等待信创小组立项完毕', '1)信创评估已经完成，等待信创小组立项完毕', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9f67748d-d22c-4c87-989c-5e4c9f7db006', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '三月: 1)信创评估已经完成，等待信创小组立项完毕', '1)信创评估已经完成，等待信创小组立项完毕', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('86df283a-b54c-4e0f-89af-2e56945fa27f', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '四月: 1)信创评估已经完成，等待信创小组立项完毕', '1)信创评估已经完成，等待信创小组立项完毕', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('8184fb8d-da09-4886-893e-0973ef1c89e1', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '五月: 1)信创评估已经完成，等待信创小组立项完毕', '1)信创评估已经完成，等待信创小组立项完毕', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('71491c1f-edbf-4942-bfb6-25ffb470eb8f', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '六月: 4、', '4、', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('e52b6d09-2cc2-4d09-ad03-91a5cc12a862', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '七月: 1）准备硬件资源
2）完成项目计划调整，计划10月初上线', '1）准备硬件资源
2）完成项目计划调整，计划10月初上线', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('2953e780-56d0-4cb2-9320-8e010e508f77', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '八月: 1）完成测试环境数据迁移，并开始测试；
2）测试环境开始适配性调整程序 
3）搭建生产环境', '1）完成测试环境数据迁移，并开始测试；
2）测试环境开始适配性调整程序 
3）搭建生产环境', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9c72e1d4-45b0-4150-8ac4-b044e6541186', '855a52cd-4fa0-4c7f-8135-d150c6c28b8e', NULL, NULL, '一月: 1.SAP、OA相关接口开发
2.项目试运行', '1.SAP、OA相关接口开发
2.项目试运行', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('45035ee0-3bde-427c-a4be-fcd9395213a2', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '十二月: 1）商务方式尽可能确认
2）按照实施计划开展可行的交流和开发工作
风险：集团的第三方开发人员尚未到位', '1）商务方式尽可能确认
2）按照实施计划开展可行的交流和开发工作
风险：集团的第三方开发人员尚未到位。
1.南通星辰合同流程内部发起。
2.与ERP及OA，影像系统各业务接口对接沟通，制定开发计划。
1.合同流程的跟踪，合同盖章确认。
2.与ERP及SRM，影像系统各业务接口对接沟通，制定开发计划。
1.接口计划与各业务对接
2.合同签订盖章
3.工程师到现场业务洽谈施工', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('cdfb1042-5e92-490b-b764-4144d0b8bc0c', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '一月: 1.供应商到达现场办公
2.制定项目计划文档', '1.供应商到达现场办公
2.制定项目计划文档', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('221b4c90-8d0a-4f52-8f7b-b03b04a092f1', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '二月: 1.配合ERP系统上线，业务数据补充
2.完成与ERP系统接口的初步沟通，评估接口方案的可行性，并且', '1.配合ERP系统上线，业务数据补充
2.完成与ERP系统接口的初步沟通，评估接口方案的可行性，并且尽快根据接口方案文档，制定开发文档
3.开发文档编辑
4.业务需求二次确认', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('bf627c4a-af23-4ec4-b88a-4231b3953422', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '三月: 1.PU系统整理需求及方案文档
2.公司内部评审需求及方案文档
3.关键用户评审需求及方案文档
4.', '1.PU系统整理需求及方案文档
2.公司内部评审需求及方案文档
3.关键用户评审需求及方案文档
4.确认开发方案与开发顺序
5.整理开发需求及所需环境', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('639321f8-8138-46bf-8836-5330ef93533d', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '四月: 为开发需求准备相应环境及数据准备（持续进行中）；
与ERP进行接口及报文的可用性核对与调试，并根据结', '为开发需求准备相应环境及数据准备（持续进行中）；
与ERP进行接口及报文的可用性核对与调试，并根据结果调整表单部分字段（进行中）；
开发工作持续进行中，目前已完成：采购申请、采购订单、采购入库及冲销同步（待调整）；
开发进行中：影像系统接口；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9b319187-1636-4bea-84f6-dcfebf9285ff', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '五月: 第一周
ERP相关接口已调用成功，并将ERP系统接口报错提交至ERP，待反馈
第二周
与用户演示并测', '第一周
ERP相关接口已调用成功，并将ERP系统接口报错提交至ERP，待反馈
第二周
与用户演示并测试已完成功能；
与ERP沟通并测试接口问题；
生产环境主数据及相关数据调整；
生产环境功能调整；
与ERP沟通付款申请、实付款、发票校验需求；
第三周
相关接口调整完毕，并完成上线工作
进行后续的开发工作', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9737cefc-10f4-442b-a1d3-8f56350b54df', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '重要里程碑: 2024-10-17 00:00:00', '2024-10-17 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('22f51c1d-a474-42ff-905c-6c0b219a82fc', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '待办事项: 转运维用押金或其他保障措施', '转运维用押金或其他保障措施', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('0d8bdedd-bc77-4fc8-a3e8-ba3ddb9a4922', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '十二月: 1、进行系统开发说明书的编写，进行系统开发与测试；2、进行最终用户操作培训，3、进行权限的收集与设定', '1、进行系统开发说明书的编写，进行系统开发与测试；2、进行最终用户操作培训，3、进行权限的收集与设定，4、针对第一轮有问题的地方进行第二轮集成测试。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ea5211dd-d975-464d-b647-476ebc35a301', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '一月: 1、网络、打印机、ERP用户检查与设置，最终用户考试，2、现有系统财务月结，动态数据收集（库存、未清', '1、网络、打印机、ERP用户检查与设置，最终用户考试，2、现有系统财务月结，动态数据收集（库存、未清销售订单、未清采购订单）3，期初库存数据录入，应收、应付、总账、暂估、固定资产录入，准备上线工作', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('087ad74d-a140-4ea7-b1c1-eba4a6e5fda6', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '二月: 尽快总结问题，针对问题分析处理对策', '尽快总结问题，针对问题分析处理对策', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('cd998206-3555-40fb-9762-2d4b8b3d5a5b', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '三月: ①上线支持
②对项目问题进行处理、沟通、讨论确定解决方案：
计划详细整体过一遍问题清单', '①上线支持
②对项目问题进行处理、沟通、讨论确定解决方案：
计划详细整体过一遍问题清单', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('63acd01d-513e-45d6-a3ff-4abcde5f85af', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '四月: ①上线支持及月结支持
②问题跟踪及解决', '①上线支持及月结支持
②问题跟踪及解决', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('b7c5a5e6-bbdb-4941-be33-b435140aa2cc', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '五月: ①上线支持
②问题跟踪及解决', '①上线支持
②问题跟踪及解决', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a0e13abc-dc9e-42e7-b845-3430cd566d9a', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '六月: 1、试运行支持和月结支持
2、问题跟踪和解决；
3、变更和优化清单确认；', '1、试运行支持和月结支持
2、问题跟踪和解决；
3、变更和优化清单确认；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('b43e0e51-6c0b-4712-bf42-e7611f944407', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '八月: 1、试运行支持和月结支持
2、问题跟踪和解决；
3、变更和优化清单确认；', '1、试运行支持和月结支持
2、问题跟踪和解决；
3、变更和优化清单确认；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('aae68357-b516-4563-b1bb-69a66f9e8f45', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '九月: 1、试运行支持和月结支持
2、问题跟踪和解决；
3、变更和优化清单确认；', '1、试运行支持和月结支持
2、问题跟踪和解决；
3、变更和优化清单确认；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('7751c6ef-b787-48c5-9ce6-b30bf5e8ab08', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '十月: ①上线支持
②问题跟踪及解决', '①上线支持
②问题跟踪及解决', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('c21d9159-815f-4cdb-ad1c-6912e0337b53', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '十一月: 1、试运行支持和月结支持
2、问题跟踪和解决；
3、变更和优化清单确认；', '1、试运行支持和月结支持
2、问题跟踪和解决；
3、变更和优化清单确认；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('50055f02-2252-458d-ad8c-8e067290445c', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '重要里程碑: 2024-07-01 00:00:00', '2024-07-01 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('0f18511f-7086-4959-8eae-b2d1443769b4', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '重要里程碑: 2024-10-17 00:00:00', '2024-10-17 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('78c79913-8046-4161-94de-659abfa5fe04', '5c168ab0-df2a-4e7f-8ab7-4d06e2d289cd', NULL, NULL, '待办事项: 盯审批进度', '盯审批进度', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('e03b390c-3a1b-4071-83f8-94b1d93ab946', '6fdaa9be-7af9-4820-afa5-b1327964606e', NULL, NULL, '待办事项: 特材各系统流程搭建', '特材各系统流程搭建', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('805210de-d47a-4b9d-8bc2-7d7bf64692ff', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '十二月: 1、环氧事业部推广：
1）南通星辰、扬农锦湖继续测试模型、验证数据；
2）跟进业务数据填报用户账号、', '1、环氧事业部推广：
1）南通星辰、扬农锦湖继续测试模型、验证数据；
2）跟进业务数据填报用户账号、权限收集；
3）试运行准备：数据准备、用户角色权限配置，排定最终用户培训计划；
2、中间体事业部运维与改进：
1）简化版测算界面测试反馈、沟通；
2）中间体12月模型运行保障；
3）SAP历史作业成本数据用户核对；
3、周二，集团数字化部经营计划求解平台专题汇报。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('b487f975-126d-4176-8f83-1422fc9be0bd', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '一月: 1、环氧事业部推广：
1）试运行结果及问题总结；
2）瑞恒公司环氧相关装置数据的查看与操作；
3）生', '1、环氧事业部推广：
1）试运行结果及问题总结；
2）瑞恒公司环氧相关装置数据的查看与操作；
3）生产环境切换准备、数据迁移；
2、中间体事业部运维与改进：
1）装置停车损失的计算方案设计、开发；
2）跟进新部署功能的试用、反馈；
3、MES集成开发推进。
4、化工事业部虚拟服务器安装、调试。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('43ddbb4f-5755-4662-8b0c-c4a85459e1a0', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '二月: 1、中间体事业部领导层使用平台
2、保障中间体2月模型运行，测试停车损失纳入模型后的计算、验证
3、', '1、中间体事业部领导层使用平台
2、保障中间体2月模型运行，测试停车损失纳入模型后的计算、验证
3、MES集成开发：跟进取数开发进度，考虑后续数据应用。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('1600c71c-371b-409b-9d67-8d59fe6ba490', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '三月: 1、三期项目计划讨论、立项材料完善、申报。
2、讨论ERP业务数据范围与数据结构。
3、跨基地求解准', '1、三期项目计划讨论、立项材料完善、申报。
2、讨论ERP业务数据范围与数据结构。
3、跨基地求解准备，中间体产业链关联业务梳理。
4、推广实施准备，实施流程梳理。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('e3fbf351-b8de-4c57-99e2-ae17be8b4de2', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '四月: 1、结合运营指标穿透项目，设计、讨论装置产品日成本实现方案。
2、跨基地模型：中间体事业部跨基地求解', '1、结合运营指标穿透项目，设计、讨论装置产品日成本实现方案。
2、跨基地模型：中间体事业部跨基地求解需求、方案沟通与完善；跟进扬农本部业务、中间体内部关联交易数据梳理。
3、推广实施：IT内部培训沟通。
4、运维优化：跟进瑞恒单耗数据核对、更新。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('6ca888a7-fea9-4d11-a052-84bd8bc413eb', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '五月: 1、日成本方案：开始SAP业务数据ETL开发。
2、跨基地模型：继续算法功能开发；开始界面开发；扬农', '1、日成本方案：开始SAP业务数据ETL开发。
2、跨基地模型：继续算法功能开发；开始界面开发；扬农本部业务、中间体内部关联业务待定问题沟通、导入测试系统。
3、内外部取数：开始SAP业务数据ETL开发。
4、运维优化：瑞恒工艺完善问题讨论、协助用户调整，单耗数据更新。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('0a1ee566-50e5-457a-8115-d0b805990429', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '六月: 1、日成本方案：跟进一体化经营管理平台项目日成本效益测算的落地方案及实现方式。
2、跨基地模型：瑞恒', '1、日成本方案：跟进一体化经营管理平台项目日成本效益测算的落地方案及实现方式。
2、跨基地模型：瑞恒工艺调整后的试用、验证与完善；讨论瑞祥工艺调整、完善模型；测试扬农本部+三基地合并求解；继续算法功能完善、界面开发。
3、外部价格集成：研究、探讨外部价格数据的使用方案。
4、沟通中间体事业部三个月滚动预测的计算逻辑、需求，评估在求解平台的实现方案。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('935e1c21-96b9-42fd-9172-e3e32d2624d0', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '七月: 1、日成本效益测算：完善日成本模型数据结构和算法功能；核对SAP、MES业务数据，完善ETL功能开发', '1、日成本效益测算：完善日成本模型数据结构和算法功能；核对SAP、MES业务数据，完善ETL功能开发，测试日成本效益计算，结果验证。
2、跨基地模型：配合用户测试扬农本部+三基地合并求解；确定市价模型扩展功能方案，着手开发实现。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('5d4b8145-8ed8-4979-af51-bfc78ff62e96', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '八月: 1、日成本效益测算：
1）继续配合用户，测试、验证数据，排查、解决问题；（主要方向：补充费用类数据后', '1、日成本效益测算：
1）继续配合用户，测试、验证数据，排查、解决问题；（主要方向：补充费用类数据后的结果验证；界面优化；）
2）瑞恒数据验证后的用户确认；
3）沟通MES数据问题及改进方案
4）考虑SAP月结后的成本数据抓取，及预测-实际数据对比的实现。
2、跨基地模型：
1）配合用户测试、完善市价模型。
2）配合用户测试、完善扬农本部+三基地合并求解。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('f30b8ad4-f8fb-4825-8816-b317ee4b6e45', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '九月: 1、日成本效益测算：
1）完成经营计划求解平台的数据填报界面开发，日成本平台数据抽取开发；
2、预实', '1、日成本效益测算：
1）完成经营计划求解平台的数据填报界面开发，日成本平台数据抽取开发；
2、预实对比：
1）功能开发：设计、开发装置成本构成的数据对比界面，含原料单耗对比、制造费用对比。
2）用户试用沟通，探讨如何使用实际数据，复盘经营计划。
3、跨基地模型：
1）开始整理瑞祥模型的新增与变更；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('f0aee62e-ffc0-47fb-b8a6-7e67f57e5aa3', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '十月: 1、系统优化方案设计
1）继续讨论、完善事前算赢平台优化方案
2、河北三家工厂基础数据收集与梳理
1', '1、系统优化方案设计
1）继续讨论、完善事前算赢平台优化方案
2、河北三家工厂基础数据收集与梳理
1)初步计划&总体调研_250918文档三家公司各填写一份问题清单解答
2)三家需提供工艺工序流程图(各家自己准备)
3)三家需提供模板12文档的基础数据材料', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('2d12a12e-83b6-458f-b741-cb7b42e98d00', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '十一月: 1、系统优化方案设计
1）瑞恒装置负荷-单耗分析方案，用户沟通讨论
2）迁移到一体化平台的，相关技术', '1、系统优化方案设计
1）瑞恒装置负荷-单耗分析方案，用户沟通讨论
2）迁移到一体化平台的，相关技术了解、培训
3）瑞恒组建项目组
2、鑫宝事前算赢推广
1）完善鑫宝模型数据
2）制定河北三家工厂实施方案、计划', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('dc468249-35e1-408e-b984-42555914b18e', '855a52cd-4fa0-4c7f-8135-d150c6c28b8e', NULL, NULL, '三月: 项目验收', '项目验收', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('86ab4ff9-f12a-4678-9faf-437c66c9c3c3', 'd018edb6-6374-46d7-9feb-19ebd875fb04', NULL, NULL, '待办事项: 总部指标穿透取数；
日成本预测需求', '总部指标穿透取数；
日成本预测需求', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('13a57012-a418-45df-8d07-860f9e1b3766', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '十二月: 1、系统优化方案设计
1）迁移到一体化平台：完成界面风格调整，及权限配置，内部测试
2）装置负荷-单', '1、系统优化方案设计
1）迁移到一体化平台：完成界面风格调整，及权限配置，内部测试
2）装置负荷-单耗分析方案，DEMO设计', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('068ff230-85b4-4616-a032-91c9338ab318', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '重要里程碑: 三期(中间体):2025/3/28
三期(推广):待定', '三期(中间体):2025/3/28
三期(推广):待定', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('09c3c9d1-b5ea-4b07-b1ff-297cd891b740', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '待办事项: BIP结合预算编制与人力部门确认，总部统筹一部分预算', 'BIP结合预算编制与人力部门确认，总部统筹一部分预算', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('6f075762-89c1-407e-bb89-4fe854300981', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '十二月: 1、一期目标相关
   1）完成HR业务流程方案确认
   2） 考勤、绩效应用场景测试跟踪 
  ', '1、一期目标相关
   1）完成HR业务流程方案确认
   2） 考勤、绩效应用场景测试跟踪 
   3）一阶段目标内容商务沟通会
2、薪酬上报相关
      1） 薪酬上报方案待HR确认
      2） 2024年11月国资委数据上报支持
3、确认个性化需求清单与初步解决方案', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ddc7368a-1566-487f-845e-647176602db6', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '一月: 1、一期目标相关
   开展流程实施工作及国资委上报取数实施工作
2、薪酬上报相关
    支持12', '1、一期目标相关
   开展流程实施工作及国资委上报取数实施工作
2、薪酬上报相关
    支持12月各单位薪资发放单维护及国资委上报
3、二阶段个性化推进
      持续进行个性化需求确认（未确认部分：国际：预算、薪酬及过账内容、 扬农：财务分摊内容）', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ba222938-1302-46aa-a1cd-9fb35a5608ca', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '三月: 1、一期目标相关
     1）统一流程实施：测试及问题解决等 
     2) 薪酬自动取数：安排', '1、一期目标相关
     1）统一流程实施：测试及问题解决等 
     2) 薪酬自动取数：安排使用培训等
     3）补充标准化实施：跟踪用户测试进度等
2、薪资项目公式、考勤相关规则持续确认
3、二阶段个性化推进
    1)薪酬审批方案沟通和确认
    2)个性化需求分类评估沟通等', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('5bf77eff-bb06-4dc8-8751-28c52f1d4731', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '四月: 1、一期目标相关
     1）统一流程实施：测试及问题解决、需求变更沟通等
     2) 薪酬自', '1、一期目标相关
     1）统一流程实施：测试及问题解决、需求变更沟通等
     2) 薪酬自动取数：推进上线
     3）补充标准化实施：跟踪用户测试进度等
2、二阶段个性化推进
    持续完善已确认需求工作量评估并和用户沟通确认', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('40371d4f-9b73-45bb-a51e-f99a489a51a2', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '五月: 1、一期目标相关
     1）统一流程实施：测试及问题解决、上线准备（请假额度、审批人、事项办理矩', '1、一期目标相关
     1）统一流程实施：测试及问题解决、上线准备（请假额度、审批人、事项办理矩阵收集）等
2、二阶段个性化推进
     1）国际部分商务谈判、立项文档准备等
     2）扬农需求确认等', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('07d04c7f-24ac-4425-93f0-54b02115d92c', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '六月: 1、一期目标相关
    统一流程上线跟踪及问题处理
  
2、二阶段个性化推进
     1）二期', '1、一期目标相关
    统一流程上线跟踪及问题处理
  
2、二阶段个性化推进
     1）二期立项相关工作', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('bf3818b1-ed89-4739-b877-470cd030aa36', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '七月: 1、一期目标相关
    统一流程上线跟踪及问题处理
  
2、二阶段个性化推进
     1）二期', '1、一期目标相关
    统一流程上线跟踪及问题处理
  
2、二阶段个性化推进
     1）二期商务流程
     2）确认二期项目整体需求方案', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('fe53d986-51cd-47a7-b5ec-6ab7bed2da97', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '八月: 1、一期目标相关
    流转单问题跟踪处理；持续流转单办理事项收集及配置
  
2、二阶段个性化推', '1、一期目标相关
    流转单问题跟踪处理；持续流转单办理事项收集及配置
  
2、二阶段个性化推进
     二期个性化（国际部分)
    1）工资发放审批功能完成内部测试、编写完成测试用例，预计下周末提交用户测试
     2）考勤年假结转功能完成内部测试、编写完成测试用例，提交用户测试
     3）员工信息导入模板详细方案与用户确认完后进行开发
     4）完善薪资测算的细化开发方案并和用户进行确认

    扬农个性化
    1）与扬农HR沟通个性化实施内容与方案
    2）评估扬农实施范围与工作量（预计8.8前完成评估）', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('0b6e1d9b-6d14-473e-b859-8d5f8edba877', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '九月: 1、一期目标相关
     1）流转单相关：
          离职审批推送流转单功能变更调整开发', '1、一期目标相关
     1）流转单相关：
          离职审批推送流转单功能变更调整开发、调动流转单功能完善等
     2）主兼岗调整方案沟通
2、二阶段个性化推进
     二期个性化（国际部分)
   a)  薪酬审批功能用户生产环境验证
   b) 模版导入功能项目组内部测试
   c）薪酬测算功能方案完成项目组评审，进入开发阶段
   d）薪资范围字段更新系统初始化数据
   e）所属产业链、岗位分类字段收集整理数据初始化系统
   f）《员工变动分析统计表》报表进入代码实现阶段', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('f93c04e4-87a5-4b8a-863a-950263759905', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '十月: 二期个性化（国际部分)
   1、模版导入功能用户测试、问题调整
   2、薪酬测算功能提交用户测试', '二期个性化（国际部分)
   1、模版导入功能用户测试、问题调整
   2、薪酬测算功能提交用户测试
   3、《员工变动分析统计表》报表提交用户测试', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('110414b6-0ecb-4807-87b9-31d867409234', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '十一月: 二期个性化（国际部分)
  1）薪酬测算功能协助用户进行UAT测试及问题处理等', '二期个性化（国际部分)
  1）薪酬测算功能协助用户进行UAT测试及问题处理等', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('67dd80ef-1619-43d0-a32e-ae963978bef4', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '十二月: 二期个性化（国际部分)
1、薪酬审批功能协助用户运行支持
2、薪酬测算功能协助用户运行支持，初始化固', '二期个性化（国际部分)
1、薪酬审批功能协助用户运行支持
2、薪酬测算功能协助用户运行支持，初始化固薪月数、奖金占比', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('8d7cd1f1-01eb-4ebd-8500-88ff4ff7a320', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '重要里程碑: 一期：2024/07
二期：2025/07', '一期：2024/07
二期：2025/07', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('836b535b-3233-4208-8343-84cfd774a390', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '待办事项: 考虑研发数字化规划', '考虑研发数字化规划', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('29618ceb-4817-4afd-acd5-4577542fd952', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '十二月: 1、剩余项目管理，文件管理，工时模块功能开发后测试
2、已上线功能优化，问题修复
3、完成全部功能上', '1、剩余项目管理，文件管理，工时模块功能开发后测试
2、已上线功能优化，问题修复
3、完成全部功能上线', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a9c598f6-73a3-476e-9479-0d1f94621a33', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '一月: 中化科技LIMS系统上线使用
跟进工塑及高纤合同签订', '中化科技LIMS系统上线使用
跟进工塑及高纤合同签订', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a7c23692-565c-4a1b-bcb2-f0d86b422ffa', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '二月: 持续跟进工塑及高纤合同签订', '持续跟进工塑及高纤合同签订', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('feb90004-2079-4db9-8f64-d232b4872d06', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '三月: 中化高纤：
与财务部门和研发部门确认需求说明书内容
编写设计文档的基础数据管理、项目科研论证、项目立', '中化高纤：
与财务部门和研发部门确认需求说明书内容
编写设计文档的基础数据管理、项目科研论证、项目立项管理部分
根据调研内容结合合同整理差异性分析
工塑：
调研工塑事业部配方管理需求', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d7a6ccbe-63cc-4f23-8f7a-f209a540fe09', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '四月: 中化高纤：
1、蓝图材料修改：财务李晓峰总将与赵开荣总就工时管理方法进行讨论明确后，此项待明确后再写', '中化高纤：
1、蓝图材料修改：财务李晓峰总将与赵开荣总就工时管理方法进行讨论明确后，此项待明确后再写入材料
2、与财务部门就化数仓同步字段进行沟通
3、测试环境安装部署
4、持续开发
工塑：
1、讨论中蓝集成对接内容
2、根据沟通记录，制作样品模板，研讨样品模板实现方案
3、根据调研内容与需求点，结合系统，画出功能原型图
4、编写概要设计文档
5、与工塑管理层及中蓝确认项目范围
6、供应商正梳理超出合同的需求，不是本周就是下周要进行商务沟通', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('82ac938f-4e3c-45bd-8feb-9ffe6fa3b2aa', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '五月: 中化高纤：
与用户演示系统功能，沟通细节并修改
与用户和SAP系统沟通逆向业务和异常情况的处理
工塑', '中化高纤：
与用户演示系统功能，沟通细节并修改
与用户和SAP系统沟通逆向业务和异常情况的处理
工塑：
开发报告管理和不合格品评审功能
测试和优化芮城和扬州两个业务流程功能', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('e5a986e7-ea36-4964-a89d-536c40d29d91', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '六月: 中化高纤：
给研发部、财务部人员进行系统功能培训
与SAP对接的相关接口开发，并进行进行联调测试
跟', '中化高纤：
给研发部、财务部人员进行系统功能培训
与SAP对接的相关接口开发，并进行进行联调测试
跟进解决试运行中出现的系统问题
工塑：
扬州ABS、芮城维护基础数据
跟进扬州ABS、芮城用户测试系统功能
跟进扬州ABS、芮城反馈的优化问题处理验证并反馈
跟进上海改性产品开发部反馈的优化问题处理验证并反馈
跟进中蓝PIMP评估情况', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('4a50446b-13f1-4f97-b093-a316d3364958', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '七月: 中化高纤：
跟进解决试运行中出现的系统问题
对系统功能进行优化和功能测试
跟进化数仓项目费用视图对研', '中化高纤：
跟进解决试运行中出现的系统问题
对系统功能进行优化和功能测试
跟进化数仓项目费用视图对研发系统项目费用集成进行调试
联合SAP、财务人员、研发人员对研发项目成本系统业务功能进行测试
制作项目立项申请书报表
工塑：
跟进扬州ABS、芮城用户维护基础数据、测试业务功能
跟进研发用户测试配方管理功能
跟进扬州工塑反馈的优化问题处理验证并反馈
跟进芮城分公司反馈的优化问题处理验证并反馈
跟进上海改性产品开发部反馈的优化问题处理验证并反馈
中化科技任务接口开发及测试
化数仓物料信息接口开发及测试
协助芮城维护样品模板
协助扬州工塑维护产品标准', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('19ca4720-0298-4584-a3cb-24b570aeaa7b', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '八月: 中化高纤：
1、跟进解决试运行中出现的系统问题
2、跟进首页面板开发与调试
3、WBS功能化数仓历史', '中化高纤：
1、跟进解决试运行中出现的系统问题
2、跟进首页面板开发与调试
3、WBS功能化数仓历史项目费用同步功能修改
4、准备正式数据
工塑：
1、协助用户测试流程及功能
2、跟进测试过程中发现的问题处理
3、芮城的报表优化
4、编写扬州ABS、研发操作培训手册
5、跟进配方任务全流程业务改为多样品流程的测试
6、跟进中蓝项目变更事宜', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('748d9bbd-dbc2-46f7-9489-45d360044b7e', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '九月: 中化高纤：
1、跟进上线后使用过程中发现的问题并处理
2、与关键用户沟通项目未尽事项等验收准备事宜
', '中化高纤：
1、跟进上线后使用过程中发现的问题并处理
2、与关键用户沟通项目未尽事项等验收准备事宜
工塑：
1、遗漏问题处理及修改
2、报表优化修改
3、准备与PIMP对接的新测试环境
4、跟进与PIMP对接接口开发进度，开发结果回传接口
5、芮城-用户操作手册更新', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('69f974ab-9af3-4ccd-971e-ec201e5afa2d', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '十月: 中化高纤：
1、持续跟踪并解决使用中新发现的问题
2、与用户沟通产成品管理方案
工塑：
1、与PIM', '中化高纤：
1、持续跟踪并解决使用中新发现的问题
2、与用户沟通产成品管理方案
工塑：
1、与PIMP联调测试配方业务模块
2、持续跟踪并解决使用中新发现的问题
3、跟进研发部新需求实现方案，与属地MES负责人（周英波）沟通配方对接BOM实现可行性，与属地ERP负责人（潘宝圣 ）沟通成本分析表对接实现可行性。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('588510b9-1b54-4d19-93fa-e9d8879ae2c0', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '十一月: 中化高纤：
1、待晓菲进一步测试产成品虚拟仓库方案后再与用户沟通
工塑：
1、跟进与PIMP联调测试', '中化高纤：
1、待晓菲进一步测试产成品虚拟仓库方案后再与用户沟通
工塑：
1、跟进与PIMP联调测试配方检测对接工作
开始研发数据化工作交接', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('b4880b5d-faed-4b31-aba2-7a4bd128c24b', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '重要里程碑: 2025-02-01 00:00:00', '2025-02-01 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a1f3ade8-fdf8-4b70-9e60-e42d215fa0f6', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '待办事项: 尽快交付用户测试', '尽快交付用户测试', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9a01c087-cf01-4b1c-9442-dd03179ea712', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '三月: 1、完成卓创连通性测试。
2、开始梳理卓创取数维度。
3、运营指标的沟通与讨论。', '1、完成卓创连通性测试。
2、开始梳理卓创取数维度。
3、运营指标的沟通与讨论。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('f336fcf3-5780-453a-8414-205a3f5ec4fe', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '四月: 主数据、ETL、指标对应源系统数据逻辑梳理持续进行', '主数据、ETL、指标对应源系统数据逻辑梳理持续进行', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('929e59e9-5e51-4dee-b481-797fc770e4f4', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '五月: 1、GU平台数据库与帆软权限开放策略
2、根据财务到各业务域关联关系拉齐，并和关键用户确认主题框架（', '1、GU平台数据库与帆软权限开放策略
2、根据财务到各业务域关联关系拉齐，并和关键用户确认主题框架（分析主题）
3、发出经营分析体系（初版）
4、进行总部层面-业务+财务研讨', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('aa62cbae-b2a0-442a-a7a0-08e9065cdb27', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '六月: 1、统一事业部层面针对指标字典定义的统一口径
2、销售量价模型修改，客户/产品维度CRM数据梳理
3', '1、统一事业部层面针对指标字典定义的统一口径
2、销售量价模型修改，客户/产品维度CRM数据梳理
3、基于指标字典进行系统探源', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('47660be2-ed78-4fbd-9d98-c96f1a7eee03', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '七月: 1、蓝图汇报；
2、梳理所有指标，准备第二批源系统取数工作（第二批源系统取数FS编写）；
3、穿透模', '1、蓝图汇报；
2、梳理所有指标，准备第二批源系统取数工作（第二批源系统取数FS编写）；
3、穿透模型实操应用及验证
4、对照表数据表开发
5、各业务域数据模型开发及报表开发
6、日成本效益：模型数据内测及报表开发', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('eedb013d-74dd-47e5-8fee-be04e215ce35', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '八月: 1、830阶段（34张表）开发进度：集成测试（5张），开发及内测：10张（财务2、采购3、销售2、生', '1、830阶段（34张表）开发进度：集成测试（5张），开发及内测：10张（财务2、采购3、销售2、生产3）
2、专题沟通（数字化+财务）产业链分摊规则-合并抵消逻辑沟通；
3、专题沟通（数字化+财务）法人口径毛利-手工调整数据逻辑沟通
4、数据治理沟通（数字化+IBM+采购+财务）：采购/财务各域
5、主数据维表及基本表设计评审
6、跟进博科ERP取数FS文档编写评估结果
7、跟进LIMS取数方案评估及取数技术对接，MES系统FS逻辑沟通；
8、日成本效益（瑞恒配置表数据导入）重算结果后，进行复测。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('7f5d33c1-c8eb-4fc4-be98-d5e93e9abd06', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '九月: 1、830阶段（34张表）：按计划推进，争取完成测试确认工作。
2、博科ERP-FS数据验证工作。', '1、830阶段（34张表）：按计划推进，争取完成测试确认工作。
2、博科ERP-FS数据验证工作。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('c5b0fcfa-2460-4c63-99c4-4dac0164dace', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '十月: 1、第三批次（环氧/河北）：数据开发、取数逻辑差异沟通
2、日成本效益（星辰&鑫宝）：业务系统取数机', '1、第三批次（环氧/河北）：数据开发、取数逻辑差异沟通
2、日成本效益（星辰&鑫宝）：业务系统取数机构通、梳理预估数据需求', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('4120a8fb-b359-44d1-ba3e-323e8694d1c0', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '十一月: 1、第三批次（环氧/河北）
1）环氧/河北UAT测试签字
2）后续问题处理
2、日成本效益推广（南通', '1、第三批次（环氧/河北）
1）环氧/河北UAT测试签字
2）后续问题处理
2、日成本效益推广（南通星辰）：
1）导入SKU-SPU对应、包装费数据，模型搭建，内部测试
2）设计日成本相关数据填报功能
3、日成本效益推广（河北鑫宝）
1）辅料、能耗数据纳入模型，重算一版继续测试
2）跟进MES数据治理（调油业务，物耗能耗数据准确性问题）', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('45e130ce-7003-4a4e-8b84-3584b62c31b1', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '十二月: 1、根据梳理进展进行复核
2、二期合同条款整理
3、S4取数开发完成并进行功能测试
4、日成本效益推', '1、根据梳理进展进行复核
2、二期合同条款整理
3、S4取数开发完成并进行功能测试
4、日成本效益推广（南通星辰）：
1）跟进MES数据补录与修正，保证测试数据准确
2）配合用户测试与数据验证
3）跟进填报功能开发，配合测试
5、日成本效益推广（河北鑫宝）
1）协助用户测试、数据验证
2）根据反馈，调整优化模型
6、瑞祥、瑞泰日成本实施准备', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('816baed5-133b-4862-bf34-d99ee37f0e60', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '重要里程碑: 2025-04-27 00:00:00', '2025-04-27 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d2dd311a-d235-49a8-ba77-31420059112a', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '十二月: 一、审计监督平台上线运行跟踪及功能优化：
1) OA集成，OA系统数仓(含总部数据)取数确定方案并进', '一、审计监督平台上线运行跟踪及功能优化：
1) OA集成，OA系统数仓(含总部数据)取数确定方案并进行接口实施与数据测试，预期进度100%；
2) 平台日常运维以及其他可能存在的测试与问题处理；
二、工塑纪检平台
1）分批次完成用户提出的各报表新的需求点，截止月底新的需求共计15处。
三、淮河化工纪检平台
1）如淮河化工系统流程完全确定的情况下，完成方案的设计与数据取数；
四、事业部审计平台
1）OA流程清单确认的情况下，获取总部的业务流程数据并完成校验。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ba8b12c5-a754-4777-a40e-ca15097f593d', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '一月: 一、审计监督平台上线运行跟踪及功能优化：
1) OA集成，OA系统数仓(含集团数据)取数如OA业务对', '一、审计监督平台上线运行跟踪及功能优化：
1) OA集成，OA系统数仓(含集团数据)取数如OA业务对接人员有时间确定方案并进行接口实施与数据测试；
2）与中化集团的IT人员沟通集团风控平台与事业部目前的审计监督平台的差异点并汇总差异材料
3) 平台日常运维以及其他可能存在的测试与问题处理；
二、工塑纪检平台
1）完成第三次新需求文档，需求与优化点共9处。
三、淮河化工纪检平台
1）如淮河化工系统流程完全确定的情况下，完成方案的设计与数据取数；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('79ce506f-1fa1-4210-a313-fab041189b66', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '二月: 一、审计监督平台上线运行跟踪及功能优化：
1) OA集成，OA系统数仓(含集团数据)取数如OA业务对', '一、审计监督平台上线运行跟踪及功能优化：
1) OA集成，OA系统数仓(含集团数据)取数如OA业务对接人员有时间确定方案并进行接口实施与数据测试；
2）集团智能监控平台进度跟进；
3) 平台日常运维以及其他可能存在的测试与问题处理；
二、工塑纪检平台
1）完成CRM报表新接口与新增字段取数以及报表展示；
2）完成ERP存货模块芮城数据合并；
三、淮河化工纪检平台
1）如淮河化工系统流程完全确定的情况下，完成方案的设计与数据取数；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('cf35fe93-5624-4617-a1c9-c3d4a0512f5d', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '重要里程碑: 2024-03-18 00:00:00', '2024-03-18 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('0591519e-7e7d-4dcf-a2ab-eafe7067c535', '8437f2eb-a7a8-4180-9d58-18026c615073', NULL, NULL, '八月: 1、跟进漏洞修复相关工作。', '1、跟进漏洞修复相关工作。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('c1bff745-b609-4eea-8d95-58f2900a04c3', '8437f2eb-a7a8-4180-9d58-18026c615073', NULL, NULL, '重要里程碑: 2025-03-31 00:00:00', '2025-03-31 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('13e7197e-ba38-4810-bd69-efecf7247bff', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '十一月: 中化高纤：
1、待晓菲进一步测试产成品虚拟仓库方案后再与用户沟通
工塑：
1、跟进与PIMP联调测试', '中化高纤：
1、待晓菲进一步测试产成品虚拟仓库方案后再与用户沟通
工塑：
1、跟进与PIMP联调测试配方检测对接工作
开始研发数据化工作交接', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('cf9294f9-353a-44a8-8fb6-acee9ee6857f', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '十二月: 1、中化高纤：12月1日召集用户开会讨论新方案，方案确定后开展开发工作。
2、工塑：继续配合PIMP', '1、中化高纤：12月1日召集用户开会讨论新方案，方案确定后开展开发工作。
2、工塑：继续配合PIMP项目组测试。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('eb2bdfc3-7422-41f9-8638-8bd1c9429175', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '待办事项: 结合2026年预算编制。11月底完成初步调研，12月初与关总讨论', '结合2026年预算编制。11月底完成初步调研，12月初与关总讨论', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('dd7a34a8-bfa9-48cb-98f0-02ae5cac2c23', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '十二月: 调研事业部下属20家HSE自建系统企业；
组织按照集团调研方案和计划开展调研。', '调研事业部下属20家HSE自建系统企业；
组织按照集团调研方案和计划开展调研。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('1ace12b8-e56f-4361-b270-e9cfdf708c4b', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '十二月: 1 、硬件和网络 网闸、防火墙调试
2 、服务器及网络 集团与瑞祥办公网络端口申请 
3 、报警模块', '1 、硬件和网络 网闸、防火墙调试
2 、服务器及网络 集团与瑞祥办公网络端口申请 
3 、报警模块 报警管理M&R组态
4 、详细设计 详细设计讨论签署 
5、能源模块
能源管理数据、报表收集
6 、MES程序部署 未开始 
7 、能源流程图绘制 关键用户 指导用户进行绘制
8、 实时数据 各装置核查、校对报表工组关键用户
9 、电力接口 和远API接口讨论确认', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('e81ab1cf-56fc-481f-9689-204e2077dc82', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '一月: 1、能源统计报表开发并进行数据验证
2、能碳管理用户培训及编制用户手册
3、报警管理数据验证
1、权', '1、能源统计报表开发并进行数据验证
2、能碳管理用户培训及编制用户手册
3、报警管理数据验证
1、权限管理 车间角色收集组态
2、权限管理 用户信息组态用户角色
3、数据收集 能源统计报表收集
4、报警管理 报警数据与DCS数据一致性验证 
开展建议方案审核
编制需求说明书
编制需求说明书
关总：要加快进度，争取2025Q1完成寻源。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('b5bbec65-2742-4cdd-acae-77390f3bdc7c', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '二月: 1、瑞祥MES工艺报警管理系统试运行，梳理优化内容
2、瑞泰MES需求确认及整理事业部立项材料', '1、瑞祥MES工艺报警管理系统试运行，梳理优化内容
2、瑞泰MES需求确认及整理事业部立项材料', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('4ad64ade-d24e-44cd-b963-bd1c88b00fbe', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '三月: 1、正式提交事业部立项，等待审批；
2、物理服务器自行购买。', '1、正式提交事业部立项，等待审批；
2、物理服务器自行购买。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('e1323576-cd34-458c-80c2-5f9f873b5df0', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '四月: 1.组织采购谈判及评审；
2.谈判结果审批；
3.单一来源谈判结果公示3天；', '1.组织采购谈判及评审；
2.谈判结果审批；
3.单一来源谈判结果公示3天；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('42c0d985-44e0-4259-b4f3-45feb9dcf7bd', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '五月: 1.需求调研：各模块基础数据收集；业务流程图绘制；需求说明书编制和确认；
2.OPC授权采购进行中；', '1.需求调研：各模块基础数据收集；业务流程图绘制；需求说明书编制和确认；
2.OPC授权采购进行中；
3.MES云服务器租赁扩容准备中；
4.软硬件现场安装调试；
5.MES标准开发培训；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('c53bab6f-63c6-473c-adfd-444280d630f8', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '六月: 1.蓝图设计：接口方案预评审，设计文档预评审；
2.基础设施：瑞祥PHD OPC服务器更换并部署，瑞', '1.蓝图设计：接口方案预评审，设计文档预评审；
2.基础设施：瑞祥PHD OPC服务器更换并部署，瑞泰OPC DA&AE授权采购，现场PKS采集可靠性验证；
3.瑞祥实施：工艺流程图绘制；工艺技控点管理建模；物料计量点组态；
4.瑞泰实施：PHD数据采集组态、流程图收集；工艺流程图绘制；物料计量点组态；能源计量点组态；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('e17e73c9-018b-4edb-b2d6-86bb7146bd1c', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '七月: 1.分解模块功能开发、测试、培训、上线、问题处理等各阶段任务；设计文档签字；
2.基础设施：瑞泰网络', '1.分解模块功能开发、测试、培训、上线、问题处理等各阶段任务；设计文档签字；
2.基础设施：瑞泰网络迁移改造（尼龙66、湿氧采集可靠性问题查找、氯代酯网络不通的调试），OPC DA&AE 采购；
3.瑞祥实施：工艺管理模块：工艺流程图绘制，报表工作；物料管理模块：物料计量组态；生产调度管理：组态；操作管理：组态；
4.瑞泰实施：工艺管理模块：报表开发；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('f9a95279-79cd-49fe-9492-c9e642f9235c', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '八月: 1.基础设施：湿氧待下次停车修改OPC服务账号密码以完成采集；Route功能迁移至PHD Shado', '1.基础设施：湿氧待下次停车修改OPC服务账号密码以完成采集；Route功能迁移至PHD Shadow服务器工作；
2.瑞祥实施：
基础设施：网络安全检查的问题整改。
2.1：工艺管理模块；2.2：物料管理模块；2.3：调度管理模块；2.4：持续改善模块；2.5：操作管理模块；2.6：系统集成接口；
3.瑞泰实施：
3.1：工艺管理模块；3.2：物料管理模块；3.3：能源管理模块；3.4：报警管理模块；3.5：生产统计模块；3.6：批次管理模块；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9d8fc4ea-5a82-4ec1-a220-a18faaffefe6', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '九月: 1.瑞祥实施：
基础设施：网络安全检查的问题整改。
1.1：工艺管理模块；1.2：物料管理模块；1.', '1.瑞祥实施：
基础设施：网络安全检查的问题整改。
1.1：工艺管理模块；1.2：物料管理模块；1.3：调度管理模块；1.4：持续改善模块；1.5：操作管理模块；1.6：生产统计模块；1.7：生产计划模块；1.8：系统集成接口；
2.瑞泰实施：
2.1：工艺管理模块；2.2：物料管理模块；2.3：调度管理模块；2.4：持续改善模块；2.5：操作管理模块；2.6：生产统计模块；2.7：生产计划模块；2.8：系统集成接口；2.9：能源管理模块；
2.10：报警管理模块；2.11：批次管理模块；
*SAP接口主数据、BOM、计划部分正在协调是否可以提前开展，报工部分正在调研三家工厂方案是否一致；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('99cfcbeb-6a8e-40f0-bbe8-6a137f47793c', '971eee5d-6f7c-4c25-b533-2e8e88ffff89', NULL, NULL, '待办事项: 停止跟踪', '停止跟踪', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('54d84def-9109-4592-9c73-7bb3887c071f', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '十一月: 1.瑞祥瑞泰上线试运行；
2.瑞泰存销数据WMS取数，预计11月初商务确定后开展；
3.瑞泰一卡通修', '1.瑞祥瑞泰上线试运行；
2.瑞泰存销数据WMS取数，预计11月初商务确定后开展；
3.瑞泰一卡通修正数据回传MES，预计11月初开始调试；
4.瑞祥绿色工厂审核对于能碳模块的需求；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('dc1ccb07-10c7-41f9-804a-f6ef73e41fc1', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '十二月: 1.瑞祥瑞泰上线试运行，问题跟踪和修复；
2.瑞泰存销数据WMS取数，预计11月初商务确定后开展；
', '1.瑞祥瑞泰上线试运行，问题跟踪和修复；
2.瑞泰存销数据WMS取数，预计11月初商务确定后开展；
3.三家工厂的报工集成WMS/SAP调试；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d6506fee-6925-4544-b160-93433f7753f6', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '重要里程碑: 2025-04-10 00:00:00', '2025-04-10 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('241dcd0a-29b6-4785-8ee4-e795343ffb4f', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '待办事项: 中间体、河北新材、圣奥', '中间体、河北新材、圣奥', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ad1b4ab5-af98-47a3-9c82-90e46906a69d', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '十月: 霍尼MES工厂运维安排。', '霍尼MES工厂运维安排。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('855dd4ee-2d16-4a66-b9c8-1fce8e4f0d73', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '十一月: 工厂运维体系讨论（包含河北、圣奥）；', '工厂运维体系讨论（包含河北、圣奥）；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('1da60e69-34c2-470c-bcdf-e65aaad4fc99', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '十二月: 1.统一运维体系讨论和编制；
2.2026年运维外包统筹，组建谈判团队。', '1.统一运维体系讨论和编制；
2.2026年运维外包统筹，组建谈判团队。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a9cc23a8-fbbc-4332-a689-2dc70a119dcc', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '待办事项: 可研范围：中间体、河北新材、圣奥；
立项：集中统一在事业部立项。', '可研范围：中间体、河北新材、圣奥；
立项：集中统一在事业部立项。', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('8379450b-dc4c-4e71-b51c-056fffd6c8a5', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '十月: 霍尼MES优化统一立项；', '霍尼MES优化统一立项；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('4ad3c4cb-477d-47ae-acb7-787695b04714', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '十一月: 收集优化需求；', '收集优化需求；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('1b1a9f64-0e04-44d7-bc6f-8a44709b178b', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '十二月: 1.收集优化需求；
2.梳理需求;', '1.收集优化需求；
2.梳理需求;', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('471f5c62-be34-4b99-b03a-0d3033bf43ea', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '待办事项: 中间体三家工厂同步推进，2025年完成立项。
2026年重点项目，做好方案评估。', '中间体三家工厂同步推进，2025年完成立项。
2026年重点项目，做好方案评估。', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ca4e8342-c75a-4986-9e0f-9f3303071532', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '六月: 1、进行瑞祥现场情况调研；
2、分析瑞恒EPM方案(周三容知提供）。
3、沟通瑞泰的EPM需求情况。', '1、进行瑞祥现场情况调研；
2、分析瑞恒EPM方案(周三容知提供）。
3、沟通瑞泰的EPM需求情况。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('b373725f-416a-4189-a64e-66c71e55b852', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '七月: 1、整合中间体三家整体方案，进行立项材料的编写', '1、整合中间体三家整体方案，进行立项材料的编写', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('56eccc18-7ed0-48bd-a13b-2c84ce48d2b5', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '八月: 1、收集各工厂的评审意见，完善项目预期价值；
2、编写需求说明书、立项报告等内容。', '1、收集各工厂的评审意见，完善项目预期价值；
2、编写需求说明书、立项报告等内容。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9ed05628-3ad0-4f6a-a46e-731b3891dce6', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '九月: 1、完成瑞恒在线监测设备清单的收集；
2、完成费用评估；
3、完善立项报告。
周三必须提交初版。', '1、完成瑞恒在线监测设备清单的收集；
2、完成费用评估；
3、完善立项报告。
周三必须提交初版。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('b5dab05a-52eb-4028-8ad6-37525e01cb13', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '十月: 1、开会讨论需求说明书；', '1、开会讨论需求说明书；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('53b6591e-cb6d-4b81-aa24-adc5c10961bf', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '十一月: 1、组织供应商在瑞泰进行调研；', '1、组织供应商在瑞泰进行调研；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('e95e4e44-28b4-49c3-a1cc-2ae12669b9dc', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '十二月: 1、进行第五家供应商在瑞祥、瑞泰的调研；
2、进行容知供应商在瑞恒的再次调研（没有电压信号的设备）；', '1、进行第五家供应商在瑞祥、瑞泰的调研；
2、进行容知供应商在瑞恒的再次调研（没有电压信号的设备）；
3、进行需求说明书的完善；
4、明确看护服务模式及数据访问方式；
5、沟通采购方式。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d400dc35-8d54-4ba1-a56e-fec56f660008', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '待办事项: 结合2025年ERP升级项目对接可能的变化。
关注运维管理的各家需求和数据兼容性。', '结合2025年ERP升级项目对接可能的变化。
关注运维管理的各家需求和数据兼容性。', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d8a2c407-8b86-4d77-9f7f-b58b4ae1c7d6', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '十二月: 1、蓝图PPT汇报&《业务蓝图差异确认书》签署
2、瑞恒WMS工单编写
3、MES接口字段确认', '1、蓝图PPT汇报&《业务蓝图差异确认书》签署
2、瑞恒WMS工单编写
3、MES接口字段确认
4、EAM接口字段确认
5、一卡通接口确认
☆☆☆☆☆持续重点跟踪的事件：
1：辅材采购业务集团要求全部需进SRM，瑞恒目前存在有部分物资未进SRM，需确认是否已沟通好全部进SRM;2：易制毒易制爆物资进出厂管控需确认最终是否在一卡通进行管控；3：瑞恒仓库网络覆盖需确认在WMS系统上线前（2025年2月28日）能否实现；4：WMS与立体库、LIMS、一卡通、OA、SAP接口字段对接需瑞恒本周与各个厂商沟通并确认接口字段对接时间以及后续推开发测试推进计划。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('2fde5b58-1e7a-4b4c-a819-0ec35242ae48', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '一月: 1、完成WCS与包装机对接方案及WCS与WMS对接WCS方开发测试计划制定
2、完成EAM&WMS对', '1、完成WCS与包装机对接方案及WCS与WMS对接WCS方开发测试计划制定
2、完成EAM&WMS对接EAM方开发测试计划制定
3、MES&WMS接口开发
4、SAP&WMS接口开发
5、完成一卡通&WMS测试环境地址对接配置
6、PDA功能开发及内测
7、测试脚本编写
8、静态数据收集模板整理', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('f3ecb818-1114-4420-b618-9130813babe5', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '二月: 1、组织用户进行单元测试及培训
2、继续完成MES接口开发
3、部分业务接口数据微调', '1、组织用户进行单元测试及培训
2、继续完成MES接口开发
3、部分业务接口数据微调', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('047619d6-5a19-40b7-a182-e9deea036d97', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '三月: 1、跟进关账期间各项业务数据补录（重点跟进销售、生产）
2、跟进流量卡、货位标签纸采购
3、跟进ME', '1、跟进关账期间各项业务数据补录（重点跟进销售、生产）
2、跟进流量卡、货位标签纸采购
3、跟进MES、EAM方生产环境接口地址配置（WMS生产环境已部署完毕）
4、现场协助一线用户各项业务开展
5、处理上线期间用户反馈优化项', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('72d6a4c1-4d4b-4d1c-bdff-65f2d34bbb40', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '四月: 1、瑞恒WMS线上运维，MES&EAM与WMS集成业务跟踪
2、瑞祥WMS前期沟通（立项、需求、流程', '1、瑞恒WMS线上运维，MES&EAM与WMS集成业务跟踪
2、瑞祥WMS前期沟通（立项、需求、流程等事务沟通）', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('f9602087-9150-4d3f-9686-d541a9243981', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '五月: 1、瑞祥WMS属地立项材料', '1、瑞祥WMS属地立项材料', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ef39c278-e02a-457d-8da1-dc8f3d7567c4', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '六月: 1、SOW需求说明书初审
2、商务合同部分的汇报及下来的商务谈判
3、WMS服务器迁移，本次无需考虑', '1、SOW需求说明书初审
2、商务合同部分的汇报及下来的商务谈判
3、WMS服务器迁移，本次无需考虑信创要求。
4、三个工厂的罐存数据分析需求沟通。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ab83cd54-4e46-4e08-9020-221a1a237a6d', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '七月: 1、合同签订
2、项目启动准备', '1、合同签订
2、项目启动准备', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('65fa5505-6fc8-4355-8f53-dc4e28ee8c52', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '八月: 1 、报表需求调研 
2 、专项解决方案制定 
3 、专项讨论（辅材物资订单收货、工程物资、报损报溢', '1 、报表需求调研 
2 、专项解决方案制定 
3 、专项讨论（辅材物资订单收货、工程物资、报损报溢SAP对接） 
4 、WORD版本蓝图梳理编制 
5 、瑞祥本次WMS项目优化清单确认', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ee7e6312-d3f4-43be-b164-94521a38fad9', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '九月: 1、测试环境物料信息推送（SAP->WMS）
2、测试环境物料批次规则属性、批次特征分类，物料分配批', '1、测试环境物料信息推送（SAP->WMS）
2、测试环境物料批次规则属性、批次特征分类，物料分配批次特征，包装物包装规则维护
3、系统单元测试（到货验收单（含PDA）、采购入库单（含PDA）、生产订单、生产入库单 测试范围包含瑞泰、瑞恒、瑞祥）
4、系统功能开发（副产品入库、生产领料、物资领用出、退库、销售出库、物料信息）', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('f4975cdb-c97e-49dd-926a-77022b12a7db', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '十月: 1、组织用户UAT测试事前准备', '1、组织用户UAT测试事前准备', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('0fc62bce-b546-459e-87f3-cd7b4c8bb47a', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '十一月: 1、WMS系统上线支持，部分业务优化调整
2、开始增补需求采购工作', '1、WMS系统上线支持，部分业务优化调整
2、开始增补需求采购工作', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('1bb0247b-ac89-4cf5-8859-54b3876bf8b5', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '十二月: 1、处理上线问题清单中未关闭项
2、完成WMS项目验收报告签署
3、增补需求采购的商务谈判', '1、处理上线问题清单中未关闭项
2、完成WMS项目验收报告签署
3、增补需求采购的商务谈判', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('73510169-efcf-4540-9263-03c3192173f8', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '重要里程碑: 2025-07-31 00:00:00', '2025-07-31 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('fc58c5a4-6bfc-410c-8cfe-d5801d80b651', '5c168ab0-df2a-4e7f-8ab7-4d06e2d289cd', NULL, NULL, '待办事项: 结合ERP升级', '结合ERP升级', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('34f1450e-f516-4675-bc4a-e16139d556ba', '5c168ab0-df2a-4e7f-8ab7-4d06e2d289cd', NULL, NULL, '三月: 1、跟踪扬农月结推迟的实施情况；
2、发布《数字化转型组织》；
3、梳理工作实施', '1、跟踪扬农月结推迟的实施情况；
2、发布《数字化转型组织》；
3、梳理工作实施', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('db8b1bb8-5ed5-48b7-a099-9361ab4b52e9', '5c168ab0-df2a-4e7f-8ab7-4d06e2d289cd', NULL, NULL, '四月: 1、继续开展销售业务流梳理。
2、供应链中心流程梳理工作沟通', '1、继续开展销售业务流梳理。
2、供应链中心流程梳理工作沟通', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('705606c3-2502-489e-b5aa-2d689146e056', '5c168ab0-df2a-4e7f-8ab7-4d06e2d289cd', NULL, NULL, '五月: 1、OA&SAP工程服务计划流程到订单和付款业务流程改造
2、优化供应链11个采购管理流程审批流和节', '1、OA&SAP工程服务计划流程到订单和付款业务流程改造
2、优化供应链11个采购管理流程审批流和节点控制调整
3、采购&销售（中间体事业部）运费管理方案蓝图调整（参考全产业链方案）', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('618f8793-4305-4909-a1d6-73a7168f2345', '5c168ab0-df2a-4e7f-8ab7-4d06e2d289cd', NULL, NULL, '六月: 1、与业务确定运费及储运管控需求，设计物流一卡通优化事项。(资源以IT和业务方为主，供应商辅助)', '1、与业务确定运费及储运管控需求，设计物流一卡通优化事项。(资源以IT和业务方为主，供应商辅助)', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('4aaa6b43-93fe-4427-8b8a-d01138f9374c', '5c168ab0-df2a-4e7f-8ab7-4d06e2d289cd', NULL, NULL, '七月: 1、整理ERP升级优化需求（进行中）
2、业务流程管控优化
1)对接南通星辰CRM（接口测试）
2)', '1、整理ERP升级优化需求（进行中）
2、业务流程管控优化
1)对接南通星辰CRM（接口测试）
2)物流系统自身优化新增车辆VIP权限（重新验证测试）；现场批控仪对接发货（试运行转正常运行）；物流对接中间体CRM接口开发。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('cf490d82-4040-4259-97e7-feb148e73620', '5c168ab0-df2a-4e7f-8ab7-4d06e2d289cd', NULL, NULL, '八月: 1、整理ERP升级优化需求（汇总中）（关总：8月完成整理汇总）
2、业务流程管控优化
1）对接南通星', '1、整理ERP升级优化需求（汇总中）（关总：8月完成整理汇总）
2、业务流程管控优化
1）对接南通星辰CRM（正常运行）
2）物流系统微信小程序数据加密同步整改中。
3）中间体事业部运费管理方案评估（组织业务部门本周进行）
4)  集团本部&瑞祥甘油关联交易业务梳理（营销中心提出尽快打通此流程）', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('736c515f-66a0-4397-8a4e-23ae8b1214e8', '5c168ab0-df2a-4e7f-8ab7-4d06e2d289cd', NULL, NULL, '九月: ERP升级优化：
1）现有ERP对接外围系统接口梳理及升级改造费用评估；
2）9月汇报材料准备中（本', 'ERP升级优化：
1）现有ERP对接外围系统接口梳理及升级改造费用评估；
2）9月汇报材料准备中（本周完成并提交，下周一下午讨论）
业务流程管控优化：
1)采购供应商升降级OA审批字段完善（进行中）', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('bf6c6602-aeed-453f-a8f8-d306c179a303', '5c168ab0-df2a-4e7f-8ab7-4d06e2d289cd', NULL, NULL, '十月: ERP升级优化：
1）按需领导安排开展；
业务流程管控优化：
1)按需完成各项流程调整', 'ERP升级优化：
1）按需领导安排开展；
业务流程管控优化：
1)按需完成各项流程调整', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('51ea9a9d-ba08-4d06-8d8a-eeb125a33e36', '5c168ab0-df2a-4e7f-8ab7-4d06e2d289cd', NULL, NULL, '十一月: ERP升级优化：
1）配合完成ERP升级项目前期工作。
2）完成上会材料提交。
业务流程管控优化：
', 'ERP升级优化：
1）配合完成ERP升级项目前期工作。
2）完成上会材料提交。
业务流程管控优化：
1) 按需完成各项流程调整', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('0ad6a73c-ed33-44d1-87b2-b81bacab5d01', '5c168ab0-df2a-4e7f-8ab7-4d06e2d289cd', NULL, NULL, '十二月: ERP升级优化：
1）配合完成ERP升级项目组织架构；
业务流程管控优化：
1) 按需完成各项流程调', 'ERP升级优化：
1）配合完成ERP升级项目组织架构；
业务流程管控优化：
1) 按需完成各项流程调整', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('72ee260e-9dc6-4116-8ae3-7f5179d3ef4a', '4755cd9b-3a46-4fd9-a91e-39d1dfcef173', NULL, NULL, '待办事项: 3月：
（三）HSE监管数据一致率低于90%，扣0.2分。
（四）HSE系统操作规范率低于95%，扣', '3月：
（三）HSE监管数据一致率低于90%，扣0.2分。
（四）HSE系统操作规范率低于95%，扣0.2分。', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d3b1ddb4-4538-4ec2-9293-f3507e076433', '4755cd9b-3a46-4fd9-a91e-39d1dfcef173', NULL, NULL, '十二月: 1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理', '1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('4a675940-bb46-42fe-b1fb-64d2bb4d6b9e', '4755cd9b-3a46-4fd9-a91e-39d1dfcef173', NULL, NULL, '一月: 1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理', '1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ce5a1005-1a0b-4a4b-8a86-e050f79919bd', '4755cd9b-3a46-4fd9-a91e-39d1dfcef173', NULL, NULL, '二月: 1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理', '1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('b9f5096f-7cb0-4d56-95cb-9ce558f57291', '4755cd9b-3a46-4fd9-a91e-39d1dfcef173', NULL, NULL, '三月: 1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理', '1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('e49cda78-f027-493b-9402-d87a458f7d3d', '4755cd9b-3a46-4fd9-a91e-39d1dfcef173', NULL, NULL, '四月: 1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理', '1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('671a95e6-f69b-47aa-8dfe-fdb4ac391605', '4755cd9b-3a46-4fd9-a91e-39d1dfcef173', NULL, NULL, '五月: 1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理', '1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('1f06f677-c90e-4656-9747-993f45a9cbdb', '4755cd9b-3a46-4fd9-a91e-39d1dfcef173', NULL, NULL, '六月: 1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理
3、持续跟进企', '1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理
3、持续跟进企业数据和监管侧数据一致性、规范性问题', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('222b00d4-d03f-4418-907e-f34c84844c09', '4755cd9b-3a46-4fd9-a91e-39d1dfcef173', NULL, NULL, '七月: 1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理
3、持续跟进企', '1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理
3、持续跟进企业数据和监管侧数据一致性、规范性问题', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('82697291-0cff-4b14-97ad-44e6223454a2', '4755cd9b-3a46-4fd9-a91e-39d1dfcef173', NULL, NULL, '八月: 1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理
3、持续跟进企', '1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理
3、持续跟进企业数据和监管侧数据一致性、规范性问题', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('23e99db5-f0d7-4c4d-8c97-78e5d09ebd47', '4755cd9b-3a46-4fd9-a91e-39d1dfcef173', NULL, NULL, '九月: 1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理
3、持续跟进企', '1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理
3、持续跟进企业数据和监管侧数据一致性、规范性问题', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('db8f0bc2-e3e8-4fe6-8f37-c0929876861c', '4755cd9b-3a46-4fd9-a91e-39d1dfcef173', NULL, NULL, '十月: 1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理
3、持续跟进企', '1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理
3、持续跟进企业数据和监管侧数据一致性、规范性问题', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('4039be47-ad9b-4671-8562-f2c8b9a3d88c', '4755cd9b-3a46-4fd9-a91e-39d1dfcef173', NULL, NULL, '十二月: 1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理
3、持续跟进企', '1、完成统建系统的数据集成工作，推进新系统的使用
2、自建系统重要问题继续跟踪和处理
3、持续跟进企业数据和监管侧数据一致性、规范性问题', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a9b1af4b-7768-46b3-9afd-19e044ed2cfd', '4755cd9b-3a46-4fd9-a91e-39d1dfcef173', NULL, NULL, '重要里程碑: 2024-05-01 00:00:00', '2024-05-01 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9046a21c-58d7-438f-aafd-0fab160c6291', '6fdaa9be-7af9-4820-afa5-b1327964606e', NULL, NULL, '十二月: 1.开展人员定位风险聚集新功能上线；
2.完成双重预防模块内部测试和问题整改，开展用户测试；
3.开', '1.开展人员定位风险聚集新功能上线；
2.完成双重预防模块内部测试和问题整改，开展用户测试；
3.开展生产管理、成本管理、任务工单、物资领用优化等功能开发；
4.开展作业票上线运行支持和bug问题整改；
5.开展三维物联网平台功能开发和建模；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('45232ffd-d107-4bac-9c4d-1fcb4a3823c2', '6fdaa9be-7af9-4820-afa5-b1327964606e', NULL, NULL, '一月: 1.开展双重预防模块上线试运行；
2.开展生产管理槽车排队叫号及槽车畅行上线试运行；
3.开展设备管', '1.开展双重预防模块上线试运行；
2.开展生产管理槽车排队叫号及槽车畅行上线试运行；
3.开展设备管理模块码头基础数据实施； 
4.开展多因子集成联调。
5。明确整体计划即实施进度，下次会议回顾。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('615cc0b9-5c8f-4c4c-b328-d4b599d7e055', '971eee5d-6f7c-4c25-b533-2e8e88ffff89', NULL, NULL, '十二月: 承包商-已完成统建系统的建设，待集团发布标准完成自建系统的数据对接
BD-已完成所有企业年度任务，核', '承包商-已完成统建系统的建设，待集团发布标准完成自建系统的数据对接
BD-已完成所有企业年度任务，核实、上报项目进度
固废-配合集团调研', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('df2315d1-4afd-47cd-9153-16657a859ae7', '6fdaa9be-7af9-4820-afa5-b1327964606e', NULL, NULL, '二月: 1，针对二期已上线的模块测试结果中与建设预期不符的共计86项，进行专项会议，讨论最终实施方案
2，车', '1，针对二期已上线的模块测试结果中与建设预期不符的共计86项，进行专项会议，讨论最终实施方案
2，车辆作业共计19项问题需在本周与供应商协同解决（槽车畅行模块小程序10项，基础数据2项，罐区作业6项，作业委托1项）
3，基础服务器优化，部分并发量高/低的模块服务器需要优化配置，并新增2台双预防服务器。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('31cabd91-c80f-4d33-a648-19e1ecbbb975', '6fdaa9be-7af9-4820-afa5-b1327964606e', NULL, NULL, '三月: 二月开发进度汇总：
1，总计建设一级功能模块11个：包括安全健康环保，报表应用，成本管理，绩效管理，', '二月开发进度汇总：
1，总计建设一级功能模块11个：包括安全健康环保，报表应用，成本管理，绩效管理，平台综合需求，设备完整性管理，生产管理，物联网平台建设，
物资管理，移动应用，政府上报接口开发，
2，建设二级功能63个，二级开发项89个:已完成(59),上线试运行(16),测试中(10),功能待调整(1),接口开发(1),开发已完成(1),实施中(1)
3，整体完成率为66%，原定于2月28日完成全部开发工作，由于需求变更或供应商资源调配问题现有29个开发项延误。
三月实施计划：
1，督促供应商优先完成所有计划开发项的开发。
2，（新增项）完成广播和AI报警联动响应开发，完成火灾报警数据接入；
3，完成双重预防隐患治理、安全检查、专项检查等变更需求开发；
4，完成承包商、职业健康、环保管理优化内容的bug整改及上线；
5，完成移动端消息推送和报警处置；
6，完成报表实施。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('be1c1841-5555-4520-ba31-872230f6cc70', '6fdaa9be-7af9-4820-afa5-b1327964606e', NULL, NULL, '四月: 4月计划：
1.完成安全检查和专项检查功能开发及上线；
2.完成中化集团双防系统接口上报；
3.完成', '4月计划：
1.完成安全检查和专项检查功能开发及上线；
2.完成中化集团双防系统接口上报；
3.完成设备app功能调试及上线；
4.开展报表实施。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a3d30c43-16a5-449f-8236-ed3812e06075', '6fdaa9be-7af9-4820-afa5-b1327964606e', NULL, NULL, '五月: 报表：
尽快完成各部门报表需求整理，对各部门的T1~T3会议报表实现全覆盖。
双重预防：
完成双预防', '报表：
尽快完成各部门报表需求整理，对各部门的T1~T3会议报表实现全覆盖。
双重预防：
完成双预防数据上报，完成对监管部门及事业部以及集团的数据上报工作。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('f47256f9-d835-4c12-b203-47c2cfe74a80', '6fdaa9be-7af9-4820-afa5-b1327964606e', NULL, NULL, '六月: 智慧管理系统二期-上线后反馈问题处理
一、协同保障部模块
船舶预确报/进出港计划优化

问题8/9：', '智慧管理系统二期-上线后反馈问题处理
一、协同保障部模块
船舶预确报/进出港计划优化

问题8/9：来港/去港信息分离展示（优化，高优）

新增问题：委托单查看时信息合并展示（优化）

负责人：胡晓雪

计划完成：6月16日前

管输作业委托新增功能

问题13：每日9:30邮件计量提醒（新增需求，高影响）

问题14：每日10:00计量确认提醒（新增需求，高影响）

负责人：胡晓雪

计划完成：6月20日前

危化品车辆管理

新增问题：运输公司输入查找功能（优化，中影响）

问题19：删除无效列展示（优化）

负责人：胡晓雪

计划完成：6月18日前

二、合同管理模块
码头账单管理修复

问题22-34：收费周期错误、NOR保存问题、服务项目错乱等（共13项Bug，高影响）

负责人：胡晓雪

计划完成：6月15日前（部分已处理需验证）

货权转移与仓储账单

问题36：台账逻辑错误、导出信息空白（Bug，高影响）

问题37：仓储账单功能完善（高影响）

负责人：胡晓雪

计划完成：6月25日前

三、库存管理模块
库存调节与损耗

问题40：库存调节备注不显示/多附件上传（优化，高影响）

问题42：库存台账数据准确性校验（优化，高影响）

负责人：胡晓雪

计划完成：6月22日前

四、承包商管理模块（HSE部/技术部）
承包商资质与状态管理

问题50：资质到期提醒（需求变更）

问题52：承包商状态分类（新增需求）

负责人：杨东/王磊

计划完成：6月20日前

人员信息优化

问题57：资料分类拆分/到期暂停作业（新增需求）

问题58：人员状态管理（新增需求）

负责人：杨东/王磊

计划完成：6月25日前

五、操作部模块
统一待办功能优化

问题77：待办任务提示铃声（优化）

问题79：待办页面自动更新（优化）

负责人：张立

计划完成：6月18日前

绩效管理整合

问题96/97：巡检/检尺等作业纳入个人绩效（系统使用优化）

负责人：宋歌

计划完成：6月20日前

六、仓储三维物联网模块
特殊作业统计优化

问题107：码头作业统计添加（新增需求）

问题110：异常作业内容可视化（新增需求）

负责人：黄成

计划完成：6月15日前

联动预警流程

问题108：误报需强制填写处理信息（新增需求）

负责人：刘云芳

计划完成：6月12日前（紧急）

七、其他高优问题
STOP观察统计（HSE部）

问题103/104：码头/仓储分区统计（新增需求）

负责人：黄贤臻

计划完成：6月15日前

层级会议异常清单

问题114：支持时间段查询与导出（需求变更）

负责人：刘云芳

计划完成：6月28日前

计划说明
优先级排序：高影响（Bug/新增需求）> 待处理 > 优化类问题。

风险项：

问题15（操作日志报表）因技术限制暂无法处理，需协调资源。

问题51（承包商批量上传）关闭，建议手动处理。

验证安排：6月25-30日集中回归测试，重点关注已标记“待验证”项（如仓储账单、绩效模块）。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('50dc0f5c-ade5-4025-a3c4-3281cf932a61', '6fdaa9be-7af9-4820-afa5-b1327964606e', NULL, NULL, '七月: 1.系统上线试运行技术支持；
2.开展电量点位梳理（新增需求）及二期电量数据采集。', '1.系统上线试运行技术支持；
2.开展电量点位梳理（新增需求）及二期电量数据采集。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('b05859c2-2fee-43f0-848f-05f65cb6ce46', '6fdaa9be-7af9-4820-afa5-b1327964606e', NULL, NULL, '八月: 8月计划：
1.系统上线试运行技术支持；
2.开展槽车作业启泵流程功能修改，以及与绩效模块的数据关联', '8月计划：
1.系统上线试运行技术支持；
2.开展槽车作业启泵流程功能修改，以及与绩效模块的数据关联（新增需求）。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('65e6868b-5483-4fe6-9d8c-03924fef99ce', '6fdaa9be-7af9-4820-afa5-b1327964606e', NULL, NULL, '重要里程碑: 2024/7', '2024/7', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('2ecb79f5-5dda-4c72-a85a-33264ed69283', '2abd6d04-c2e8-4284-9477-fc7f1bb7f67c', NULL, NULL, '待办事项: 化工事业部考核目标：PID整定：9套；APC投用：4套。', '化工事业部考核目标：PID整定：9套；APC投用：4套。', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d16cb873-d4b7-4f36-93b5-2ab196af1ef4', '2abd6d04-c2e8-4284-9477-fc7f1bb7f67c', NULL, NULL, '十二月: 编制采购方案
准备两家候选供应商谈判
初步计划12-30这周谈判，等待瑞恒领导决策。', '编制采购方案
准备两家候选供应商谈判
初步计划12-30这周谈判，等待瑞恒领导决策。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('b75b7021-20a1-49f2-849d-00882712fe6e', '2abd6d04-c2e8-4284-9477-fc7f1bb7f67c', NULL, NULL, '一月: 提交OA采购申请审批流程；
召开采购谈判会议；
公示采购结果；', '提交OA采购申请审批流程；
召开采购谈判会议；
公示采购结果；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9ee60ab5-887e-4535-800a-d3bacdfc8141', '2abd6d04-c2e8-4284-9477-fc7f1bb7f67c', NULL, NULL, '三月: 探讨建设中间体事业部的先进控制团队。', '探讨建设中间体事业部的先进控制团队。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('4c649139-e6ae-471c-859a-6cb35d1156c0', '2abd6d04-c2e8-4284-9477-fc7f1bb7f67c', NULL, NULL, '四月: 1、瑞恒APC按计划实施；
2、瑞祥APC按计划实施；
3、瑞泰APC开展项目可研', '1、瑞恒APC按计划实施；
2、瑞祥APC按计划实施；
3、瑞泰APC开展项目可研', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('dbbc651d-be69-4e9d-8919-31232921aa31', '2abd6d04-c2e8-4284-9477-fc7f1bb7f67c', NULL, NULL, '六月: 瑞恒：酚酮装置APC：●●继续开展酚酮车间、环氧丙烷车间和丙烷脱氢车间基础自动化提升工作。●●继续投', '瑞恒：酚酮装置APC：●●继续开展酚酮车间、环氧丙烷车间和丙烷脱氢车间基础自动化提升工作。●●继续投运调试苯酚精馏塔APC控制器。●●继续投运调试原料苯酚塔APC控制器。●●继续投运调试原料分离塔APC控制器。●●继续投运调试丙酮塔APC控制器。●●搭建异丙苯单元APC控制器。
瑞祥：软硬件采购和安装；DCS组态编辑；APC建模及组态。
瑞泰：开展采购寻源。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('baaa9a69-c4c7-498a-9556-b30c898c732f', '2abd6d04-c2e8-4284-9477-fc7f1bb7f67c', NULL, NULL, '重要里程碑: 2025-02-21 00:00:00', '2025-02-21 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('100b7a2b-2db8-48ee-813c-15f21df535a1', '50f7c3cd-57ba-406b-92a1-2738c4f9ec0f', NULL, NULL, '待办事项: 中控、华为解决方案', '中控、华为解决方案', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('3d026968-dadc-4589-8ec9-44e63eefde62', '80db9432-84d2-441b-b497-c867a8308b65', NULL, NULL, '待办事项: 收集使用情况的数据（成果数据）：各类的数据量，效果情况。项目组已做准备。

组织向邱总做试运行状体汇', '收集使用情况的数据（成果数据）：各类的数据量，效果情况。项目组已做准备。

组织向邱总做试运行状体汇报。春节后。', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('6b316142-1122-4f29-8cbc-2b332fc3ba7c', '80db9432-84d2-441b-b497-c867a8308b65', NULL, NULL, '十二月: 1、上线检查材料准备；
2、物料管理流程梳理及集成沟通；
3、移动审批事项跟进；
4、HSE接口调试', '1、上线检查材料准备；
2、物料管理流程梳理及集成沟通；
3、移动审批事项跟进；
4、HSE接口调试；
5、PHD扩容事项跟进；
6、电力系统数据接入事项跟进；
7、T1、T2会议试用；
8、上线试运行支持。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('031d9657-313f-45ff-98b6-07570f7a15eb', '80db9432-84d2-441b-b497-c867a8308b65', NULL, NULL, '一月: 1、生产成本报表优化；
2、2025年年计划录入；
3、卓越运营模块使用推进；
4、ERP、WMS、', '1、生产成本报表优化；
2、2025年年计划录入；
3、卓越运营模块使用推进；
4、ERP、WMS、事前算赢系统集成推进；
5、PHD扩容事项跟进；
6、电力数据接入；
7、渗透测试、基线检查；
8、移动端试用及优化；
9、上线试运行支持。
1、ERP系统集成推进；
2、WMS系统集成推进；
3、事前算赢系统集成推进；
4、T3会议组态；
5、电力系统接入推进；
6、上线试运行支持。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ee45d04a-64f5-4529-b513-939410faffcb', '80db9432-84d2-441b-b497-c867a8308b65', NULL, NULL, '二月: 1、生产成本功能优化；
2、卓越运营模块使用推进；
3、ERP、WMS、OA系统集成推进；
4、上线', '1、生产成本功能优化；
2、卓越运营模块使用推进；
3、ERP、WMS、OA系统集成推进；
4、上线前安全检查漏洞修复；
5、项目剩余事项梳理；
6、功能清单梳理；
7、问题清单梳理；
8、属地汇报准备；
9、交付物准备；
10、运维机制建立。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('3b199a23-4356-4e9c-b51a-7e627218c791', '80db9432-84d2-441b-b497-c867a8308b65', NULL, NULL, '重要里程碑: 2024-07-04 00:00:00', '2024-07-04 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('5c2f0d30-603d-4846-a562-df16d7d08588', '0f20a971-b51b-4773-ab71-e08691ee7d68', NULL, NULL, '待办事项: 每周周例会正常召开；
春节前上线。', '每周周例会正常召开；
春节前上线。', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a4ada27f-9682-4e69-9ada-9262f69e5c6b', '0f20a971-b51b-4773-ab71-e08691ee7d68', NULL, NULL, '十二月: 商务部分：
1、芮城支付软件费用
2、霍尼韦尔软件支付准备
属地准备：
1、芮城：推进网闸采购工作
', '商务部分：
1、芮城支付软件费用
2、霍尼韦尔软件支付准备
属地准备：
1、芮城：推进网闸采购工作
2、添加剂：
   安徽圣奥：12.3计划组织用户培训
   山东圣奥：报警点位组态，层级组态，权限配置
   泰安圣奥：报警点位组态，层级组态，权限配置
   富比亚：软件授权采购谈判
   淮河化工：报警点位组态，层级组态，权限配置
   河北三家：网闸，服务器，授权采购中，预计12.10到货
3、事业部：
1、推进多因子集成开发
2、芮城网页访问测试', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('85f38bb8-4c9e-4809-96ba-84cf32741405', '0f20a971-b51b-4773-ab71-e08691ee7d68', NULL, NULL, '一月: 属地准备：
   安徽圣奥：用户上线试用，部分乱码显示乱问问题正在处理
   山东圣奥：用户上线试用', '属地准备：
   安徽圣奥：用户上线试用，部分乱码显示乱问问题正在处理
   山东圣奥：用户上线试用
   泰安圣奥：用户上线试用
   富比亚： 用户上线试用，用户现场培训
   淮河化工：用户上线试用
   芮城：用户试用中，用户无法登录多因子，联系配置
   河北三家：用户试用中，数据采集核对，报警点位整理及优化
事业部：
1、上线前测试，基础架构团队负责，目前已提交所有材料，测试预计一周
2、上线报告准备审查
3、各家提供报警优先级对应关系', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('5c3acede-d349-4d22-b9f1-b752339a43cf', '0f20a971-b51b-4773-ab71-e08691ee7d68', NULL, NULL, '重要里程碑: 2024-08-01 00:00:00', '2024-08-01 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('f0332647-e713-45bd-b869-658bcd31a561', 'da24b04f-9d2f-408b-af24-d4475bba5313', NULL, NULL, '待办事项: 完成率100%；', '完成率100%；', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('913601a6-2432-42d0-ac25-f8acbee92f5d', 'da24b04f-9d2f-408b-af24-d4475bba5313', NULL, NULL, '十二月: 1、 质量原始记录模版组态
2、物料管理的组态
3、 能源管理组态
4、用户台账测试
5、 产品出厂', '1、 质量原始记录模版组态
2、物料管理的组态
3、 能源管理组态
4、用户台账测试
5、 产品出厂流程测试
6、滏鼎报警事件数据采集测试', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('3e102050-267a-4dbc-8a12-c8107f74bb7a', 'da24b04f-9d2f-408b-af24-d4475bba5313', NULL, NULL, '一月: 1、装置计量组态，能源管理组态，下周完成
2、设备动态监视，安装完成，系统组态调试
3、色谱仪数据采', '1、装置计量组态，能源管理组态，下周完成
2、设备动态监视，安装完成，系统组态调试
3、色谱仪数据采集调试
4、HSE接口调试，上周未完成工作
5、地磅接口调试，上周未完成工作
6、Uniformance insight 动态图更新。
7、质检模块试运行（全数据录入）
8、多因子登录mes测试', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('61a859a6-f6aa-44e4-a11a-50b54f73e8ad', 'da24b04f-9d2f-408b-af24-d4475bba5313', NULL, NULL, '二月: 系统测试', '系统测试', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('53a74130-7665-46f7-9dbb-016b7f44146a', 'da24b04f-9d2f-408b-af24-d4475bba5313', NULL, NULL, '三月: 1、采购到厂：自动同步SAP，采购订单，按照实际业务创建到厂计划
2、产品发货：自动同步SAP外向交', '1、采购到厂：自动同步SAP，采购订单，按照实际业务创建到厂计划
2、产品发货：自动同步SAP外向交货单，按照实际业务创建到厂计划
3、生产排程：自动同步SAP生产订单，每天按照实际业务备货，排程
4、生产任务执行：每天按照实际生产订订单下线量，贴码，扫码。
5、产品入库：每天按照实际业务确认产品入库数量
6、产品拣配：桶装扫码发货，其他按照数量发货
7、质量检验：原料自动触发送检、质量检验；产品发货自动送检，生成COA；生产下线自动送检，产品检验
8、交接班日志：初馏、精制、仓管每班填写交接班日志
9、装置计量：每班确认装置计量消耗和库存数据，每班提交
10、能源计量：每班填写能源计量数据', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('7abe8ec3-d6ca-4e60-b68c-68968dd7c867', 'da24b04f-9d2f-408b-af24-d4475bba5313', NULL, NULL, '四月: 继续对各功能模块进行实操并收集发现的问题及时处置。做好问题跟踪，继续优化进出厂流程', '继续对各功能模块进行实操并收集发现的问题及时处置。做好问题跟踪，继续优化进出厂流程', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('89d8c5ce-490d-4c8d-9148-cea913740cb3', 'da24b04f-9d2f-408b-af24-d4475bba5313', NULL, NULL, '重要里程碑: 2024-08-15 00:00:00', '2024-08-15 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('df177e2f-70e3-4245-a633-862b00af8e85', '9a60e0ba-c679-47d6-bc21-38589195c80d', NULL, NULL, '待办事项: 尽快验收；乙方人员是否还在现场？', '尽快验收；乙方人员是否还在现场？', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('79e7db45-805b-4177-ae1d-ef4dabc248f0', '9a60e0ba-c679-47d6-bc21-38589195c80d', NULL, NULL, '十二月: 其他模块继续开发中', '其他模块继续开发中', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d0be891c-e594-4438-bb37-682e41860eca', '9a60e0ba-c679-47d6-bc21-38589195c80d', NULL, NULL, '一月: 管线打开模块这周开始开发，
统计分析和变更管理随后开发，争取月底前完成', '管线打开模块这周开始开发，
统计分析和变更管理随后开发，争取月底前完成', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('40735cba-305d-4d04-9412-45d57b02a33f', '9a60e0ba-c679-47d6-bc21-38589195c80d', NULL, NULL, '重要里程碑: 2024-03-01 00:00:00', '2024-03-01 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('041ca5a1-61a5-4174-9276-e8773db4266b', '855a52cd-4fa0-4c7f-8135-d150c6c28b8e', NULL, NULL, '十二月: 1. 锦湖设备主数据维保业务等主数据收集并上传至系统；
2.   SAP、OA相关接口开发；
3. ', '1. 锦湖设备主数据维保业务等主数据收集并上传至系统；
2.   SAP、OA相关接口开发；
3. 网络开通、VPN账号收集、申请。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('7ded0621-38d5-4cbd-84da-60c0b6cd52a5', 'd018edb6-6374-46d7-9feb-19ebd875fb04', NULL, NULL, '十二月: 1、主数据已接收ERP推送
2、培训、练习
3、中蓝质量数据维护
4、上线过渡阶段策略沟通
5、CO', '1、主数据已接收ERP推送
2、培训、练习
3、中蓝质量数据维护
4、上线过渡阶段策略沟通
5、COA报告打印
1、上线检查清单
2、上线应急策略
3、设备模块上线
4、中蓝质量数据维护', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('87ae1b09-e37e-4406-8ed8-480dc5524cb1', 'd018edb6-6374-46d7-9feb-19ebd875fb04', NULL, NULL, '一月: 1、建立紧急联系机制（电话、微信/微信群），先处理问题后保留问题记录
2、问题收集，优化建议在线文档', '1、建立紧急联系机制（电话、微信/微信群），先处理问题后保留问题记录
2、问题收集，优化建议在线文档
3、中蓝质量1.6号下午再开展一次培训
4、用户手册提交用户
5、正式环境设备模块存在问题需要处理
6、1~7业务数据补录', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('3c759f2b-6302-4afb-985f-96267e7fe851', 'd018edb6-6374-46d7-9feb-19ebd875fb04', NULL, NULL, '二月: 1、系统上线问题处理
2、生产、设备、质量相关报表开发', '1、系统上线问题处理
2、生产、设备、质量相关报表开发', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('67a62d47-5edd-474e-94dc-3ed03c3e082a', 'd018edb6-6374-46d7-9feb-19ebd875fb04', NULL, NULL, '三月: 1.ERP月末结算价对接
2.设备工单成本报表继续开发
3.物料凭证同步，在和化数仓对接', '1.ERP月末结算价对接
2.设备工单成本报表继续开发
3.物料凭证同步，在和化数仓对接', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('1f528447-e100-4582-819b-0d7746d08e56', 'd018edb6-6374-46d7-9feb-19ebd875fb04', NULL, NULL, '四月: 1.物料凭证同步，在和化数仓对接完成
2.验收准备', '1.物料凭证同步，在和化数仓对接完成
2.验收准备', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a5382fd1-ad2c-498e-b50d-e81d739c9d78', 'd018edb6-6374-46d7-9feb-19ebd875fb04', NULL, NULL, '五月: 1.验收及转运维阶段', '1.验收及转运维阶段', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('529132e4-685c-427a-9236-b30342b41c75', 'd018edb6-6374-46d7-9feb-19ebd875fb04', NULL, NULL, '重要里程碑: 2025-10-15 00:00:00', '2025-10-15 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('795770c6-1c85-4791-af64-2c9e5f4629c6', 'fead739a-d955-480a-a304-3e5d2c1f60a0', NULL, NULL, '十二月: 1、提交立项审批流程，并约供应商进行价格谈判。', '1、提交立项审批流程，并约供应商进行价格谈判。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('857d4150-3f3c-47c6-be70-6f313affd7f3', 'fead739a-d955-480a-a304-3e5d2c1f60a0', NULL, NULL, '一月: 瑞祥：1、进行移动端的测试；2、进行第二轮系统培训
瑞泰：1、进行VPN申请；2、进行系统培训
总体', '瑞祥：1、进行移动端的测试；2、进行第二轮系统培训
瑞泰：1、进行VPN申请；2、进行系统培训
总体：采购谈判', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d4dd0b92-985c-46f4-9247-dc90f5804f94', 'fead739a-d955-480a-a304-3e5d2c1f60a0', NULL, NULL, '三月: 瑞恒：
1、准备剩余模块的上线工作；
2、调研委外检修流程在OA审批还是在EAM审批的相关需求；
3', '瑞恒：
1、准备剩余模块的上线工作；
2、调研委外检修流程在OA审批还是在EAM审批的相关需求；
3、明确完成时间。
瑞祥：
1、推进系统功能上线运行
2、专项设备、特种设备台账导入、检定计划制定
3、台账、ITPM计划等各基础资料新增及更新
4、进行固资台账绑定设备台账导入
5、密封腐蚀台账完善导入，腐蚀计划制定
瑞泰：
1、推进点检标准完善，推进系统功能上线；
3、电气相关功能沟通、制定电气相关业务审批流 ；
3、进行固资台账绑定设备台账导入；
4、缺陷管理、检修计划、风险管理模块与清云系统业务如何切割需要进行讨论；
5、组织集团确定报警区分方式；
6、讨论固定资产与SAP集成的需求；
圣奥：
1、进行商务合同相关流程；
2、技术协议进行最终确认。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('1969bcf1-9fcd-4f4b-8cb7-230d230d0874', 'fead739a-d955-480a-a304-3e5d2c1f60a0', NULL, NULL, '四月: 瑞恒：
1、确认项目验收交付文档；
2、沟通建立系统运维机制；
瑞祥：
1、推进系统功能上线运行；
', '瑞恒：
1、确认项目验收交付文档；
2、沟通建立系统运维机制；
瑞祥：
1、推进系统功能上线运行；
2、风险管理功能模块推进上线使用；
3、进行OPC数据接入；
瑞泰：
1、压力容器，压力管道检验计划全面启动上线运行；
2、进行每日执行数据情况统计（PPM+检修）
3、风险管理功能持续推进上线使用；
圣奥：
1、开展项目启动会。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('2216ddd6-b5e2-4503-a598-239bdaa4a455', 'fead739a-d955-480a-a304-3e5d2c1f60a0', NULL, NULL, '五月: 1、完善各模块流程制度，点检标准、润滑标准要求明确，车间主任签字确认，指定人员进行周期性检查，根据情', '1、完善各模块流程制度，点检标准、润滑标准要求明确，车间主任签字确认，指定人员进行周期性检查，根据情况进行考核；
2、进行项目验收会的前期沟通。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('7d392754-ed85-4a62-9451-3181f5a8f616', 'fead739a-d955-480a-a304-3e5d2c1f60a0', NULL, NULL, '重要里程碑: 2024-04-15 00:00:00', '2024-04-15 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('caeb1c7a-7bd6-445f-afd2-bb460003cba3', '8d4e2284-40b0-4ead-b0cb-1dc5354679da', NULL, NULL, '待办事项: 先将中间体三家工厂进行验收；', '先将中间体三家工厂进行验收；', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d7577238-432a-4618-b9d5-b88479f84fde', '8d4e2284-40b0-4ead-b0cb-1dc5354679da', NULL, NULL, '五月: 瑞祥：
1、DCS数据接入的服务器资源协调；
2、进行项目验收会的前期沟通；
3、进行基建、电气等设', '瑞祥：
1、DCS数据接入的服务器资源协调；
2、进行项目验收会的前期沟通；
3、进行基建、电气等设备台账完善
瑞泰：
1、进行项目验收会的前期沟通；
2、进行检修流程优化调整；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('80c3756d-69a3-45f0-9bf6-cc26ab401ec6', '8d4e2284-40b0-4ead-b0cb-1dc5354679da', NULL, NULL, '重要里程碑: 瑞祥：2024/6/15
瑞泰：2024/7/15', '瑞祥：2024/6/15
瑞泰：2024/7/15', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ff5e3912-b3f0-450d-a712-7c5f3ba15f30', '8437f2eb-a7a8-4180-9d58-18026c615073', NULL, NULL, '待办事项: 后续统一与中化信息购买看护服务，抓紧立项', '后续统一与中化信息购买看护服务，抓紧立项', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9ca6fc0a-f83c-43b9-9ea7-75a81153bce9', '8437f2eb-a7a8-4180-9d58-18026c615073', NULL, NULL, '五月: 1、进行数据迁移工具开发，预计进展90%；
2、完成升级方案全量测试；
3、完成诊断中心数据迁移测试', '1、进行数据迁移工具开发，预计进展90%；
2、完成升级方案全量测试；
3、完成诊断中心数据迁移测试；
4、进行报警业务数据迁移工具开发，预计进展90%。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a03d2a77-2313-41b5-9162-b147e2512719', '8437f2eb-a7a8-4180-9d58-18026c615073', NULL, NULL, '六月: 1、进行系统切换升级方案制定并发布；
2、进行圣奥化学服务器结构部署调整与新老服务器数据传输；
3、', '1、进行系统切换升级方案制定并发布；
2、进行圣奥化学服务器结构部署调整与新老服务器数据传输；
3、进行系统正式切换的准备与线上系统培训工作。', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('253291f7-c181-4ef7-b342-8c4bfbf828be', '8437f2eb-a7a8-4180-9d58-18026c615073', NULL, NULL, '七月: 1、进行系统功能监护运行；
2、提交上线安全检查材料；', '1、进行系统功能监护运行；
2、提交上线安全检查材料；', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('fd0ef0af-b0eb-4141-98e4-38d265c5de37', '971eee5d-6f7c-4c25-b533-2e8e88ffff89', NULL, NULL, '一月: 承包商-已完成统建系统的建设，待集团发布标准完成自建系统的数据对接
BD-已完成所有企业年度任务，核', '承包商-已完成统建系统的建设，待集团发布标准完成自建系统的数据对接
BD-已完成所有企业年度任务，核实、上报项目进度
固废-配合集团调研，完成基础信息收集表', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('3ff3ca8b-eb62-4b17-9b24-f2dded4331b9', '971eee5d-6f7c-4c25-b533-2e8e88ffff89', NULL, NULL, '二月: 承包商-已完成统建系统的建设，沟通自建系统数据上报事宜
BD-按照集团要求，和各企业沟通确认2025', '承包商-已完成统建系统的建设，沟通自建系统数据上报事宜
BD-按照集团要求，和各企业沟通确认2025年建设内容
固废-配合中化信息进行系统试运行', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('33427613-b5a1-43a7-b6d1-299c5142c24a', '971eee5d-6f7c-4c25-b533-2e8e88ffff89', NULL, NULL, '三月: 承包商-按照集团计划，推进自建系统数据接入
BD-按照集团要求，推进系统完善
固废-配合中化信息进行', '承包商-按照集团计划，推进自建系统数据接入
BD-按照集团要求，推进系统完善
固废-配合中化信息进行系统试运行', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a7e31c6e-deb4-431b-8ae8-e6213736e613', '971eee5d-6f7c-4c25-b533-2e8e88ffff89', NULL, NULL, '四月: 承包商-按照集团计划，推进自建系统数据接入
BD-按照集团要求，推进系统完善
固废-配合中化信息进行', '承包商-按照集团计划，推进自建系统数据接入
BD-按照集团要求，推进系统完善
固废-配合中化信息进行系统试运行', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('c478c37c-2a6f-49ee-bd3a-b741d40aee93', '971eee5d-6f7c-4c25-b533-2e8e88ffff89', NULL, NULL, '五月: 承包商-按照集团计划，推进自建系统数据接入
BD-按照集团要求，推进系统完善
固废-配合中化信息进行', '承包商-按照集团计划，推进自建系统数据接入
BD-按照集团要求，推进系统完善
固废-配合中化信息进行系统试运行', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('96fc5315-0aaf-4c91-9cd8-d99297efd72f', '971eee5d-6f7c-4c25-b533-2e8e88ffff89', NULL, NULL, '六月: 承包商-按照集团计划，推进自建系统数据接入
BD-按照集团要求，推进系统完善
固废-配合中化信息进行', '承包商-按照集团计划，推进自建系统数据接入
BD-按照集团要求，推进系统完善
固废-配合中化信息进行系统试运行', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('48647d6a-9968-4210-bd3c-24d8b0b110d6', '971eee5d-6f7c-4c25-b533-2e8e88ffff89', NULL, NULL, '七月: 承包商-按照集团计划，推进自建系统数据接入
BD-按照集团要求，推进系统完善
固废-关注固废系统正式', '承包商-按照集团计划，推进自建系统数据接入
BD-按照集团要求，推进系统完善
固废-关注固废系统正式版运行情况，收集相关问题', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('98d30117-8e45-4725-b152-e44df69256b5', '971eee5d-6f7c-4c25-b533-2e8e88ffff89', NULL, NULL, '八月: 承包商-按照集团计划，推进自建系统数据接入
BD-已完成年度计划，不再跟踪
固废-关注固废系统正式版', '承包商-按照集团计划，推进自建系统数据接入
BD-已完成年度计划，不再跟踪
固废-关注固废系统正式版运行情况，收集相关问题', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('60e2a579-5276-45f1-bf59-1caa0d4bd78f', '971eee5d-6f7c-4c25-b533-2e8e88ffff89', NULL, NULL, '九月: 暂不跟踪', '暂不跟踪', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('0993c0e9-b6e1-4339-9a88-3df21cf60c08', '971eee5d-6f7c-4c25-b533-2e8e88ffff89', NULL, NULL, '十月: 暂不跟踪', '暂不跟踪', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('bd6729f6-cf76-4bc3-bc32-3641a948d1c7', '971eee5d-6f7c-4c25-b533-2e8e88ffff89', NULL, NULL, '十一月: 暂不跟踪', '暂不跟踪', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('dbd23dd8-2c8f-4f4e-a55b-4d3b3c2e7950', '971eee5d-6f7c-4c25-b533-2e8e88ffff89', NULL, NULL, '重要里程碑: 2024-05-01 00:00:00', '2024-05-01 00:00:00', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9782e656-b652-48ac-b81c-f230b65f8129', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '待办事项: 计划', '计划', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('7fad62c8-7542-4f1d-9410-c11b9efaa1bf', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '十一月: 确定最新工单流程细节', '确定最新工单流程细节', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('75577248-2942-4b5c-9edb-612467de1789', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '十二月: 老旧电脑升级', '老旧电脑升级', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ab90ee6d-1f18-4f5c-ba93-76fb47fc36f8', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '待办事项: 计划', '计划', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('2754ef60-141f-4bb6-aec2-43d5cf7bf9b9', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '十一月: 尽快确认最终采购方式并确认采购周期是否满足HSE要求整改期限，及时将情况上报至中化，防止后续持续通报', '尽快确认最终采购方式并确认采购周期是否满足HSE要求整改期限，及时将情况上报至中化，防止后续持续通报该情况', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('935e3a2c-5141-40e3-b84d-622c90df82af', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '十二月: 1.提交采购计划并持续跟踪进度
2.移动布控球调试接入HSE平台关联高危作业票', '1.提交采购计划并持续跟踪进度
2.移动布控球调试接入HSE平台关联高危作业票', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d2138a56-fa02-497a-b561-7a73dc9be23f', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '待办事项: 计划', '计划', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('be4ae557-1456-42bd-9f9d-b7d6fd3bd7d6', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '十月: 试运行', '试运行', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d96cbf6c-d869-4a8b-a34e-98e417156e93', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '十一月: 拟定验收报告所需材料，并跟踪后续验收情况，继续保障机器人日常运行', '拟定验收报告所需材料，并跟踪后续验收情况，继续保障机器人日常运行', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('085b9e01-00c6-4c1e-beb2-1e6078ede133', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '十二月: 继续跟踪巡检机器人项目情况，保障机器人日常运维，制定项目问题清单', '继续跟踪巡检机器人项目情况，保障机器人日常运维，制定项目问题清单', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('7e03a5a2-02fb-4265-8787-b29e259ab18b', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '待办事项: 计划', '计划', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('39e48e3b-fbf0-42c0-9628-12aaddbefa31', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '十一月: 1.继续完成标准化桌面扫盲工作
2.将这次扫出盗版软件用户电脑全部标准化', '1.继续完成标准化桌面扫盲工作
2.将这次扫出盗版软件用户电脑全部标准化', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d066a2e9-21bc-4a39-a47e-c46873036934', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '十二月: 准备IT资产管理规范编制（参考现有规范，成熟方案）
包括：分类，编码规则，配备标准，管理流程', '准备IT资产管理规范编制（参考现有规范，成熟方案）
包括：分类，编码规则，配备标准，管理流程', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('31713af4-74d7-4636-8ca7-3b0a074f46b2', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '待办事项: 计划', '计划', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('032e95e4-0668-406e-afe4-fd39134897da', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '十一月: 继续跟进人力系统需优化方面需求', '继续跟进人力系统需优化方面需求', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('8614eaad-1e86-4efa-9f73-c27142740021', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '十二月: 后续将由霍尼工程师对用户各需求做进一步调研，等全部业务梳理完成后再进行下一步工作安排', '后续将由霍尼工程师对用户各需求做进一步调研，等全部业务梳理完成后再进行下一步工作安排', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9814c33a-e983-4f20-bed0-8bdfc3cbe382', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '待办事项: 02-生产运营', '02-生产运营', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('f7930ffe-14db-478e-86a8-66cb6b317110', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '顾涛: 张巾', '张巾', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('e738456e-efe3-414b-9bae-300f3bd7f35c', 'fc05067c-a99d-4a30-97d5-38f047e3b9ef', NULL, NULL, '1月: 2月', '2月', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d853379d-70c0-419d-992b-f42cde9dc56b', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '待办事项: 03-管理应用', '03-管理应用', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('87c075fc-fadd-4c13-a1b0-13d40942e630', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '顾涛: 彭静', '彭静', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('2f47e70f-bb46-4bae-ac88-c8263e1ae931', '553cb673-ae98-4eec-b017-6a0c28808542', NULL, NULL, '1月: 3月', '3月', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a0da5d87-dfc3-481c-9c90-5c6d10462d56', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '待办事项: 04-基设网安', '04-基设网安', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('a9d31333-152f-44da-b4ad-985f3814fdd3', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '顾涛: 翟晓菲', '翟晓菲', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ce759dd2-03cd-49e1-a1eb-6ce800dab617', '3130a219-16f7-438c-9adc-fea886e05735', NULL, NULL, '1月: 4月', '4月', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('1a1202f6-ec04-4592-b075-3ceeb840033e', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '待办事项: 05-N/A', '05-N/A', 'todo', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('b62ff613-99d1-45d2-b63d-c362e92737cf', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '顾涛: 李晶玮', '李晶玮', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9ea1494d-8145-4b37-80e3-657c3e074c57', 'c97d959e-148a-4966-91cf-295ba6c89af0', NULL, NULL, '1月: 5月', '5月', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('19b398f9-f3b4-4b51-bf68-7874ce308366', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '顾涛: 宣安来', '宣安来', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9b7204f8-3103-4846-978b-81e1ab8bc8ce', '02c9021f-3555-46ca-84e7-d136aa03b012', NULL, NULL, '1月: 6月', '6月', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('0a6dabfb-5c3a-4e78-91fc-4a01e482d33c', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '顾涛: 吴在华', '吴在华', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('2695d9dc-2850-44c7-a348-2d4d47ea4d66', '3ac65e32-3295-4a24-86fd-645fb83b10f7', NULL, NULL, '1月: 7月', '7月', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('13f41e49-2a21-4d05-84a1-bcc4f3e5d845', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '顾涛: 李亨翡', '李亨翡', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d9fbc555-aa3f-4c91-b39c-0ba9bb3a1aab', 'd1009270-2263-404c-a39b-0a98cd0b8845', NULL, NULL, '1月: 8月', '8月', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('c9c929f5-1192-487d-b619-1cdbfabd3af8', '5c168ab0-df2a-4e7f-8ab7-4d06e2d289cd', NULL, NULL, '顾涛: 张晓峰', '张晓峰', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('31e40dd5-120e-4383-a7f4-a3dd9dbc3e1f', '5c168ab0-df2a-4e7f-8ab7-4d06e2d289cd', NULL, NULL, '1月: 9月', '9月', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('495b1604-168e-4b3b-a2c3-5387f04bb4ae', '4755cd9b-3a46-4fd9-a91e-39d1dfcef173', NULL, NULL, '顾涛: 蒋兰萍', '蒋兰萍', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('65b30dfd-e72b-4056-912f-54f493321e97', '4755cd9b-3a46-4fd9-a91e-39d1dfcef173', NULL, NULL, '1月: 10月', '10月', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('3997c622-b4df-45f6-bcf4-c4a91d01ee8a', '6fdaa9be-7af9-4820-afa5-b1327964606e', NULL, NULL, '顾涛: 陶云飞', '陶云飞', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('e3e6f3eb-c624-4eff-90fe-9adf665f94ce', '6fdaa9be-7af9-4820-afa5-b1327964606e', NULL, NULL, '1月: 11月', '11月', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('409d9148-1147-4738-a5ce-830e82b46d3a', '2abd6d04-c2e8-4284-9477-fc7f1bb7f67c', NULL, NULL, '顾涛: 黄亮', '黄亮', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('3a5175ce-37cc-4952-af25-7209a3aca731', '2abd6d04-c2e8-4284-9477-fc7f1bb7f67c', NULL, NULL, '1月: 12月', '12月', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('0a0a0d69-aa83-4487-8395-a0cd94e47503', '50f7c3cd-57ba-406b-92a1-2738c4f9ec0f', NULL, NULL, '顾涛: 王蕾', '王蕾', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('d0324985-17d9-4dd3-b818-a426014fdefa', '80db9432-84d2-441b-b497-c867a8308b65', NULL, NULL, '顾涛: 刘鑫', '刘鑫', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('2a6024d1-05ec-426e-a302-0d29a60d919a', '0f20a971-b51b-4773-ab71-e08691ee7d68', NULL, NULL, '顾涛: 董俊', '董俊', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('8336ee09-1b05-4a1a-bab3-a29f12a9acf3', 'da24b04f-9d2f-408b-af24-d4475bba5313', NULL, NULL, '顾涛: 赵俊', '赵俊', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('1b9eb8b6-84ea-41b0-aa04-cccbc006f453', '9a60e0ba-c679-47d6-bc21-38589195c80d', NULL, NULL, '顾涛: 张羽翔', '张羽翔', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('fb2f28d2-9612-4841-a3a8-8c52da185ea3', '855a52cd-4fa0-4c7f-8135-d150c6c28b8e', NULL, NULL, '顾涛: 吴晶晶', '吴晶晶', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('068890a4-1003-42ed-b84e-404a2bc2f87c', 'd018edb6-6374-46d7-9feb-19ebd875fb04', NULL, NULL, '顾涛: 赵佳', '赵佳', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('5216f715-b222-4ba3-84d5-60bdee3e915a', 'fead739a-d955-480a-a304-3e5d2c1f60a0', NULL, NULL, '顾涛: 孙聪', '孙聪', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('bb729ad1-58b1-4886-b9a1-db062bf722d7', '8d4e2284-40b0-4ead-b0cb-1dc5354679da', NULL, NULL, '顾涛: 张敏', '张敏', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('4ecc18c2-3a47-4b84-8014-95641f26e997', '8437f2eb-a7a8-4180-9d58-18026c615073', NULL, NULL, '顾涛: 丁凯', '丁凯', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('8a4bef1e-6a8b-43bd-8445-08dee1f39549', '971eee5d-6f7c-4c25-b533-2e8e88ffff89', NULL, NULL, '顾涛: 顾明军', '顾明军', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('6e48069c-17ed-4e1b-9e0c-901fe07630e2', '931ff23f-ac64-436c-825f-9015293f7e33', NULL, NULL, '顾涛: 陈璞', '陈璞', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('ff9bf58c-8f3f-410d-873c-e6d918876698', 'd3a57d0c-9692-493b-a0df-aa634da5c727', NULL, NULL, '顾涛: 马天明', '马天明', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('9de7380c-4bd7-45f1-a7a1-73c7becb5be3', 'f1277119-8f97-4810-9d43-441236cafe05', NULL, NULL, '顾涛: 丁骞', '丁骞', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('4053a0fb-4299-4338-81c4-5a54cc1e839d', '5c4cf2b3-dc97-4c1c-8d52-83274ac0eec5', NULL, NULL, '顾涛: 梁诚', '梁诚', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('dfb4f917-799a-4e81-8f09-91e2325b21f1', 'a13acb78-58fd-451b-9cf7-cb5e266c13d7', NULL, NULL, '顾涛: 黄云', '黄云', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('e54ad7d5-a00a-4773-919e-45999f4cf953', 'a926e889-469c-4b37-9841-178f7ab83f6f', NULL, NULL, '顾涛: 丁翔', '丁翔', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();


INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('f84ca86f-8b7c-402d-9e47-5533bde58281', '95372a85-07fc-4547-8b3e-7150dc978975', NULL, NULL, '顾涛: 姚晓龙', '姚晓龙', 'in_progress', NULL, NULL, NULL, NULL, NULL, NULL, 0.0, '[]'::jsonb, '{}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();
