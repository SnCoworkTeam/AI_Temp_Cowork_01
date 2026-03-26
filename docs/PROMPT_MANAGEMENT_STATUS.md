# 提示词管理现状分析

## 当前状态

### ✅ 已实现的功能

1. **提示词引擎（PromptEngine）**
   - 位置：`agent-service/src/core/prompt_engine/`
   - 功能：提示词优化、验证、缓存
   - 支持从YAML文件加载模板

2. **模板管理器（TemplateManager）**
   - 位置：`agent-service/src/core/prompt_engine/template_manager.py`
   - 功能：从YAML文件加载模板，支持动态重载
   - 配置文件：`agent-service/config/prompt_templates.yaml`

3. **部分提示词已统一管理**
   - 部分提示词已迁移到YAML配置文件
   - 支持任务分类（TaskCategory）

### ❌ 缺失的功能

1. **后台管理界面**
   - ❌ 没有提示词管理的后台页面
   - ❌ 无法通过UI查看、编辑提示词
   - ❌ 无法可视化提示词效果

2. **API管理接口**
   - ❌ 没有提示词CRUD的API
   - ❌ 无法通过API动态管理提示词
   - ❌ 无法版本控制提示词

3. **数据库存储**
   - ❌ 提示词只存在YAML文件中
   - ❌ 没有数据库存储，无法追踪历史
   - ❌ 无法多环境管理（开发/测试/生产）

4. **大量硬编码提示词**
   - ❌ 很多Agent中仍有硬编码的f-string提示词
   - ❌ 例如：`mcp_tool_agent.py`、`content_agent.py`、`analysis_agent.py`等
   - ❌ 这些提示词没有统一管理

## 问题分析

### 1. 硬编码提示词分布

发现大量硬编码提示词在以下文件中：

- `agent-service/src/core/agents/mcp_tool_agent.py` (269-547行)
  - MCP工具智能体的提示词（包含Few-Shot示例）
  - **这是刚刚改进的邮件参数提取提示词**

- `agent-service/src/core/agents/content_agent.py` (232-263行)
  - 内容生成提示词

- `agent-service/src/core/agents/quality_check_agent.py` (173-219行)
  - 质量检查提示词

- `agent-service/src/core/agents/data_clean_agent.py` (167-204行)
  - 数据清洗提示词

- `agent-service/src/core/agents/analysis_agent.py` (168-206行)
  - 数据分析提示词

- `agent-service/src/core/agents/insight_agent.py` (161-193行)
  - 业务洞察提示词

### 2. 为什么没有统一管理？

1. **历史遗留**：很多Agent在提示词引擎实现之前就存在
2. **开发习惯**：直接在代码中写提示词更方便快速迭代
3. **缺少工具**：没有后台管理界面，修改YAML不够直观
4. **缺少迁移**：没有系统性地将硬编码提示词迁移到统一管理

## 建议方案

### 方案1：完善提示词管理系统（推荐）

#### 1.1 添加数据库存储

创建提示词表：
```sql
CREATE TABLE prompt_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    system_prompt TEXT,
    examples JSONB,
    temperature FLOAT DEFAULT 0.3,
    max_tokens INT DEFAULT 2000,
    version INT DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    metadata JSONB
);
```

#### 1.2 添加API接口

在 `agent-service/src/routes/` 下创建 `prompts.py`：

```python
@router.get("/prompts", response_model=List[PromptTemplateResponse])
async def list_prompts(
    category: Optional[str] = None,
    is_active: Optional[bool] = None
):
    """列出所有提示词模板"""

@router.get("/prompts/{prompt_id}", response_model=PromptTemplateResponse)
async def get_prompt(prompt_id: int):
    """获取单个提示词模板"""

@router.post("/prompts", response_model=PromptTemplateResponse)
async def create_prompt(prompt: PromptTemplateCreate):
    """创建新的提示词模板"""

@router.put("/prompts/{prompt_id}", response_model=PromptTemplateResponse)
async def update_prompt(prompt_id: int, prompt: PromptTemplateUpdate):
    """更新提示词模板"""

@router.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: int):
    """删除提示词模板（软删除）"""

@router.post("/prompts/{prompt_id}/test")
async def test_prompt(prompt_id: int, test_input: PromptTestRequest):
    """测试提示词效果"""
```

#### 1.3 添加后台管理界面

在 `web-ui/src/app/admin/` 下创建 `prompts/` 目录：

- `page.tsx` - 提示词列表页面
- `[id]/page.tsx` - 提示词编辑页面
- `create/page.tsx` - 创建提示词页面
- `test/page.tsx` - 提示词测试页面

功能：
- 列表展示所有提示词
- 编辑提示词（支持Markdown、代码高亮）
- 版本历史查看
- 测试提示词效果
- 批量导入/导出

#### 1.4 迁移硬编码提示词

逐步将硬编码提示词迁移到数据库：

1. **优先级1**：`mcp_tool_agent.py` 的提示词（刚刚改进的）
2. **优先级2**：常用Agent的提示词
3. **优先级3**：其他Agent的提示词

### 方案2：改进现有YAML管理（快速方案）

如果暂时不想做数据库存储，可以：

1. **改进YAML结构**：添加更多元数据
2. **添加管理工具**：创建命令行工具管理YAML
3. **添加验证**：确保YAML格式正确
4. **添加文档**：说明如何添加/修改提示词

## 实施建议

### 阶段1：基础功能（1-2周）

1. ✅ 创建数据库表
2. ✅ 实现API接口（CRUD）
3. ✅ 实现基础的后台管理界面
4. ✅ 迁移1-2个关键提示词到数据库

### 阶段2：完善功能（2-3周）

1. ✅ 添加版本控制
2. ✅ 添加测试功能
3. ✅ 添加导入/导出
4. ✅ 迁移更多提示词

### 阶段3：优化体验（1-2周）

1. ✅ 添加提示词模板库
2. ✅ 添加AI辅助优化
3. ✅ 添加使用统计
4. ✅ 添加A/B测试

## 当前需要立即处理的问题

### 问题1：`mcp_tool_agent.py` 的提示词

**现状**：刚刚改进的邮件参数提取提示词是硬编码的

**建议**：
1. 立即迁移到数据库或YAML
2. 在后台管理界面中可以编辑
3. 支持版本控制和回滚

### 问题2：缺少统一管理

**现状**：提示词分散在代码和YAML中

**建议**：
1. 统一迁移到数据库
2. 代码中只保留引用，不保留内容
3. 提供迁移工具

## 总结

**当前状态**：
- ✅ 有提示词引擎基础设施
- ❌ 没有后台管理界面
- ❌ 没有API管理接口
- ❌ 大量硬编码提示词未统一管理

**建议**：
1. **短期**：添加API和后台管理界面
2. **中期**：迁移硬编码提示词到数据库
3. **长期**：完善版本控制、测试、优化等功能

**优先级**：
1. 🔴 **高优先级**：`mcp_tool_agent.py` 的提示词（刚刚改进的）
2. 🟡 **中优先级**：常用Agent的提示词
3. 🟢 **低优先级**：其他Agent的提示词

