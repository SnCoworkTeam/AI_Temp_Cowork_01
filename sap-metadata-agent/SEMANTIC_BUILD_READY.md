# SAP元数据语义分析构建 - 就绪

## ✅ 已完成的工作

### 1. 语义分析构建脚本 ✅

**文件**: `build_semantic_analysis.py`

**功能特性**:
- ✅ 分批处理数据资产和业务实体
- ✅ 断点续传支持（自动保存/恢复进度）
- ✅ 错误重试机制（最多3次）
- ✅ 详细的进度跟踪和统计
- ✅ 完整的错误处理和日志记录

### 2. 快速启动脚本 ✅

**PowerShell脚本**: `build_semantic.ps1`
- 自动检查Python环境
- 自动检查服务连接
- 友好的参数提示

**Bash脚本**: `build_semantic.sh`
- 适用于Linux/Mac系统
- 自动检查环境和服务

### 3. 使用文档 ✅

**文件**: `SEMANTIC_ANALYSIS_BUILD_GUIDE.md`
- 完整的使用说明
- 故障排除指南
- 性能优化建议

## 🚀 快速开始

### Windows (PowerShell)

```powershell
# 基本用法
.\build_semantic.ps1

# 指定批次大小
.\build_semantic.ps1 -BatchSize 100

# 从进度文件恢复
.\build_semantic.ps1 -Resume
```

### Linux/Mac (Bash)

```bash
# 基本用法
./build_semantic.sh

# 指定批次大小
./build_semantic.sh --batch-size 100

# 从进度文件恢复
./build_semantic.sh --resume
```

### Python直接调用

```bash
# 基本用法
python build_semantic_analysis.py

# 指定参数
python build_semantic_analysis.py --batch-size 100 --assets-offset 0

# 从进度文件恢复
python build_semantic_analysis.py --resume
```

## 📋 前置条件检查清单

在开始构建之前，请确认：

- [ ] **SAP元数据已构建**: 元数据服务中有SAP元数据
- [ ] **知识库服务运行**: `http://localhost:8004/api/health` 可访问
- [ ] **元数据服务运行**: `http://localhost:8005/health` 可访问
- [ ] **Python环境**: Python 3.8+ 已安装
- [ ] **依赖包**: 已安装所需依赖（见 `requirements.txt`）

## 🔍 验证元数据

在开始构建语义分析之前，可以验证元数据是否已构建：

```bash
# 检查SAP数据资产数量
curl "http://localhost:8005/api/data-assets?source_system=SAP&limit=1"

# 或使用Python脚本
python check_count.py
```

## 📊 构建过程

### 阶段1: 处理数据资产

- 从元数据服务获取SAP数据资产
- 分批处理（默认每批50个）
- 转换为语义文档
- 存储到知识库

### 阶段2: 处理业务实体

- 从元数据服务获取SAP业务实体
- 分批处理
- 转换为语义文档
- 存储到知识库

### 进度跟踪

构建过程中会自动保存进度到 `semantic_build_progress.json`:

```json
{
  "assets_offset": 5000,
  "entities_offset": 100,
  "total_indexed": 4800,
  "total_failed": 200,
  "last_update": "2024-01-15T10:30:00"
}
```

## ⚙️ 配置建议

### 批次大小选择

| 批次大小 | 适用场景 | 内存占用 | 处理速度 |
|---------|---------|---------|---------|
| 10-30   | 资源受限环境 | 低 | 慢 |
| 50-100  | 推荐配置 | 中 | 中 |
| 200+    | 高性能环境 | 高 | 快 |

### 环境变量

```bash
# 元数据服务URL
export METADATA_SERVICE_URL=http://localhost:8005

# 知识库服务URL
export KNOWLEDGE_BASE_URL=http://localhost:8004

# 批次大小（可选）
export SEMANTIC_BATCH_SIZE=50
```

## 📈 预期结果

构建完成后，你应该看到：

1. **知识库中的文档**: 所有SAP元数据已转换为可搜索的语义文档
2. **统计信息**: 成功索引数量、失败数量、成功率
3. **进度文件清理**: 构建成功后自动清理进度文件

## 🔄 断点续传

如果构建过程中断：

1. **自动保存**: 进度会自动保存到 `semantic_build_progress.json`
2. **继续构建**: 使用 `--resume` 参数继续
3. **跳过已处理**: 自动从上次位置继续

```bash
# 继续构建
python build_semantic_analysis.py --resume
```

## 🐛 常见问题

### Q: 构建速度很慢？

A: 可以尝试：
- 增加批次大小: `--batch-size 100`
- 检查网络延迟
- 检查知识库服务性能

### Q: 部分文档索引失败？

A: 可以：
- 查看错误日志
- 使用 `--resume` 继续构建（会自动重试）
- 检查知识库服务状态

### Q: 内存不足？

A: 可以：
- 减小批次大小: `--batch-size 20`
- 增加批次间延迟（修改脚本中的 `BATCH_DELAY`）

## 📚 相关文档

- [语义分析构建指南](./SEMANTIC_ANALYSIS_BUILD_GUIDE.md) - 详细使用说明
- [SAP元数据构建指南](./BUILD_GUIDE.md) - 元数据构建说明
- [知识库服务文档](../knowledge-base/README.md) - 知识库服务说明

## 🎯 下一步

构建完成后，可以：

1. **验证索引**: 使用语义搜索测试
2. **监控使用**: 监控搜索使用情况
3. **优化索引**: 根据结果调整文档内容
4. **定期更新**: 元数据更新时重新构建

---

**准备就绪！** 🚀

现在可以开始构建语义分析索引了。建议先使用默认参数测试，确认一切正常后再进行完整构建。

