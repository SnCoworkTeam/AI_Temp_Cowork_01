# 工作流设计器

基于React Flow的拖拽式工作流设计器，支持可视化创建和编辑工作流。

## 功能特性

### 1. 节点面板 (NodePanel)

- 提供9种预定义节点类型：
  - **基础节点**: 开始、结束
  - **AI节点**: LLM节点
  - **工具节点**: 工具调用
  - **逻辑节点**: 条件判断
  - **数据处理**: 数据转换
  - **集成节点**: HTTP请求
  - **控制节点**: 延迟
  - **调试节点**: 日志

- 支持搜索和分类筛选
- 支持拖拽或点击添加节点

### 2. 属性面板 (PropertyPanel)

- 根据节点类型显示不同的配置选项
- LLM节点: 模型选择、温度、提示词模板
- 工具节点: 工具名称、参数配置
- 条件节点: 条件表达式、分支标签
- HTTP节点: URL、方法、请求头、请求体
- 支持JSON格式的高级配置编辑

### 3. 画布操作

- 拖拽节点
- 连接节点（拖拽创建连接线）
- 缩放和平移画布
- 小地图导航
- 节点选择和高亮

### 4. 节点组件

每个节点类型都有自定义的视觉组件：

- **LLMNode**: 蓝色主题，显示模型和提示词预览
- **ToolNode**: 紫色主题，显示工具名称
- **ConditionNode**: 黄色主题，支持真/假两个输出端口
- **TransformNode**: 靛蓝色主题，显示转换类型
- **HTTPNode**: 青色主题，显示HTTP方法和URL
- **StartNode**: 绿色圆形，表示工作流起点
- **EndNode**: 红色圆形，表示工作流终点

## 使用方法

### 访问设计器

```
/workflow-designer
/workflow-designer?id=<workflow_id>  // 编辑现有工作流
```

### 创建新工作流

1. 从节点面板拖拽或点击节点添加到画布
2. 点击节点之间的连接点创建连接
3. 选中节点后在属性面板配置节点属性
4. 在顶部输入工作流名称和描述
5. 点击"保存工作流"按钮

### 编辑工作流

1. 通过URL参数传入workflow_id
2. 工作流会自动加载到画布
3. 修改节点和连接
4. 保存更改

## 节点配置示例

### LLM节点

```json
{
  "model": "gpt-4",
  "temperature": 0.7,
  "prompt_template": "分析以下数据：{input_data}",
  "max_tokens": 2000
}
```

### 工具调用节点

```json
{
  "tool_name": "sap_query",
  "parameters": {
    "table": "MARA",
    "query": "${search_query}"
  },
  "mcp_gateway_url": "http://mcp-gateway:8001"
}
```

### 条件判断节点

```json
{
  "condition": "len(state.get('data', [])) > 0",
  "true_output": "has_data",
  "false_output": "no_data"
}
```

## 技术栈

- **React Flow**: 工作流可视化库
- **Next.js**: React框架
- **TypeScript**: 类型安全
- **TailwindCSS**: 样式框架

## 注意事项

1. 每个工作流必须有一个开始节点
2. 条件节点可以有多个输出端口
3. 节点配置支持状态变量引用（`${variable_name}`）
4. 保存时会自动验证工作流结构
5. 连接的节点必须有有效的输入/输出端口
