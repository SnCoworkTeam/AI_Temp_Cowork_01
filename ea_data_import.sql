-- 企业架构数据导入SQL
-- 生成时间: 2025-12-07 13:38:34.312492


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('3a487f63-afd0-4df1-9562-60fd9c91cd4d', '采购流程', '企业采购业务流程，包括需求申请、供应商选择、合同签订等环节', '采购部', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('be601e9b-90cc-4e62-b436-1ad25a919c2d', '销售流程', '企业销售业务流程，包括客户管理、订单处理、发货等环节', '销售部', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('ef74140e-f99c-45ec-bda2-6fe51c4d4a93', '2.1采购部组织架构图', '高日常库存管理的工作效率。\n组织机构\n中化添加剂事业部组织架构图，如下：\n2.1采购部组织架构图\n2.2 仓储部门组织架构图\n部门职责\n采购部部门职责\n部门职责：\n负责包括原料采购、装备及MRO采购、采购管理等工作。统筹策划和确定采购战略，建设和维护供应商管理体系，控制采购总成本，协助决策层制定公司发展战略。\n1、建立采购体系，完善各项采购制度和采购流程；\n2、关注市场变化，做好与采购业务相关的市场调研及趋势预测工作，提供各类调研数据与报告，结合财务、生产、销售、战略等部门为公司经营决策提供参考依据。\n3、与各需求部门沟通协调确定最终的采购需求，制定采购计划，签订合同或下达采购订单，配合各部门做好验', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('b5b88459-c171-4492-b594-fdbdb9f381d0', '负责包括原料采购、装备及MRO采购、采购管理等工作', '责\n部门职责：\n负责包括原料采购、装备及MRO采购、采购管理等工作。统筹策划和确定采购战略，建设和维护供应商管理体系，控制采购总成本，协助决策层制定公司发展战略。\n1、建立采购体系，完善各项采购制度和采购流程；\n2、关注市场变化，做好与采购业务相关的市场调研及趋势预测工作，提供各类调研数据与报告，结合财务、生产、销售、战略等部门为公司经营决策提供参考依据。\n3、与各需求部门沟通协调确定最终的采购需求，制定采购计划，签订合同或下达采购订单，配合各部门做好验收入库、发票催收和付款工作。\n4、管控采购成本，寻找最佳批量，与技术、生产及质量管理部一起设定最佳质量标准，追求采购总成本最低。处理质量投诉，保障物', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('42080eaf-6fed-43cc-970a-268a2f3d6319', '备及MRO采购、采购管理等工作', '备及MRO采购、采购管理等工作。统筹策划和确定采购战略，建设和维护供应商管理体系，控制采购总成本，协助决策层制定公司发展战略。\n1、建立采购体系，完善各项采购制度和采购流程；\n2、关注市场变化，做好与采购业务相关的市场调研及趋势预测工作，提供各类调研数据与报告，结合财务、生产、销售、战略等部门为公司经营决策提供参考依据。\n3、与各需求部门沟通协调确定最终的采购需求，制定采购计划，签订合同或下达采购订单，配合各部门做好验收入库、发票催收和付款工作。\n4、管控采购成本，寻找最佳批量，与技术、生产及质量管理部一起设定最佳质量标准，追求采购总成本最低。处理质量投诉，保障物料质量持续达标。\n5、平衡国内外采购', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('926817fe-7fbf-457c-b1e4-f3db0fcb3b90', '追求采购总成本最低', '与技术、生产及质量管理部一起设定最佳质量标准，追求采购总成本最低。处理质量投诉，保障物料质量持续达标。\n5、平衡国内外采购量，利用进料加工等税收优惠政策，寻找最合理价格。将公司效益做到最大化。\n6、在采购管理规定和招标制度规范下协调、配合各业务部门，完成项目及服务类采购工作，并做好定期抽查工作，向被检查单位及管理层提供整改建议报告。\n7、建立供应商档案，维护供应商关系，与具有市场竞争力、合作稳定性及持续性良好的供应商建立长期战略合作关系。\n仓储部部门职责\n圣奥化学泰国有限公司：\n负责原辅材料、设备及备品备件、产成品入库、在库及出库管理\n1.\t收根据物资检验结果办理入库手续，并进行分类保管。\n2.\t负', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('7f680915-8132-4289-9f97-5907fe52b123', '4.3采购价格主数据', '管理,部分供应商在MDM管理。\n供应商分类：国内供应商、国外供应商、员工供应商\n4.3采购价格主数据\n采购价格主数据在SRM系统价格库进行管理，目前没有同步到SAP系统；国内采购价格使用含税单价，进口采购业务价格使用外币不进行本币转换；\n付款条件清单如下：\n业务流程\n5.1物料主数据管理现状\n目前添加剂主数据申请流程为原料、产成品在集团MDM申请并同步到化工事业部主数据管理系统，化工事业部主数据系统与ERP接口创建物料主数据基本视图、工厂视图、采购视图、生产视图、销售视图、会计视图等在ERP中进行批量扩充。集团MDM申请的编码与SAP集成并分发基础视图。\n圣奥化学物料主数据根据审批流的不同分七类：\n', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('0a482d67-a335-4185-95d9-98077f2126f7', '自动将原采购订单发布给供应商', '自动将原采购订单发布给供应商；供应商确认完成后，订单信息会传给SAP；\n固定资产需求计划：需求部门在OA中提报采购申请，审批通过后，归口管理部门需创建固定资产编码，IT类固资直接走目录化商城或电商商城采购流程；\n固定资产采购执行：非IT类采购员发起采购评审流程，并形成寻源结果及价格库数据，根据采购评审结果或寻源结果创建采购订单，对于需要走合同的订单，由采购员根据订单发起合同流程，无需签订合同的订单在订单审批完成后自动发布至供应商，需签订合同的订单在合同签订完成后发布至供应商，供应商对采购部发出的采购订单进行确认，确认完成后订单数据同步至SAP\n备品备件需求计划\nIEAM/OA提报需求计划，OA进行审', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('f26b0fdb-ba1a-41b6-8600-f98b027645b7', '引用采购订单签署合同', '同的订单在审批后不自动发布至供应商；合同签署时，引用采购订单签署合同；合同签署确认后，会自动将原采购订单发布给供应商；供应商确认完成后，订单信息会传给SAP；\n费用化需求计划：电商平台下单的走电商商城采购流程，不走电商商城下单需要需求部门在OA提出需求计划申请并对提报的需求并在OA进行审批，审批通过后，系统根据申请类型和物料品类进行自动分配采购员\n费用类采购执行：费用类采购订单支持无物料编码下单；采购员创建采购订单提交后，采购订单在SRM进行审批，审批通过的将直接发布给供应商进行确认；审批拒绝的订单返回订单维护界面重新编辑；供应商确认时主要对数量、交期进行确认，并且可对订单行项目信息编辑反馈信息，一', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('b3e491c6-2f7f-4c47-951b-10b0cda01f28', '5.5特殊采购流程', '用部门、质检、HSE共同评审，判断“让步接收”或“退货”，原材料质检不合格不收货（原材料如果某项非关键指标不合格可如让步接收，按订单数量扣减接收），D类和MRO类物料不合格直接换货供应商\n5.5 特殊采购流程\n5.5.1寄售业务\n1、前置仓寄售业务：工厂计划员统计下个月采购物料编码、数量，需求发京东京东按照需求清单发到工厂寄售仓库，货到后先验收，验收合格后在京东WMS收货到前置仓，使用部门按需领料，领料后保管员先在京东WMS出库，25号汇总消耗量形成对账单，根据对账单核对，部门在京东下订单，同时在ERP系统创建采购订单并收货，使用部门在IEAM提交领料申请，仓库确认物料编码、数量并审批，系统收到审批', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('cc35e51a-29ab-4632-974a-660b9a40dce9', '采购员根据采购申请创建对发货工厂的采购订单同步到SAP', '工过账。\n4 工厂->工厂\n工厂提报需求OA审批后到SRM，采购员根据采购申请创建对发货工厂的采购订单同步到SAP，发货工厂交货单发货过账，收货工厂在SAP根据采购订单进行收货。\n7.流程清单\n7.1采购管理业务流程\n注：紧急采购流程与上述流程均一致，但需要10天内补齐单据\n（1）未来业务流程需要补充水电气采购流程、付款流程\n（2）未来业务流程服务采购和费用化采购需要做出区分\n（3）未来需要单独体现项目采购流程进行\n（4）未来业务流程需要补充招标流程\n（5）未来业务流程增加采购结算流程\n7.2库存管理业务流程\n（1）未来需要考虑危废处理流程\n8.需求及优化点：\n（一）物料主数据：SAP S4系统物料', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('3ad0395f-efaa-4225-a052-0fb6c8c842e4', '收货工厂在SAP根据采购订单进行收货', 'SAP，发货工厂交货单发货过账，收货工厂在SAP根据采购订单进行收货。\n7.流程清单\n7.1采购管理业务流程\n注：紧急采购流程与上述流程均一致，但需要10天内补齐单据\n（1）未来业务流程需要补充水电气采购流程、付款流程\n（2）未来业务流程服务采购和费用化采购需要做出区分\n（3）未来需要单独体现项目采购流程进行\n（4）未来业务流程需要补充招标流程\n（5）未来业务流程增加采购结算流程\n7.2库存管理业务流程\n（1）未来需要考虑危废处理流程\n8.需求及优化点：\n（一）物料主数据：SAP S4系统物料主数据需增加物料评估类型（原材料、库存商品、备件等）和物料组（机备件、标准件、电器、仪表等）\n（二）采购：\n', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('c54fa49b-a6d2-4480-863e-9a1f7934c8a4', '注：紧急采购流程与上述流程均一致', '理业务流程\n注：紧急采购流程与上述流程均一致，但需要10天内补齐单据\n（1）未来业务流程需要补充水电气采购流程、付款流程\n（2）未来业务流程服务采购和费用化采购需要做出区分\n（3）未来需要单独体现项目采购流程进行\n（4）未来业务流程需要补充招标流程\n（5）未来业务流程增加采购结算流程\n7.2库存管理业务流程\n（1）未来需要考虑危废处理流程\n8.需求及优化点：\n（一）物料主数据：SAP S4系统物料主数据需增加物料评估类型（原材料、库存商品、备件等）和物料组（机备件、标准件、电器、仪表等）\n（二）采购：\n报表需求\n（1）降本率报表（和预算相比、历史价、市场价）\n（2）执行率报表\n（3）各家库存实时报表', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('d0aa197b-f09f-41fe-8217-cd98dacbf54d', '（二）采购：', '库存商品、备件等）和物料组（机备件、标准件、电器、仪表等）\n（二）采购：\n报表需求\n（1）降本率报表（和预算相比、历史价、市场价）\n（2）执行率报表\n（3）各家库存实时报表（需要取SRM价格）\n（4）采购流程执行效率表，每个流程需要提醒功能\n（5）采购价格分析报表（横纵向比较，横向比较其他工厂，纵向比较前期采购价格）\n优化需求\n（1）三单匹配目前由人工操作，是否能够系统自动匹配，系统比较有问题的系统自动提醒\n（2）STO业务流程优化，统一工厂间调拨业务，现系统根据物料类型，部分物料采购订单创建在1753，发货工厂创建发货通知单，建议通过系统上线，统一工厂间调拨业务流程，其中国内与泰国工厂调拨还需要创', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('9f55fdbc-f4f3-43f1-ba40-68428e89e783', 'MM模块主要包括:物料需求计划、物料主数据、采购、库存管理、仓库管理、后勤信息系统等几个组成部分', '用中最为广泛应用的模块，与财务、生产、销售、成本等模块均有密切的关系。特别是对物料主数据中各种参数的设置将直接影响到成本、生产、销售中的流程和结果。MM 模块主要包括:物料需求计划、物料主数据、采购、库存管理、仓库管理、后勤信息系统等几个组成部分。\n物料主数据是整个物料管理模块的基石,物料主数据资料设置的正确与否将直接影响到相关模块运作的精确程度。\nERP 的采购包括有框架协议、询价报价、信息记录、采购申请、采购订单等部分组成。我们可以通过事先设置的采购协议依据需求自动建立采购申请，并将这些采购申请转为采购订单。同时也可以通过信息记录来限制采购员擅自更改采购价格。建立一个具备有效监控的采购体系。添加', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('60df7623-fe91-4ff2-b66e-3f9b147c5d3d', '库存管理单元实际上包括物料收发的整个过程', '购申请转为采购订单。同时也可以通过信息记录来限制采购员擅自更改采购价格。建立一个具备有效监控的采购体系。添加剂事业部目前询报价、价格库、供应商管理、合同管理以及付款审核等功能在SRM系统中进行管理。\n库存管理单元实际上包括物料收发的整个过程，这个过程不仅仅是采购收货、采购退货还包括生产的收发、库存调整甚至是跨公司、工厂的转移。在做库存管理时系统也将记录系统的操作时间和记帐时间，并允许记录实际操作的单据号码，为后续的查询提供和检索方便。添加剂事业部通过MES、WMS系统与ERP系统集成实现库存物资出入库管理，极大提高日常库存管理的工作效率。\n组织机构\n中化添加剂事业部组织架构图，如下：\n2.1采购部组', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('5e14329b-9a28-47fc-9f9b-c874c6107fd0', '在做库存管理时系统也将记录系统的操作时间和记帐时间', '移。在做库存管理时系统也将记录系统的操作时间和记帐时间，并允许记录实际操作的单据号码，为后续的查询提供和检索方便。添加剂事业部通过MES、WMS系统与ERP系统集成实现库存物资出入库管理，极大提高日常库存管理的工作效率。\n组织机构\n中化添加剂事业部组织架构图，如下：\n2.1采购部组织架构图\n2.2 仓储部门组织架构图\n部门职责\n采购部部门职责\n部门职责：\n负责包括原料采购、装备及MRO采购、采购管理等工作。统筹策划和确定采购战略，建设和维护供应商管理体系，控制采购总成本，协助决策层制定公司发展战略。\n1、建立采购体系，完善各项采购制度和采购流程；\n2、关注市场变化，做好与采购业务相关的市场调研及趋势', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('c60314de-0571-4544-8af6-46c6acef6607', '5.4库存管理现状', '下比价， OA申请在SRM创建采购订单，采购订单在SRM进行审批，审批通过后打印订单，如果订单金额大于十万，需要打印合同（对数量、交期进行确认），与供应商进行签字确认，SRM 订单同步SAP\n5.4 库存管理现状\n5.4.1安徽圣奥化学科技有限公司\n入库业务\n原料：MES记录过磅信息、质检信息、到库信息并实物入库，到货后，通过MES记录过磅信息，质检信息、到库信息办理入库（保税的MIBK物料按报关信息入库），手动SAP操作收货入库\n备品备件：到货后线下手动将质检合格信息录入到MES，合格品手动SAP操作收货入库\n包材：到货后线下手动将质检合格信息录入到MES，合格品手动SAP操作收货入\n能源：SAP', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('3bf80546-7d80-4b56-8148-1cf2ade7a0c3', '7.2库存管理业务流程', '补充水电气采购流程、付款流程\n（2）未来业务流程服务采购和费用化采购需要做出区分\n（3）未来需要单独体现项目采购流程进行\n（4）未来业务流程需要补充招标流程\n（5）未来业务流程增加采购结算流程\n7.2库存管理业务流程\n（1）未来需要考虑危废处理流程\n8.需求及优化点：\n（一）物料主数据：SAP S4系统物料主数据需增加物料评估类型（原材料、库存商品、备件等）和物料组（机备件、标准件、电器、仪表等）\n（二）采购：\n报表需求\n（1）降本率报表（和预算相比、历史价、市场价）\n（2）执行率报表\n（3）各家库存实时报表（需要取SRM价格）\n（4）采购流程执行效率表，每个流程需要提醒功能\n（5）采购价格分析报表', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('ae012d27-39b2-49ed-adac-7a8c0067a51b', '参与对生产过程中质量进行管控', '、销售中心对接客户资源的管理，对客户资源信息进行保密。\n2.负责对公司重要客户定期进行交流沟通，了解客户需求，关注客户满意度，组织客户信息评审并反馈。\n3.负责在授权的情况下行使客户代表的职责，参与对生产过程中质量进行管控，确保产品质量符合客户要求。\n4.负责结合圣奥化学运营中心对公司客户满意度定期做自我评价，对评价的过程及结果进行记录并做到持续改进。\n5.负责依据圣奥化学运营中心下发的销售任务结合公司实际产销存情况排程发货计划，制定公司内部发货管理控程序，对发货流程及包装要求等实施有效控制。\n6.负责与生产系统、检测中心做好出货成品的编号的追溯工作。\n7.负责根据IATF标准要求对最终库存成品的特', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('6c94bebe-73c9-4afa-aa41-70aa10cb26b2', '5.负责依据圣奥化学运营中心下发的销售任务结合公司实际产销存情况排程发货计划', '求。\n4.负责结合圣奥化学运营中心对公司客户满意度定期做自我评价，对评价的过程及结果进行记录并做到持续改进。\n5.负责依据圣奥化学运营中心下发的销售任务结合公司实际产销存情况排程发货计划，制定公司内部发货管理控程序，对发货流程及包装要求等实施有效控制。\n6.负责与生产系统、检测中心做好出货成品的编号的追溯工作。\n7.负责根据IATF标准要求对最终库存成品的特性制定控制计划。\n山东圣奥化学科技有限公司：\n1、负责仓储原材物料、产品、顾客产品的标识、贮存、摆放及维护、保管；\n2、负责搬运、贮存、防护和交过程的组织实施；\n3、负责仓库环境的管理，严格执行有关防火和危险物品管理规定，搞好仓库防火、防盗、危险', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('3e68a082-5c0f-41df-9530-2b46783c36ce', '（1）未来业务流程需要补充水电气采购流程、付款流程', '货工厂交货单发货过账，收货工厂在SAP根据采购订单进行收货。\n7.流程清单\n7.1采购管理业务流程\n注：紧急采购流程与上述流程均一致，但需要10天内补齐单据\n（1）未来业务流程需要补充水电气采购流程、付款流程\n（2）未来业务流程服务采购和费用化采购需要做出区分\n（3）未来需要单独体现项目采购流程进行\n（4）未来业务流程需要补充招标流程\n（5）未来业务流程增加采购结算流程\n7.2库存管理业务流程\n（1）未来需要考虑危废处理流程\n8.需求及优化点：\n（一）物料主数据：SAP S4系统物料主数据需增加物料评估类型（原材料、库存商品、备件等）和物料组（机备件、标准件、电器、仪表等）\n（二）采购：\n报表需求\n', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('0c5487e5-8c7a-4782-994a-e047a8340052', '2.1采购部组织架构图', '高日常库存管理的工作效率。\n组织机构\n中化添加剂事业部组织架构图，如下：\n2.1采购部组织架构图\n2.2 仓储部门组织架构图\n部门职责\n采购部部门职责\n部门职责：\n负责包括原料采购、装备及MRO采购、采购管理等工作。统筹策划和确定采购战略，建设和维护供应商管理体系，控制采购总成本，协助决策层制定公司发展战略。\n1、建立采购体系，完善各项采购制度和采购流程；\n2、关注市场变化，做好与采购业务相关的市场调研及趋势预测工作，提供各类调研数据与报告，结合财务、生产、销售、战略等部门为公司经营决策提供参考依据。\n3、与各需求部门沟通协调确定最终的采购需求，制定采购计划，签订合同或下达采购订单，配合各部门做好验', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('1970430a-a61d-4e36-8722-5faa6e92a617', '负责包括原料采购、装备及MRO采购、采购管理等工作', '责\n部门职责：\n负责包括原料采购、装备及MRO采购、采购管理等工作。统筹策划和确定采购战略，建设和维护供应商管理体系，控制采购总成本，协助决策层制定公司发展战略。\n1、建立采购体系，完善各项采购制度和采购流程；\n2、关注市场变化，做好与采购业务相关的市场调研及趋势预测工作，提供各类调研数据与报告，结合财务、生产、销售、战略等部门为公司经营决策提供参考依据。\n3、与各需求部门沟通协调确定最终的采购需求，制定采购计划，签订合同或下达采购订单，配合各部门做好验收入库、发票催收和付款工作。\n4、管控采购成本，寻找最佳批量，与技术、生产及质量管理部一起设定最佳质量标准，追求采购总成本最低。处理质量投诉，保障物', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('a6e01c89-bd5b-4948-bd8c-54118f6b8d75', '备及MRO采购、采购管理等工作', '备及MRO采购、采购管理等工作。统筹策划和确定采购战略，建设和维护供应商管理体系，控制采购总成本，协助决策层制定公司发展战略。\n1、建立采购体系，完善各项采购制度和采购流程；\n2、关注市场变化，做好与采购业务相关的市场调研及趋势预测工作，提供各类调研数据与报告，结合财务、生产、销售、战略等部门为公司经营决策提供参考依据。\n3、与各需求部门沟通协调确定最终的采购需求，制定采购计划，签订合同或下达采购订单，配合各部门做好验收入库、发票催收和付款工作。\n4、管控采购成本，寻找最佳批量，与技术、生产及质量管理部一起设定最佳质量标准，追求采购总成本最低。处理质量投诉，保障物料质量持续达标。\n5、平衡国内外采购', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('02b62c7d-82df-40e3-9b1f-0291ea97800d', '追求采购总成本最低', '与技术、生产及质量管理部一起设定最佳质量标准，追求采购总成本最低。处理质量投诉，保障物料质量持续达标。\n5、平衡国内外采购量，利用进料加工等税收优惠政策，寻找最合理价格。将公司效益做到最大化。\n6、在采购管理规定和招标制度规范下协调、配合各业务部门，完成项目及服务类采购工作，并做好定期抽查工作，向被检查单位及管理层提供整改建议报告。\n7、建立供应商档案，维护供应商关系，与具有市场竞争力、合作稳定性及持续性良好的供应商建立长期战略合作关系。\n仓储部部门职责\n圣奥化学泰国有限公司：\n负责原辅材料、设备及备品备件、产成品入库、在库及出库管理\n1.\t收根据物资检验结果办理入库手续，并进行分类保管。\n2.\t负', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('b2ddd703-1c6f-40f6-804b-4d0180bddc4b', '4.3采购价格主数据', '管理,部分供应商在MDM管理。\n供应商分类：国内供应商、国外供应商、员工供应商\n4.3采购价格主数据\n采购价格主数据在SRM系统价格库进行管理，目前没有同步到SAP系统；国内采购价格使用含税单价，进口采购业务价格使用外币不进行本币转换；\n付款条件清单如下：\n业务流程\n5.1物料主数据管理现状\n目前添加剂主数据申请流程为原料、产成品在集团MDM申请并同步到化工事业部主数据管理系统，化工事业部主数据系统与ERP接口创建物料主数据基本视图、工厂视图、采购视图、生产视图、销售视图、会计视图等在ERP中进行批量扩充。集团MDM申请的编码与SAP集成并分发基础视图。\n圣奥化学物料主数据根据审批流的不同分七类：\n', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('8c5e81f5-897b-4db6-9b28-0014cd4b71a2', '自动将原采购订单发布给供应商', '自动将原采购订单发布给供应商；供应商确认完成后，订单信息会传给SAP；\n固定资产需求计划：需求部门在OA中提报采购申请，审批通过后，归口管理部门需创建固定资产编码，IT类固资直接走目录化商城或电商商城采购流程；\n固定资产采购执行：非IT类采购员发起采购评审流程，并形成寻源结果及价格库数据，根据采购评审结果或寻源结果创建采购订单，对于需要走合同的订单，由采购员根据订单发起合同流程，无需签订合同的订单在订单审批完成后自动发布至供应商，需签订合同的订单在合同签订完成后发布至供应商，供应商对采购部发出的采购订单进行确认，确认完成后订单数据同步至SAP\n备品备件需求计划\nIEAM/OA提报需求计划，OA进行审', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('b83833fe-9203-4fb6-a85e-0122f0f16137', '引用采购订单签署合同', '同的订单在审批后不自动发布至供应商；合同签署时，引用采购订单签署合同；合同签署确认后，会自动将原采购订单发布给供应商；供应商确认完成后，订单信息会传给SAP；\n费用化需求计划：电商平台下单的走电商商城采购流程，不走电商商城下单需要需求部门在OA提出需求计划申请并对提报的需求并在OA进行审批，审批通过后，系统根据申请类型和物料品类进行自动分配采购员\n费用类采购执行：费用类采购订单支持无物料编码下单；采购员创建采购订单提交后，采购订单在SRM进行审批，审批通过的将直接发布给供应商进行确认；审批拒绝的订单返回订单维护界面重新编辑；供应商确认时主要对数量、交期进行确认，并且可对订单行项目信息编辑反馈信息，一', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('cd635d30-c8ff-4c85-a559-7fe06da61803', '5.5特殊采购流程', '用部门、质检、HSE共同评审，判断“让步接收”或“退货”，原材料质检不合格不收货（原材料如果某项非关键指标不合格可如让步接收，按订单数量扣减接收），D类和MRO类物料不合格直接换货供应商\n5.5 特殊采购流程\n5.5.1寄售业务\n1、前置仓寄售业务：工厂计划员统计下个月采购物料编码、数量，需求发京东京东按照需求清单发到工厂寄售仓库，货到后先验收，验收合格后在京东WMS收货到前置仓，使用部门按需领料，领料后保管员先在京东WMS出库，25号汇总消耗量形成对账单，根据对账单核对，部门在京东下订单，同时在ERP系统创建采购订单并收货，使用部门在IEAM提交领料申请，仓库确认物料编码、数量并审批，系统收到审批', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('03d575ba-4043-4926-bd3c-3d6e588c9dec', '采购员根据采购申请创建对发货工厂的采购订单同步到SAP', '工过账。\n4 工厂->工厂\n工厂提报需求OA审批后到SRM，采购员根据采购申请创建对发货工厂的采购订单同步到SAP，发货工厂交货单发货过账，收货工厂在SAP根据采购订单进行收货。\n7.流程清单\n7.1采购管理业务流程\n注：紧急采购流程与上述流程均一致，但需要10天内补齐单据\n（1）未来业务流程需要补充水电气采购流程、付款流程\n（2）未来业务流程服务采购和费用化采购需要做出区分\n（3）未来需要单独体现项目采购流程进行\n（4）未来业务流程需要补充招标流程\n（5）未来业务流程增加采购结算流程\n7.2库存管理业务流程\n（1）未来需要考虑危废处理流程\n8.需求及优化点：\n（一）物料主数据：SAP S4系统物料', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('75c49e1b-efb3-4947-b3e7-cb47cbc9ee0f', '收货工厂在SAP根据采购订单进行收货', 'SAP，发货工厂交货单发货过账，收货工厂在SAP根据采购订单进行收货。\n7.流程清单\n7.1采购管理业务流程\n注：紧急采购流程与上述流程均一致，但需要10天内补齐单据\n（1）未来业务流程需要补充水电气采购流程、付款流程\n（2）未来业务流程服务采购和费用化采购需要做出区分\n（3）未来需要单独体现项目采购流程进行\n（4）未来业务流程需要补充招标流程\n（5）未来业务流程增加采购结算流程\n7.2库存管理业务流程\n（1）未来需要考虑危废处理流程\n8.需求及优化点：\n（一）物料主数据：SAP S4系统物料主数据需增加物料评估类型（原材料、库存商品、备件等）和物料组（机备件、标准件、电器、仪表等）\n（二）采购：\n', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('216e3b5c-a36a-4532-a2b4-b7eee3f354ec', '注：紧急采购流程与上述流程均一致', '理业务流程\n注：紧急采购流程与上述流程均一致，但需要10天内补齐单据\n（1）未来业务流程需要补充水电气采购流程、付款流程\n（2）未来业务流程服务采购和费用化采购需要做出区分\n（3）未来需要单独体现项目采购流程进行\n（4）未来业务流程需要补充招标流程\n（5）未来业务流程增加采购结算流程\n7.2库存管理业务流程\n（1）未来需要考虑危废处理流程\n8.需求及优化点：\n（一）物料主数据：SAP S4系统物料主数据需增加物料评估类型（原材料、库存商品、备件等）和物料组（机备件、标准件、电器、仪表等）\n（二）采购：\n报表需求\n（1）降本率报表（和预算相比、历史价、市场价）\n（2）执行率报表\n（3）各家库存实时报表', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('2c1d6fc0-e5c3-4f70-a3e3-2dc4752b742d', '（二）采购：', '库存商品、备件等）和物料组（机备件、标准件、电器、仪表等）\n（二）采购：\n报表需求\n（1）降本率报表（和预算相比、历史价、市场价）\n（2）执行率报表\n（3）各家库存实时报表（需要取SRM价格）\n（4）采购流程执行效率表，每个流程需要提醒功能\n（5）采购价格分析报表（横纵向比较，横向比较其他工厂，纵向比较前期采购价格）\n优化需求\n（1）三单匹配目前由人工操作，是否能够系统自动匹配，系统比较有问题的系统自动提醒\n（2）STO业务流程优化，统一工厂间调拨业务，现系统根据物料类型，部分物料采购订单创建在1753，发货工厂创建发货通知单，建议通过系统上线，统一工厂间调拨业务流程，其中国内与泰国工厂调拨还需要创', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('ec8dc863-703b-4790-8596-c9fab88b2e20', 'MM模块主要包括:物料需求计划、物料主数据、采购、库存管理、仓库管理、后勤信息系统等几个组成部分', '用中最为广泛应用的模块，与财务、生产、销售、成本等模块均有密切的关系。特别是对物料主数据中各种参数的设置将直接影响到成本、生产、销售中的流程和结果。MM 模块主要包括:物料需求计划、物料主数据、采购、库存管理、仓库管理、后勤信息系统等几个组成部分。\n物料主数据是整个物料管理模块的基石,物料主数据资料设置的正确与否将直接影响到相关模块运作的精确程度。\nERP 的采购包括有框架协议、询价报价、信息记录、采购申请、采购订单等部分组成。我们可以通过事先设置的采购协议依据需求自动建立采购申请，并将这些采购申请转为采购订单。同时也可以通过信息记录来限制采购员擅自更改采购价格。建立一个具备有效监控的采购体系。添加', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('bc075048-fd4b-4997-b51a-32acff212097', '库存管理单元实际上包括物料收发的整个过程', '购申请转为采购订单。同时也可以通过信息记录来限制采购员擅自更改采购价格。建立一个具备有效监控的采购体系。添加剂事业部目前询报价、价格库、供应商管理、合同管理以及付款审核等功能在SRM系统中进行管理。\n库存管理单元实际上包括物料收发的整个过程，这个过程不仅仅是采购收货、采购退货还包括生产的收发、库存调整甚至是跨公司、工厂的转移。在做库存管理时系统也将记录系统的操作时间和记帐时间，并允许记录实际操作的单据号码，为后续的查询提供和检索方便。添加剂事业部通过MES、WMS系统与ERP系统集成实现库存物资出入库管理，极大提高日常库存管理的工作效率。\n组织机构\n中化添加剂事业部组织架构图，如下：\n2.1采购部组', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('8b3ba5ac-4948-4ad6-a9fc-a937cf0eeaee', '在做库存管理时系统也将记录系统的操作时间和记帐时间', '移。在做库存管理时系统也将记录系统的操作时间和记帐时间，并允许记录实际操作的单据号码，为后续的查询提供和检索方便。添加剂事业部通过MES、WMS系统与ERP系统集成实现库存物资出入库管理，极大提高日常库存管理的工作效率。\n组织机构\n中化添加剂事业部组织架构图，如下：\n2.1采购部组织架构图\n2.2 仓储部门组织架构图\n部门职责\n采购部部门职责\n部门职责：\n负责包括原料采购、装备及MRO采购、采购管理等工作。统筹策划和确定采购战略，建设和维护供应商管理体系，控制采购总成本，协助决策层制定公司发展战略。\n1、建立采购体系，完善各项采购制度和采购流程；\n2、关注市场变化，做好与采购业务相关的市场调研及趋势', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('cfd82fb1-b0ba-4b89-a9f9-ff4daca28471', '5.4库存管理现状', '下比价， OA申请在SRM创建采购订单，采购订单在SRM进行审批，审批通过后打印订单，如果订单金额大于十万，需要打印合同（对数量、交期进行确认），与供应商进行签字确认，SRM 订单同步SAP\n5.4 库存管理现状\n5.4.1安徽圣奥化学科技有限公司\n入库业务\n原料：MES记录过磅信息、质检信息、到库信息并实物入库，到货后，通过MES记录过磅信息，质检信息、到库信息办理入库（保税的MIBK物料按报关信息入库），手动SAP操作收货入库\n备品备件：到货后线下手动将质检合格信息录入到MES，合格品手动SAP操作收货入库\n包材：到货后线下手动将质检合格信息录入到MES，合格品手动SAP操作收货入\n能源：SAP', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('d61cdde3-120f-4570-aa93-325ded049846', '7.2库存管理业务流程', '补充水电气采购流程、付款流程\n（2）未来业务流程服务采购和费用化采购需要做出区分\n（3）未来需要单独体现项目采购流程进行\n（4）未来业务流程需要补充招标流程\n（5）未来业务流程增加采购结算流程\n7.2库存管理业务流程\n（1）未来需要考虑危废处理流程\n8.需求及优化点：\n（一）物料主数据：SAP S4系统物料主数据需增加物料评估类型（原材料、库存商品、备件等）和物料组（机备件、标准件、电器、仪表等）\n（二）采购：\n报表需求\n（1）降本率报表（和预算相比、历史价、市场价）\n（2）执行率报表\n（3）各家库存实时报表（需要取SRM价格）\n（4）采购流程执行效率表，每个流程需要提醒功能\n（5）采购价格分析报表', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('72fcad1a-37a5-44ad-a298-07f1ca88835c', '参与对生产过程中质量进行管控', '、销售中心对接客户资源的管理，对客户资源信息进行保密。\n2.负责对公司重要客户定期进行交流沟通，了解客户需求，关注客户满意度，组织客户信息评审并反馈。\n3.负责在授权的情况下行使客户代表的职责，参与对生产过程中质量进行管控，确保产品质量符合客户要求。\n4.负责结合圣奥化学运营中心对公司客户满意度定期做自我评价，对评价的过程及结果进行记录并做到持续改进。\n5.负责依据圣奥化学运营中心下发的销售任务结合公司实际产销存情况排程发货计划，制定公司内部发货管理控程序，对发货流程及包装要求等实施有效控制。\n6.负责与生产系统、检测中心做好出货成品的编号的追溯工作。\n7.负责根据IATF标准要求对最终库存成品的特', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('89a14d05-8570-4d5e-8d1c-2103926762eb', '5.负责依据圣奥化学运营中心下发的销售任务结合公司实际产销存情况排程发货计划', '求。\n4.负责结合圣奥化学运营中心对公司客户满意度定期做自我评价，对评价的过程及结果进行记录并做到持续改进。\n5.负责依据圣奥化学运营中心下发的销售任务结合公司实际产销存情况排程发货计划，制定公司内部发货管理控程序，对发货流程及包装要求等实施有效控制。\n6.负责与生产系统、检测中心做好出货成品的编号的追溯工作。\n7.负责根据IATF标准要求对最终库存成品的特性制定控制计划。\n山东圣奥化学科技有限公司：\n1、负责仓储原材物料、产品、顾客产品的标识、贮存、摆放及维护、保管；\n2、负责搬运、贮存、防护和交过程的组织实施；\n3、负责仓库环境的管理，严格执行有关防火和危险物品管理规定，搞好仓库防火、防盗、危险', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO business_processes (id, name, description, owner, status, classification, level, parent_id, meta_data, created_at, updated_at)
VALUES ('cd378ef0-d526-47fe-ae6a-3fc566985656', '（1）未来业务流程需要补充水电气采购流程、付款流程', '货工厂交货单发货过账，收货工厂在SAP根据采购订单进行收货。\n7.流程清单\n7.1采购管理业务流程\n注：紧急采购流程与上述流程均一致，但需要10天内补齐单据\n（1）未来业务流程需要补充水电气采购流程、付款流程\n（2）未来业务流程服务采购和费用化采购需要做出区分\n（3）未来需要单独体现项目采购流程进行\n（4）未来业务流程需要补充招标流程\n（5）未来业务流程增加采购结算流程\n7.2库存管理业务流程\n（1）未来需要考虑危废处理流程\n8.需求及优化点：\n（一）物料主数据：SAP S4系统物料主数据需增加物料评估类型（原材料、库存商品、备件等）和物料组（机备件、标准件、电器、仪表等）\n（二）采购：\n报表需求\n', '', 'active', '核心流程', 1, NULL, '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO application_systems (id, name, description, system_type, vendor, version, status, owner, meta_data, created_at, updated_at)
VALUES ('f2b23782-6de1-4258-a590-ce7dfd48f260', 'ERP系统', '企业资源规划系统，管理企业核心业务流程', 'ERP', 'SAP', 'S/4HANA 2023', 'active', 'IT部', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO application_systems (id, name, description, system_type, vendor, version, status, owner, meta_data, created_at, updated_at)
VALUES ('46962368-bf94-4a95-af2c-617b7e0cc326', 'CRM系统', '客户关系管理系统，管理客户信息和销售流程', 'CRM', 'Salesforce', '2024.1', 'active', 'IT部', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO application_systems (id, name, description, system_type, vendor, version, status, owner, meta_data, created_at, updated_at)
VALUES ('d3ece49f-ca14-43d7-87c5-587a29fac960', 'SAP系统', '并统一管理、国资委新管理需求以及SAP产品版本更新换代的要求，事业部计划在2025年启动添加剂事业部SAP系统升级至S4 HANA的项目。\n项目目标\n落实集团统一数据和流程标准，实现数据纵向穿透，业财横向贯通的管理要求，提升企业风控水平：通过新主数据平台实现统一数据标准的落地，进而优化数据分析流程，提升数据驱动决策的能力，最终实现业务价值的最大化；通过流程标准的落地，将内控要点嵌入关键流程节点和系统权限，从而实现整体流程的统一管理和合规性保障。不仅有助于提升企业的运营效率和风险防控能力，还能为未来的业务扩', 'ERP', '', '', 'active', '', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO application_systems (id, name, description, system_type, vendor, version, status, owner, meta_data, created_at, updated_at)
VALUES ('582323f2-5a88-45c0-b83c-9d0a62d19310', 'SAP S4系统', '流程\n7.2库存管理业务流程\n（1）未来需要考虑危废处理流程\n8.需求及优化点：\n（一）物料主数据：SAP S4系统物料主数据需增加物料评估类型（原材料、库存商品、备件等）和物料组（机备件、标准件、电器、仪表等）\n（二）采购：\n报表需求\n（1）降本率报表（和预算相比、历史价、市场价）\n（2）执行率报表\n（3）各家库存实时报表（需要取SRM价格）\n（4）采购流程执行效率表，每个流程需要提醒功能\n（5）采购价格分析报表（横纵向比较，横向比较其他工厂，纵向比较前期采购价格）\n优化需求\n（1）三单匹配目前由人工操作，是', 'ERP', '', '', 'active', '', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO application_systems (id, name, description, system_type, vendor, version, status, owner, meta_data, created_at, updated_at)
VALUES ('c413e47b-1b20-4523-99a2-f2b449f27173', 'ERP系统', '上重新实施系统，优化企业生产运营流程，优化成本核算结构，促进管理升级：在原有成熟流程的基础上重新实施ERP系统，理顺同外围系统的流程关系，统一产业链内部经营单元的产供销流程，帮助企业解决多年系统使用中的困难和不足，优化系统业务流程，提高经营管理效率。优化点包括但不限于：理顺月结流程，确保月结对正常生产运营的影响最小化；优化BOM结构；优化统一物流流程；优化产成品、原料、备品备件类商品的关联交易流程；充分利用MRP功能协助生产；探讨并实现公用工程类物质的合理化成本核算方案；实现产业链成本还原，实现销售成本还', 'ERP', '', '', 'active', '', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO application_systems (id, name, description, system_type, vendor, version, status, owner, meta_data, created_at, updated_at)
VALUES ('76074910-0552-4163-8655-9d9b9e1b5c4f', 'CRM系统', '前外围系统与物资模块集成：现有使用和SAP有接口的系统主要有 MES 系统、WMS系统、SRM系统、CRM系统、OA、IEAM、MDM、66快车、EOS和财务共享系统。各工厂使用外围系统的情况如下表：\n1.4 MM模块概述\n物料管理业务线条的ERP应用中最为广泛应用的模块，与财务、生产、销售、成本等模块均有密切的关系。特别是对物料主数据中各种参数的设置将直接影响到成本、生产、销售中的流程和结果。MM 模块主要包括:物料需求计划、物料主数据、采购、库存管理、仓库管理、后勤信息系统等几个组成部分。\n物料主数据', 'CRM', '', '', 'active', '', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('450bf1e5-4e51-4724-9846-02a30d67f93b', '订单实体', '订单数据实体，包含订单基本信息', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('d67d7ce3-399c-42e9-8fca-3b781625544f', '客户实体', '客户数据实体，包含客户基本信息', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('29198ea4-768f-45e9-8be7-901caa4ccc43', '引用采购订单签署合同', '合同签署时，引用采购订单签署合同；合同签署确认后，会自动将原采购订单发布给供应商；供应商确认完成后，订单信息会传给SAP；\n固定资产需求计划：需求部门在OA中提报采购申请，审批通过后，归口管理部门需创建固定资产编码，IT类固资直接走目录化商城或电商商城采购流程；\n固定资产采购执行：非IT类采购员发起采购评审流程，并形成寻源结果及价格库数据，根据采购评审结果或寻源结果创建采购订单，对于需要走合同的订单，由采购员根据订单发起合同流程，无需签订合同的订单在订单审批完成后自动发布至供应商，需签订合同的订单在合', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('d26ce7e1-a905-4c19-a0e9-82c78185ba41', '需签订合同的订单在合同签订完成后发布至供应商', '应商，需签订合同的订单在合同签订完成后发布至供应商，供应商对采购部发出的采购订单进行确认，确认完成后订单数据同步至SAP\n备品备件需求计划\nIEAM/OA提报需求计划，OA进行审批，审批通过后，系统根据申请类型和物料品类进行自动分配采购员，采购员根据采购申请进行寻源，并形成寻源结果和价格库数据\n采购执行\n根据寻源结果或价格库价格创建采购订单，采购订单在SRM中进行审批；\n采购员在维护订单的时候判断是否需要签署合同（订单金额超过5万、或存在分期付款、或存在质保金、或有图纸要求时需要签订合同），需要签署合', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('097aaa1a-8c05-44ea-bfcd-18211b067785', '采购员在SRM创建采购订单', '，供方提供箱单发票后，采购员在SRM创建采购订单，同时采购订单在SRM进行审批，审批通过后直接将采购订单信息同步给MES\n备品备件/包材/固定资产/费用化：OA提报需求，审批后通过后线下比价， OA申请在SRM创建采购订单，采购订单在SRM进行审批，审批通过后打印订单，如果订单金额大于十万，需要打印合同（对数量、交期进行确认），与供应商进行签字确认，SRM 订单同步SAP\n5.4 库存管理现状\n5.4.1安徽圣奥化学科技有限公司\n入库业务\n原料：MES记录过磅信息、质检信息、到库信息并实物入库，到货后', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('456d90be-7e86-41f0-bb6a-ecbcdd0d94e1', '按订单数量扣减接收', '起不合格评审处置申请单，由使用部门、质检、HSE共同评审，判断“让步接收”或“退货”，如让步接收，按订单数量扣减接收，D类和MRO类物料不合格直接退货供应商\n5.4.2连云港圣奥化学科技有限公司\n入库：\n原料：地磅记录重量信息，SAP基于采购订单手工收货入库\n备品备件/包材：到货后线下质检，合格品后手动SAP操作收货入库\n能源：基于线下盘点计算数量，SAP创建无审批采购订单，基于线下盘点数量，采购订单收货入库\n产品：SAP创建生产订单, 上位机根据生产订单创建生产订单任务，WMS根据生产任务进行实物收', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('df7e2185-6282-4622-9555-438fbf954b6c', '按订单数量扣减接收）', '，判断“让步接收”或“退货”，原材料质检不合格不收货（原材料如果某项非关键指标不合格可如让步接收，按订单数量扣减接收），D类和MRO（未来考虑部分退货）类物料不合格直接退货供应商\n不合格品退货流程：工厂PMC打印退货通知单，安排物流退货，收到退货实物通知总部供应链。供应链单证员基于客户退货单在SAP中操作，对退货通知单退货过账，开销售红字发票；判断是否为公司间销售，如果是，创建退货采购订单并退货过账。工厂基于退货采购订单创建工厂退货单，退货收货后开公司间销售红字发票。\n5.4.4泰安圣奥化工有限公司\n', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('3c3fa60a-e230-4498-8360-213db08109d9', '（2）物料需求计划与执行报表（采购申请数量、已创建订单数量', '是否有不以库位管理产品的合格状态，减少虚拟库位号\n（2）物料需求计划与执行报表（采购申请数量、已创建订单数量，已执行数量）\n（3）库龄报表（3个月内、3-6个月划分，6-12个月，12个月以上）\n（4）生产部门返工信息与库存数量与仓储部门不同步，未来希望仓储部门能及时同步物料库存数量信息\n（5）备品备件库存库位号显示，目前备品备件收货在WMS，需要与WMS同步信息\n（6）出入库领料单打印（中英或英泰文）\n（7）其他系统能及时同步SAP库存\n（8）销售报表：显示销售日期、数量、送达方等信息\n其他：【金山', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('80d07f37-a9b5-465b-b8d7-a9e365d6c305', '特别是对物料主数据中各种参数的设置将直接影响到成本、生产、销售中的流程和结果', '管理业务线条的ERP应用中最为广泛应用的模块，与财务、生产、销售、成本等模块均有密切的关系。特别是对物料主数据中各种参数的设置将直接影响到成本、生产、销售中的流程和结果。MM 模块主要包括:物料需求计划、物料主数据、采购、库存管理、仓库管理、后勤信息系统等几个组成部分。\n物料主数据是整个物料管理模块的基石,物料主数据资料设置的正确与否将直接影响到相关模块运作的精确程度。\nERP 的采购包括有框架协议、询价报价、信息记录、采购申请、采购订单等部分组成。我们可以通过事先设置的采购协议依据需求自动建立采购申', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('ab2a996c-dd68-4f7b-bcab-b9dab3c59a99', 'MM模块主要包括:物料需求计划、物料主数据、采购、库存管理、仓库管理、后勤信息系统等几个组成部分', '主数据中各种参数的设置将直接影响到成本、生产、销售中的流程和结果。MM 模块主要包括:物料需求计划、物料主数据、采购、库存管理、仓库管理、后勤信息系统等几个组成部分。\n物料主数据是整个物料管理模块的基石,物料主数据资料设置的正确与否将直接影响到相关模块运作的精确程度。\nERP 的采购包括有框架协议、询价报价、信息记录、采购申请、采购订单等部分组成。我们可以通过事先设置的采购协议依据需求自动建立采购申请，并将这些采购申请转为采购订单。同时也可以通过信息记录来限制采购员擅自更改采购价格。建立一个具备有效监', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('6f149aaf-1f55-4d56-8cf5-797ddd2eb37d', '对客户资源信息进行保密', '对客户资源信息进行保密。\n2.负责对公司重要客户定期进行交流沟通，了解客户需求，关注客户满意度，组织客户信息评审并反馈。\n3.负责在授权的情况下行使客户代表的职责，参与对生产过程中质量进行管控，确保产品质量符合客户要求。\n4.负责结合圣奥化学运营中心对公司客户满意度定期做自我评价，对评价的过程及结果进行记录并做到持续改进。\n5.负责依据圣奥化学运营中心下发的销售任务结合公司实际产销存情况排程发货计划，制定公司内部发货管理控程序，对发货流程及包装要求等实施有效控制。\n6.负责与生产系统、检测中心做好出货', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('a3a2c1ec-d50e-4259-a3ab-5d6168ecbd85', 'M模块主要包括:物料需求计划、物料主数据、采购、库存管理、仓库管理、后勤信息系统等几个组成部分', 'M 模块主要包括:物料需求计划、物料主数据、采购、库存管理、仓库管理、后勤信息系统等几个组成部分。\n物料主数据是整个物料管理模块的基石,物料主数据资料设置的正确与否将直接影响到相关模块运作的精确程度。\nERP 的采购包括有框架协议、询价报价、信息记录、采购申请、采购订单等部分组成。我们可以通过事先设置的采购协议依据需求自动建立采购申请，并将这些采购申请转为采购订单。同时也可以通过信息记录来限制采购员擅自更改采购价格。建立一个具备有效监控的采购体系。添加剂事业部目前询报价、价格库、供应商管理、合同管理以', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('833d4f06-551d-46c8-b07b-1bd3482382a5', '物料主数据是整个物料管理模块的基石,物料主数据资料设置的正确与否将直接影响到相关模块运作的精确程度', '主数据、采购、库存管理、仓库管理、后勤信息系统等几个组成部分。\n物料主数据是整个物料管理模块的基石,物料主数据资料设置的正确与否将直接影响到相关模块运作的精确程度。\nERP 的采购包括有框架协议、询价报价、信息记录、采购申请、采购订单等部分组成。我们可以通过事先设置的采购协议依据需求自动建立采购申请，并将这些采购申请转为采购订单。同时也可以通过信息记录来限制采购员擅自更改采购价格。建立一个具备有效监控的采购体系。添加剂事业部目前询报价、价格库、供应商管理、合同管理以及付款审核等功能在SRM系统中进行管', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('fa44dc03-8b4c-456f-99e5-650c96f3072a', '添加剂事业部MM模块的基础数据主要包括物料主数据、供应商主数据、采购价格主数据', '。\n8、负责仓储部属地QHSE四个零目标实现。\n基础数据\n添加剂事业部 MM 模块的基础数据主要包括物料主数据、供应商主数据、采购价格主数据。\n4.1物料主数据及采购物资分类\n添加剂事业部物料目前主要分为原辅料及包装，MRO类物资、产成品（最终产品和过程产品）和其他物资，其中原辅材料及包装又细分为A类原料、B类原料、C类原料、D类原料，MRO类物资细分为生产设备、备品备件、油品类、劳保用品、化验用品、信息用品（硬件）、软件、办公用品，其他物资分为服务、专项项目、工程项目，同时，水电气风在系统中也做物料', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('4c1ed0b2-800e-4682-ace3-1ab7a62d6faf', '5.1物料主数据管理现状', '采购价格使用含税单价，进口采购业务价格使用外币不进行本币转换；\n付款条件清单如下：\n业务流程\n5.1物料主数据管理现状\n目前添加剂主数据申请流程为原料、产成品在集团MDM申请并同步到化工事业部主数据管理系统，化工事业部主数据系统与ERP接口创建物料主数据基本视图、工厂视图、采购视图、生产视图、销售视图、会计视图等在ERP中进行批量扩充。集团MDM申请的编码与SAP集成并分发基础视图。\n圣奥化学物料主数据根据审批流的不同分七类：\n①产成品、——由QC经理、集团EHS审核后，在中化集团主数据系统（MDM）', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('04e97ace-e6be-4d3e-8e6e-e426107893a7', '圣奥化学物料主数据根据审批流的不同分七类：', '售视图、会计视图等在ERP中进行批量扩充。集团MDM申请的编码与SAP集成并分发基础视图。\n圣奥化学物料主数据根据审批流的不同分七类：\n①产成品、——由QC经理、集团EHS审核后，在中化集团主数据系统（MDM）操作新建;\n②主材（不含保密物料）——由集团HSE审核后，在中化集团主数据系统（MDM）操作新建;\n③包装袋——需由QC经理审批，有质量标准/质量编码；\n④其他生产性（半成品、辅助原材料、保密物料、包装辅材、副产品等①②③以外的所有生产类物料）；\n⑤非生产类物料（备品备件、HSE、电气仪表等）；', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('c906db16-345b-48fa-a323-a2be3edc265a', '其中①产成品②主材先在MDM（中化集团主数据管理系统）新增物料', 'HSE、电气仪表等）；\n⑥中间产品、副产品；\n⑦实验室耗材。\n其中①产成品②主材先在MDM（中化集团主数据管理系统）新增物料，并由MDM附码，再用MDM的物料号在SAP新建/扩展；③包装物④其他生产性⑤非生产性直接在SAP创建；⑥中间产品、副产品⑦实验室耗材直接在MES创建。\n物料批次管理：目前各生产工厂均对产成品启用了批次管理，用于产品的唯一标识管理和质量追溯；泰国部分原材料启用了批次管理，进行质量跟踪。\n5.2供应商主数据管理现状\n供应商注册，提交基本信息，注册完成后进入供应商库。\n根据业务需要，邀请供应商信息维护调查表，供应商需先填报供应商基本信', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('b9db9bcc-f795-4ddc-bd4a-8b8dabe82f91', '4.2供应商主数据', '务、专项项目、工程项目，同时，水电气风在系统中也做物料化管理，有对应的物料编码。\n物料分类：\n4.2供应商主数据\n供应商管理方式包括准入制和备案制，主材和包材供应商采用准入制，准入制需供应商提供供应商资质资料、质检单、中试报告（如有）等，备品备件和服务类供应商一般采用备案制，备案制需供应商提供供应商资质资料审核通过即可。\n供应商采购目录和黑名单均在SRM 系统管理,部分供应商在MDM管理。\n供应商分类：国内供应商、国外供应商、员工供应商\n4.3采购价格主数据\n采购价格主数据在SRM系统价格库进行管理，目', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('58522196-cdf0-4b12-b9df-d7cf8907796e', '5.2供应商主数据管理现状', '用了批次管理，用于产品的唯一标识管理和质量追溯；泰国部分原材料启用了批次管理，进行质量跟踪。\n5.2供应商主数据管理现状\n供应商注册，提交基本信息，注册完成后进入供应商库。\n根据业务需要，邀请供应商信息维护调查表，供应商需先填报供应商基本信息，由化工事业部主数据系统审核通过后，由集团主数据系统维护和管理供应商主数据基本视图，事业部主数据系统维护供应商主数据财务和采购视图。\n5.3需求计划到采购执行管理现状\n5.3.1   国内\n主材/包材需求计划：生产/运营OA需求计划提报并对提报的需求进行审批，审批通', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('028e4410-7f35-46ae-bf1c-51e0749ad35c', '后进入供应商库', '后进入供应商库。\n根据业务需要，邀请供应商信息维护调查表，供应商需先填报供应商基本信息，由化工事业部主数据系统审核通过后，由集团主数据系统维护和管理供应商主数据基本视图，事业部主数据系统维护供应商主数据财务和采购视图。\n5.3需求计划到采购执行管理现状\n5.3.1   国内\n主材/包材需求计划：生产/运营OA需求计划提报并对提报的需求进行审批，审批通过后，系统根据申请类型和物料品类进行自动分配采购员，采购员根据采购申请进行寻源，并形成寻源结果和价格库数据\n主材/包材采购执行：根据寻源结果或价格库价格创建采购订单，采购订单在SRM中进行审批；采购员在维护订单的时候判断是否需要签署合同（订单金', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('21647616-5d9f-4baf-9e50-2f5a6a397109', '7.2库存管理业务流程', '采购结算流程\n7.2库存管理业务流程\n（1）未来需要考虑危废处理流程\n8.需求及优化点：\n（一）物料主数据：SAP S4系统物料主数据需增加物料评估类型（原材料、库存商品、备件等）和物料组（机备件、标准件、电器、仪表等）\n（二）采购：\n报表需求\n（1）降本率报表（和预算相比、历史价、市场价）\n（2）执行率报表\n（3）各家库存实时报表（需要取SRM价格）\n（4）采购流程执行效率表，每个流程需要提醒功能\n（5）采购价格分析报表（横纵向比较，横向比较其他工厂，纵向比较前期采购价格）\n优化需求\n（1）三单匹配目前由人工操作，是否能够系统自动匹配，系统比较有问题的系统自', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO data_entities (id, name, description, entity_type, meta_data, created_at, updated_at)
VALUES ('84792745-ce01-475e-920b-4b6653676ee5', '（3）各家库存实时报表（需要取SRM价格）', '（二）采购：\n报表需求\n（1）降本率报表（和预算相比、历史价、市场价）\n（2）执行率报表\n（3）各家库存实时报表（需要取SRM价格）\n（4）采购流程执行效率表，每个流程需要提醒功能\n（5）采购价格分析报表（横纵向比较，横向比较其他工厂，纵向比较前期采购价格）\n优化需求\n（1）三单匹配目前由人工操作，是否能够系统自动匹配，系统比较有问题的系统自动提醒\n（2）STO业务流程优化，统一工厂间调拨业务，现系统根据物料类型，部分物料采购订单创建在1753，发货工厂创建发货通知单，建议通过系统上线，统一工厂间调拨', '业务实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO technology_components (id, name, description, component_type, version, meta_data, created_at, updated_at)
VALUES ('06bd9ab8-27e7-4841-97e0-898cb9716313', 'PostgreSQL数据库', '关系型数据库管理系统', '数据库', '15', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO technology_components (id, name, description, component_type, version, meta_data, created_at, updated_at)
VALUES ('7c4a526e-d169-4302-ae0b-671e7d5bdcd3', 'Redis缓存', '内存数据结构存储系统', '缓存', '7', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO technology_components (id, name, description, component_type, version, meta_data, created_at, updated_at)
VALUES ('a7f79b7e-fc9f-4b7e-8dde-f116d6769290', '（4）接口', '等业务\n（3）简化能源采购进厂业务流程，月末以消耗量自动触发采购订单，自动收货、保持进出平衡\n（4）接口，现备品备件IEAM系统领料，在IEAM系统创建领单，选择成本中心、库位，物料，数量提交、审批，同步SAP自动扣减库存，IEAM同步SAP中间表对接库存，SAP和IEAM系统无库存同步接口，建议增加接口\n（二）仓储部门：\n（1）库位管理，现系统中成品库3000和3100主要是区分能否发货合格状态，S4系统是否有不以库位管理产品的合格状态，减少虚拟库位号\n（2）物料需求计划与执行报表（采购申请数量、', '接口', '', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO technology_components (id, name, description, component_type, version, meta_data, created_at, updated_at)
VALUES ('e45e0baf-68bc-4101-b640-183dfac069f1', 'SAP和IEAM系统无库存同步接口', '提交、审批，同步SAP自动扣减库存，IEAM同步SAP中间表对接库存，SAP和IEAM系统无库存同步接口，建议增加接口\n（二）仓储部门：\n（1）库位管理，现系统中成品库3000和3100主要是区分能否发货合格状态，S4系统是否有不以库位管理产品的合格状态，减少虚拟库位号\n（2）物料需求计划与执行报表（采购申请数量、已创建订单数量，已执行数量）\n（3）库龄报表（3个月内、3-6个月划分，6-12个月，12个月以上）\n（4）生产部门返工信息与库存数量与仓储部门不同步，未来希望仓储部门能及时同步物料库存数', '接口', '', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO technology_components (id, name, description, component_type, version, meta_data, created_at, updated_at)
VALUES ('8731e773-14b3-45a4-8c7d-3d53130b0d62', '4.负责物料的存储管理和存储状态', '2.负责库存物资按其分类原则进行分类储存。\n3.负责编制存货管理规定并优化管理流程。\n4.负责物料的存储管理和存储状态。\n5.负责有效控制并提升物资周转\n客户管理：\n1.负责与圣奥化学运营中心、销售中心对接客户资源的管理，对客户资源信息进行保密。\n2.负责对公司重要客户定期进行交流沟通，了解客户需求，关注客户满意度，组织客户信息评审并反馈。\n3.负责在授权的情况下行使客户代表的职责，参与对生产过程中质量进行管控，确保产品质量符合客户要求。\n4.负责结合圣奥化学运营中心对公司客户满意度定期做自我评价，', '存储', '', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO architecture_relationships (id, source_id, source_type, target_id, target_type, relationship_type, description, properties, created_at, updated_at)
VALUES ('b04d3b84-9ba3-4290-a3f2-71615a47561d', '3a487f63-afd0-4df1-9562-60fd9c91cd4d', 'business_process', 'f2b23782-6de1-4258-a590-ce7dfd48f260', 'application_system', 'implements', '采购流程由ERP系统实现', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO architecture_relationships (id, source_id, source_type, target_id, target_type, relationship_type, description, properties, created_at, updated_at)
VALUES ('321bfbee-4c94-4693-801b-77203f737ffa', 'f2b23782-6de1-4258-a590-ce7dfd48f260', 'application_system', '450bf1e5-4e51-4724-9846-02a30d67f93b', 'data_entity', 'uses', 'ERP系统使用订单实体', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO architecture_relationships (id, source_id, source_type, target_id, target_type, relationship_type, description, properties, created_at, updated_at)
VALUES ('f55500b3-58a2-4117-bf27-5e370e2292ce', '3a487f63-afd0-4df1-9562-60fd9c91cd4d', 'business_process', 'f2b23782-6de1-4258-a590-ce7dfd48f260', 'application_system', 'implements', '采购流程由ERP系统实现', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO architecture_relationships (id, source_id, source_type, target_id, target_type, relationship_type, description, properties, created_at, updated_at)
VALUES ('3fd8e202-1876-4edb-9bdc-d16daf474aa8', 'be601e9b-90cc-4e62-b436-1ad25a919c2d', 'business_process', '46962368-bf94-4a95-af2c-617b7e0cc326', 'application_system', 'implements', '销售流程由CRM系统实现', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO architecture_relationships (id, source_id, source_type, target_id, target_type, relationship_type, description, properties, created_at, updated_at)
VALUES ('9d2c8d3d-bd97-48b1-a574-1048770c055f', 'ef74140e-f99c-45ec-bda2-6fe51c4d4a93', 'business_process', 'd3ece49f-ca14-43d7-87c5-587a29fac960', 'application_system', 'implements', '2.1采购部组织架构图由SAP系统实现', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO architecture_relationships (id, source_id, source_type, target_id, target_type, relationship_type, description, properties, created_at, updated_at)
VALUES ('772002c8-f7e9-41fb-a489-7c4c1614079c', 'b5b88459-c171-4492-b594-fdbdb9f381d0', 'business_process', '582323f2-5a88-45c0-b83c-9d0a62d19310', 'application_system', 'implements', '负责包括原料采购、装备及MRO采购、采购管理等工作由SAP S4系统实现', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO architecture_relationships (id, source_id, source_type, target_id, target_type, relationship_type, description, properties, created_at, updated_at)
VALUES ('e2ba8f1e-77fb-402e-a10a-532b83785f45', '42080eaf-6fed-43cc-970a-268a2f3d6319', 'business_process', 'c413e47b-1b20-4523-99a2-f2b449f27173', 'application_system', 'implements', '备及MRO采购、采购管理等工作由ERP系统实现', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;


INSERT INTO architecture_relationships (id, source_id, source_type, target_id, target_type, relationship_type, description, properties, created_at, updated_at)
VALUES ('cb191cb6-eb3e-43a8-a3f4-b856d564e3be', '926817fe-7fbf-457c-b1e4-f3db0fcb3b90', 'business_process', '76074910-0552-4163-8655-9d9b9e1b5c4f', 'application_system', 'implements', '追求采购总成本最低由CRM系统实现', '{}', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

