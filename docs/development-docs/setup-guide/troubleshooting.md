# 故障排查指南

## 常见问题

### 1. 数据库连接失败

**症状**: 服务启动时提示数据库连接失败

**解决方案**:
- 检查PostgreSQL是否运行: `docker-compose ps`
- 检查环境变量配置
- 检查数据库端口是否被占用
- 查看数据库日志: `docker-compose logs postgres`

### 2. 端口冲突

**症状**: 服务启动失败，提示端口被占用

**解决方案**:
- 检查端口占用: `netstat -an | grep <port>`
- 修改`.env`文件中的端口配置
- 停止占用端口的其他服务

### 3. 依赖安装失败

**症状**: `pip install` 失败

**解决方案**:
- 使用国内镜像源: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple`
- 升级pip: `pip install --upgrade pip`
- 检查Python版本: `python --version`

### 4. 前端构建失败

**症状**: `npm run build` 失败

**解决方案**:
- 清除缓存: `npm cache clean --force`
- 删除node_modules重新安装
- 检查Node.js版本: `node --version`

### 5. 服务无法启动

**症状**: Docker容器启动后立即退出

**解决方案**:
- 查看容器日志: `docker-compose logs <service-name>`
- 检查环境变量配置
- 检查服务依赖是否启动
- 验证代码是否有语法错误

## 获取帮助

如果问题仍然存在：
1. 查看服务日志
2. 检查GitHub Issues
3. 联系开发团队









