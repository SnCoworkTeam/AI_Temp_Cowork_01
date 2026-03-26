# AI辅助CI/CD测试快速启动指南

**目标**: 10分钟内启动第一次测试-修复循环
**日期**: 2025-12-04

---

## 🚀 快速启动(3步)

### 步骤1: 检查环境 (2分钟)

```bash
# 检查GitHub CLI
gh --version
# 如果未安装: winget install --id GitHub.cli

# 检查Python
python --version  # 需要3.11+

# 检查Node.js
node --version    # 需要18+

# 确保已登录GitHub
gh auth status
```

### 步骤2: 启动测试器 (1分钟)

```bash
# 进入项目目录
cd e:\enterprise-ai-platform

# 启动AI辅助测试器(按层级测试)
python scripts/cicd/ai_assisted_tester.py --mode layer

# 或者测试单个服务
python scripts/cicd/ai_assisted_tester.py --mode service
```

### 步骤3: 协作修复 (5-10分钟)

当脚本提示"需要Claude Code协助修复"时:

1. **打开错误报告**
   - 脚本会生成: `claude_report_iter_1_*.md`
   - 在VSCode中打开这个文件

2. **在Claude Code中运行以下提示**:

```
请帮我修复这个错误报告中的所有错误。

错误报告文件: [复制上面的文件路径]

请按以下步骤操作:
1. 阅读错误报告,理解所有错误
2. 优先处理标记为'🔧 可修复'的错误
3. 对每个错误:
   - 使用Read工具读取相关文件
   - 分析错误的根本原因
   - 使用Edit工具进行修复
   - 确保修复不引入新问题
4. 修复完成后,运行验证命令:
   cd web-ui && npx tsc --noEmit
5. 如果验证通过,提交代码:
   git add -A
   git commit -m "fix: AI-assisted fixes for CI/CD"
   git push origin main
```

3. **等待Claude Code完成**
   - Claude Code会自动读取文件、分析错误、执行修复
   - 验证修复结果
   - 提交代码

4. **返回脚本终端**
   - 按Enter继续
   - 脚本会启动新一轮测试

---

## 📋 工作流程图

```
Python脚本                          Claude Code (您)
    │
    ├─ 启动GitHub Actions
    │
    ├─ 等待测试完成
    │
    ├─ 下载日志
    │
    ├─ 分析错误
    │
    ├─ 生成错误报告
    │   └─ claude_report_*.md
    │
    ├─ ⏸️  暂停,等待修复
    │                                   │
    └────────────────────────────────→ ├─ 打开错误报告
                                        │
                                        ├─ 阅读错误信息
                                        │
                                        ├─ 读取相关代码文件
                                        │
                                        ├─ 分析错误原因
                                        │
                                        ├─ 执行代码修复
                                        │
                                        ├─ 运行验证命令
                                        │
                                        ├─ 提交代码
                                        │
    ←────────────────────────────────┘
    │
    ├─ 继续下一轮测试
    │
    └─ 循环...
```

---

## 🎯 第一次测试建议

### 推荐从web-ui开始

原因:
- TypeScript错误多
- Claude Code修复效果好
- 快速看到效果

```bash
# 只测试web-ui
python scripts/cicd/ai_assisted_tester.py --mode service

# 然后在提示时选择web-ui服务
```

---

## 💡 Claude Code提示词模板

### 模板1: 批量修复(推荐)

```
我需要你帮我修复CI/CD测试中发现的错误。

错误报告: [文件路径]

请逐个处理所有错误:
1. 先处理'🔧 可修复'的错误
2. 对每个错误:
   - 读取相关文件
   - 理解错误上下文
   - 执行修复
3. 修复后立即验证:
   cd web-ui && npx tsc --noEmit
4. 全部修复完成后提交代码
```

### 模板2: 单个错误修复

```
请帮我修复这个错误:

文件: [文件路径]
行号: [行号]
错误: [错误消息]

步骤:
1. 读取文件内容
2. 理解错误原因
3. 提供修复方案
4. 执行修复
5. 验证
```

### 模板3: 复杂错误分析

```
这个错误比较复杂,请帮我深入分析:

[粘贴错误详情]

请:
1. 读取相关的多个文件
2. 分析错误的根本原因
3. 考虑可能的副作用
4. 提供详细的修复方案
5. 解释为什么这样修复
```

---

## ⚙️ 高级选项

### 禁用AI辅助

如果想要完全自动化(不等待人工):

```bash
python scripts/cicd/ai_assisted_tester.py --mode layer --no-ai-assist
```

### 测试特定服务

```bash
# 修改脚本,指定服务列表
# 或手动调用test_service()方法
```

### 自定义迭代次数

编辑脚本:
```python
self.max_iterations_per_service = 5  # 默认5次
```

---

## 📊 预期结果

### 第一次运行

- **时间**: 20-30分钟
- **结果**:
  - 发现10-20个错误
  - 修复5-15个错误
  - 可能需要2-3次迭代

### 持续运行(1周后)

- **时间**: 每次15-20分钟
- **结果**:
  - 错误数量减少
  - 修复成功率提高
  - 覆盖率提升5-10%

---

## ⚠️ 常见问题

### Q1: GitHub Actions配额不够?

**A**:
- 使用GitHub Free: 每月2000分钟
- 每次测试约15-20分钟
- 每天最多运行3-5次
- 考虑使用self-hosted runner

### Q2: Claude Code修复失败?

**A**:
- 检查错误报告是否完整
- 尝试单个错误修复
- 查看Claude Code的输出
- 手动介入复杂错误

### Q3: 测试一直失败?

**A**:
- 检查是否有环境问题
- 查看详细的日志
- 隔离问题服务
- 寻求人工帮助

### Q4: 如何暂停测试?

**A**:
- Ctrl+C 中断Python脚本
- 进度会自动保存
- 下次运行会从上次位置继续

---

## 📚 更多资源

- **详细文档**: [AI_ASSISTED_CICD_LOOP_PLAN.md](AI_ASSISTED_CICD_LOOP_PLAN.md)
- **系统性测试计划**: [docs/SYSTEMATIC_TESTING_PLAN.md](docs/SYSTEMATIC_TESTING_PLAN.md)
- **脚本源码**: [scripts/cicd/ai_assisted_tester.py](scripts/cicd/ai_assisted_tester.py)

---

## ✅ 检查清单

启动前确认:

- [ ] GitHub CLI已安装并登录
- [ ] Python 3.11+ 已安装
- [ ] Node.js 18+ 已安装
- [ ] 在项目根目录
- [ ] 有足够的GitHub Actions配额
- [ ] 已阅读本指南

开始测试:

- [ ] 运行测试脚本
- [ ] 等待错误报告生成
- [ ] 在Claude Code中打开报告
- [ ] 运行修复提示词
- [ ] 验证修复结果
- [ ] 提交代码
- [ ] 返回脚本继续

---

## 🎉 开始吧!

```bash
python scripts/cicd/ai_assisted_tester.py --mode layer
```

Good luck! 🚀
