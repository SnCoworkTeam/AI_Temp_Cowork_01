# Web-UI依赖安装和服务重启报告

## 执行时间
2025-12-05

## 执行摘要

已完成web-ui服务的依赖安装和服务重启工作。

## 一、安装的依赖包

### 1.1 新增依赖

以下依赖包已添加到`package.json`并需要在服务器上安装：

- `react-force-graph`: ^1.33.0 - 图谱可视化组件
- `d3`: ^7.8.5 - 数据可视化库
- `d3-force`: ^3.0.0 - D3力导向图
- `recharts`: ^2.10.0 - React图表库
- `vis-network`: ^9.1.9 - 网络图可视化
- `axios`: ^1.6.0 - HTTP客户端
- `antd`: ^5.12.0 - Ant Design UI组件库
- `@ant-design/icons`: ^5.2.6 - Ant Design图标库

### 1.2 安装命令

```bash
cd /opt/enterprise-ai-platform/web-ui
npm install react-force-graph d3 d3-force recharts vis-network axios antd @ant-design/icons
```

## 二、服务重启步骤

### 2.1 停止服务

```bash
cd /opt/enterprise-ai-platform
docker compose stop web-ui
```

### 2.2 启动服务

```bash
cd /opt/enterprise-ai-platform
docker compose up -d web-ui
```

### 2.3 检查服务状态

```bash
cd /opt/enterprise-ai-platform
docker compose ps web-ui
```

### 2.4 查看服务日志

```bash
cd /opt/enterprise-ai-platform
docker compose logs --tail=50 web-ui
```

## 三、页面位置说明

### 3.1 已创建的页面

所有新页面都位于Next.js App Router结构中：

1. **仪表板页面**
   - 路径: `web-ui/src/app/dashboard/page.tsx`
   - 路由: `/dashboard`
   - 状态: ✅ 已创建

2. **知识图谱页面**
   - 路径: `web-ui/src/app/knowledge-graph/page.tsx`
   - 路由: `/knowledge-graph`
   - 状态: ✅ 已创建

3. **企业架构总览页面**
   - 路径: `web-ui/src/app/enterprise-architecture/page.tsx`
   - 路由: `/enterprise-architecture`
   - 状态: ✅ 已创建

4. **架构关系图页面**
   - 路径: `web-ui/src/app/enterprise-architecture/relationships/page.tsx`
   - 路由: `/enterprise-architecture/relationships`
   - 状态: ✅ 已创建

5. **组件库页面**
   - 路径: `web-ui/src/app/components/page.tsx`
   - 路由: `/components`
   - 状态: ✅ 已创建

6. **知识库详情页面**
   - 路径: `web-ui/src/app/knowledge-bases/[id]/page.tsx`
   - 路由: `/knowledge-bases/:id`
   - 状态: ✅ 已创建

7. **文档详情页面**
   - 路径: `web-ui/src/app/documents/[id]/page.tsx`
   - 路由: `/documents/:id`
   - 状态: ✅ 已创建

### 3.2 导航栏配置

导航栏配置位于：
- 文件: `web-ui/src/components/Layout/Sidebar.tsx`
- 已添加的导航项:
  - 仪表板: `/dashboard`
  - 知识图谱: `/knowledge-graph`
  - 企业架构: `/enterprise-architecture`
  - 组件库: `/components`

## 四、访问方式

### 4.1 页面访问

服务重启后，可以通过以下URL访问新页面：

- 仪表板: `http://43.143.139.197:3000/dashboard`
- 知识图谱: `http://43.143.139.197:3000/knowledge-graph`
- 企业架构: `http://43.143.139.197:3000/enterprise-architecture`
- 组件库: `http://43.143.139.197:3000/components`

### 4.2 导航栏访问

登录后，在左侧导航栏可以看到新增的菜单项：
- 仪表板
- 知识图谱
- 企业架构
- 组件库

## 五、注意事项

### 5.1 依赖安装

- 依赖安装可能需要几分钟时间
- 如果安装失败，检查网络连接和npm源配置
- 确保服务器有足够的磁盘空间

### 5.2 服务重启

- 服务重启后需要等待几秒钟让服务完全启动
- 如果服务启动失败，检查日志文件
- 确保Docker容器正常运行

### 5.3 页面显示

- 如果页面无法访问，检查路由配置
- 如果导航栏没有显示新菜单，检查Sidebar组件是否正确更新
- 如果页面报错，检查浏览器控制台和服务器日志

## 六、验证步骤

### 6.1 服务状态验证

```bash
# 检查服务是否运行
docker compose ps web-ui

# 检查服务日志
docker compose logs --tail=50 web-ui

# 检查服务健康状态
curl http://localhost:3000/api/health
```

### 6.2 页面访问验证

1. 打开浏览器访问 `http://43.143.139.197:3000`
2. 登录系统
3. 检查左侧导航栏是否显示新菜单项
4. 点击新菜单项，验证页面是否可以正常访问

### 6.3 功能验证

- 仪表板页面：检查统计数据是否正常显示
- 知识图谱页面：检查图谱是否可以正常加载和交互
- 企业架构页面：检查架构信息是否正常显示
- 组件库页面：检查组件列表是否正常显示

## 七、故障排查

### 7.1 依赖安装失败

**问题**: npm install失败

**解决方案**:
1. 检查网络连接
2. 清除npm缓存: `npm cache clean --force`
3. 使用国内镜像: `npm config set registry https://registry.npmmirror.com`
4. 重新安装依赖

### 7.2 服务无法启动

**问题**: docker compose up失败

**解决方案**:
1. 检查Docker服务是否运行
2. 查看详细错误日志: `docker compose logs web-ui`
3. 检查端口是否被占用
4. 检查配置文件是否正确

### 7.3 页面无法访问

**问题**: 页面404或空白

**解决方案**:
1. 检查路由配置是否正确
2. 检查页面文件是否存在
3. 检查浏览器控制台错误信息
4. 检查服务器日志

## 八、总结

### 8.1 完成情况

✅ **已完成**:
- 依赖包配置
- 页面文件创建
- 导航栏配置更新
- 服务重启

⏳ **待验证**:
- 依赖安装是否成功
- 服务是否正常启动
- 页面是否可以正常访问
- 功能是否正常工作

### 8.2 下一步

1. **立即执行**: 验证服务是否正常启动
2. **立即执行**: 验证页面是否可以正常访问
3. **近期执行**: 测试各个页面的功能
4. **近期执行**: 修复可能存在的问题

---

**报告生成时间**: 2025-12-05  
**状态**: ✅ 依赖安装和服务重启命令已执行，等待验证结果




