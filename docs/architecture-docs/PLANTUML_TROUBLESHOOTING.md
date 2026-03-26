# PlantUML 问题排查指南

## 常见错误：Request header is too large

### 问题描述

在使用在线PlantUML服务器（如 plantuml.com）时，可能会遇到以下错误：

```
java.lang.IllegalArgumentException: Request header is too large
```

### 原因分析

1. **PlantUML文件过大**：文件内容太多，超过了HTTP请求头大小限制
2. **在线服务器限制**：在线PlantUML服务器对请求大小有限制（通常8KB左右）
3. **URL编码问题**：通过URL参数传递时，编码后的内容更大

### 解决方案

#### 方案1：使用本地PlantUML工具（推荐）

**安装PlantUML：**

```bash
# Windows (使用Chocolatey)
choco install plantuml

# macOS (使用Homebrew)
brew install plantuml

# Linux
sudo apt-get install plantuml

# 或使用Docker
docker run --rm -v "$PWD:/work" plantuml/plantuml:latest *.puml
```

**生成图片：**

```bash
# 生成单个文件
plantuml docs/architecture-docs/system-architecture-detailed.puml

# 生成所有文件到指定目录
plantuml docs/architecture-docs/*.puml -o docs/images/architecture/

# 生成SVG格式（推荐，矢量图）
plantuml -tsvg docs/architecture-docs/*.puml -o docs/images/architecture/
```

#### 方案2：简化PlantUML文件

如果必须使用在线工具，可以：

1. **减少内部组件细节**：移除组件内部的子组件定义
2. **简化注释**：减少note注释的内容
3. **拆分大文件**：将大文件拆分成多个小文件
4. **移除不必要的样式**：简化skinparam配置

**示例优化：**

```plantuml
' 优化前（复杂）
component [Agent Service\n智能体核心服务\nPort: 8010] as AgentService {
    component [意图识别] as IntentRecognition
    component [任务分类] as TaskClassifier
    component [执行引擎] as ExecutionEngine
    component [流式处理] as StreamingProcessor
}

' 优化后（简化）
component [Agent Service\nPort: 8010] as AgentService
```

#### 方案3：使用文件上传方式

某些PlantUML在线工具支持文件上传，而不是通过URL参数传递：

1. 访问支持文件上传的PlantUML工具
2. 上传`.puml`文件
3. 生成图片

#### 方案4：使用VS Code插件

1. 安装PlantUML插件（如"PlantUML"）
2. 打开`.puml`文件
3. 使用快捷键预览（通常是`Alt+D`）
4. 导出为图片

**VS Code插件推荐：**
- PlantUML (by jebbs)
- Markdown Preview Mermaid Support

#### 方案5：使用PlantUML服务器

搭建本地PlantUML服务器：

```bash
# 使用Docker运行PlantUML服务器
docker run -d -p 8080:8080 plantuml/plantuml-server:jetty

# 访问 http://localhost:8080
```

### 文件大小建议

- **小型图表**（< 5KB）：可以使用在线工具
- **中型图表**（5-15KB）：建议使用本地工具或VS Code插件
- **大型图表**（> 15KB）：必须使用本地工具

### 优化技巧

1. **使用别名**：减少重复的长名称
   ```plantuml
   component [Agent Service\nPort: 8010] as AS
   ```

2. **简化连接线标签**：使用简短标签
   ```plantuml
   AS --> KB : 检索
   ' 而不是
   AS --> KB : 知识检索和语义搜索
   ```

3. **移除不必要的样式**：只保留必要的样式配置

4. **拆分大图**：将复杂架构图拆分成多个子图

### 检查文件大小

```bash
# Windows PowerShell
Get-Content docs/architecture-docs/system-architecture-detailed.puml | Measure-Object -Character

# Linux/Mac
wc -c docs/architecture-docs/system-architecture-detailed.puml
```

### 推荐工作流程

1. **开发阶段**：使用VS Code插件实时预览
2. **文档生成**：使用本地PlantUML工具批量生成
3. **CI/CD**：在构建流程中集成PlantUML生成

### 相关资源

- [PlantUML官方文档](https://plantuml.com/)
- [PlantUML在线服务器](http://www.plantuml.com/plantuml/uml/)
- [PlantUML GitHub](https://github.com/plantuml/plantuml)




