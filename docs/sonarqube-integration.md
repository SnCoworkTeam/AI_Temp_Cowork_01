# SonarQube 集成指南

## 概述

SonarQube 已部署在服务器 `124.220.181.231:9000`，为所有服务提供统一的代码质量视图、历史趋势和技术债务管理。

## 访问信息

- **访问地址**: http://124.220.181.231:9000
- **默认用户名**: admin
- **默认密码**: admin (首次登录后必须修改)

## 项目配置

### 1. 在SonarQube中创建项目

1. 登录SonarQube
2. 点击 "Create Project" -> "Manually"
3. 填写项目信息：
   - **Project Key**: `enterprise-ai-platform`
   - **Display Name**: `Enterprise AI Platform`
4. 生成Token：
   - 点击 "Generate a token"
   - 保存Token（只显示一次）

### 2. 配置SonarQube Scanner

#### 方式一：使用Docker（推荐）

在项目根目录创建 `sonar-project.properties`:

```properties
sonar.projectKey=enterprise-ai-platform
sonar.projectName=Enterprise AI Platform
sonar.projectVersion=1.0

# 源代码路径
sonar.sources=.
sonar.sourceEncoding=UTF-8

# 排除文件
sonar.exclusions=**/node_modules/**,**/dist/**,**/build/**,**/__pycache__/**,**/*.pyc,**/venv/**,**/env/**,**/.git/**,**/htmlcov/**,**/mypy-report/**,**/coverage/**,**/logs/**,**/backups/**,**/*.log

# 测试路径
sonar.tests=.
sonar.test.inclusions=**/test_*.py,**/tests/**,**/*_test.py

# Python配置
sonar.python.version=3.10,3.11

# 代码覆盖率报告路径
sonar.python.coverage.reportPaths=coverage.json,htmlcov/coverage.xml

# SonarQube服务器
sonar.host.url=http://124.220.181.231:9000
sonar.login=YOUR_SONAR_TOKEN
```

#### 方式二：本地安装SonarQube Scanner

```bash
# 下载SonarQube Scanner
wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip
unzip sonar-scanner-cli-5.0.1.3006-linux.zip
sudo mv sonar-scanner-5.0.1.3006-linux /opt/sonar-scanner
export PATH=$PATH:/opt/sonar-scanner/bin
```

### 3. 运行代码分析

#### 使用Docker运行分析

```bash
# 在项目根目录执行
docker run --rm \
  -v $(pwd):/usr/src \
  -w /usr/src \
  sonarsource/sonar-scanner-cli:latest \
  -Dsonar.projectKey=enterprise-ai-platform \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://124.220.181.231:9000 \
  -Dsonar.login=YOUR_SONAR_TOKEN \
  -Dsonar.exclusions=**/node_modules/**,**/dist/**,**/build/**,**/__pycache__/**
```

#### 使用本地Scanner

```bash
sonar-scanner
```

### 4. CI/CD集成

#### GitHub Actions集成

在 `.github/workflows/sonarqube.yml` 中添加：

```yaml
name: SonarQube Analysis

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  sonarqube:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0  # 完整历史记录用于增量分析

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests with coverage
        run: |
          pytest --cov=. --cov-report=xml --cov-report=json

      - name: SonarQube Scan
        uses: sonarsource/sonarqube-scan-action@master
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
          SONAR_HOST_URL: http://124.220.181.231:9000
```

在GitHub仓库设置中添加Secret：
- `SONAR_TOKEN`: SonarQube生成的Token

#### Jenkins集成

在Jenkins Pipeline中添加：

```groovy
stage('SonarQube Analysis') {
    steps {
        script {
            def scannerHome = tool 'SonarQube Scanner'
            withSonarQubeEnv('SonarQube') {
                sh "${scannerHome}/bin/sonar-scanner \
                    -Dsonar.projectKey=enterprise-ai-platform \
                    -Dsonar.sources=. \
                    -Dsonar.host.url=http://124.220.181.231:9000"
            }
        }
    }
}
```

### 5. 质量门禁配置

在SonarQube中配置质量门禁：

1. 进入 **Quality Gates** -> **Create**
2. 设置质量门禁规则：
   - **代码覆盖率**: >= 80%
   - **重复代码**: < 3%
   - **技术债务**: < 5%
   - **安全漏洞**: 0
   - **严重问题**: 0
   - **阻断问题**: 0

3. 设置为默认质量门禁

### 6. 多服务分析配置

为每个服务创建单独的项目：

#### API Gateway
```properties
sonar.projectKey=api-gateway
sonar.projectName=API Gateway
sonar.sources=api-gateway
```

#### Auth Service
```properties
sonar.projectKey=auth-service
sonar.projectName=Auth Service
sonar.sources=auth-service
```

#### Project Management
```properties
sonar.projectKey=project-management
sonar.projectName=Project Management
sonar.sources=project-management
```

### 7. 技术债务管理

SonarQube自动跟踪技术债务：

1. 查看技术债务报告：
   - 进入项目 -> **Measures** -> **Technical Debt**

2. 设置技术债务规则：
   - **Code Smells**: 每个问题对应一定技术债务时间
   - **Bugs**: 每个问题对应一定技术债务时间
   - **Vulnerabilities**: 每个问题对应一定技术债务时间

3. 技术债务趋势：
   - 查看历史趋势图表
   - 设置技术债务预算

### 8. 历史趋势分析

SonarQube自动记录每次分析的历史数据：

1. **代码覆盖率趋势**: 查看覆盖率变化
2. **问题趋势**: 查看问题数量变化
3. **技术债务趋势**: 查看技术债务变化
4. **代码行数趋势**: 查看代码增长情况

### 9. 报告和仪表板

#### 项目仪表板
- 访问项目主页查看概览
- 自定义仪表板组件

#### 质量报告
- 导出PDF报告
- 导出Excel报告
- API获取报告数据

### 10. 维护和监控

#### 服务状态检查
```bash
# 检查服务状态
sudo systemctl status sonarqube

# 查看日志
sudo journalctl -u sonarqube -f

# 检查数据库连接
sudo -u postgres psql -d sonarqube -c "SELECT COUNT(*) FROM projects;"
```

#### 备份
```bash
# 备份数据库
sudo -u postgres pg_dump sonarqube > sonarqube_backup_$(date +%Y%m%d).sql

# 备份配置和数据
tar -czf sonarqube_backup_$(date +%Y%m%d).tar.gz /opt/sonarqube/conf /opt/sonarqube/data
```

#### 更新
```bash
# 停止服务
sudo systemctl stop sonarqube

# 备份当前版本
cp -r /opt/sonarqube /opt/sonarqube.backup

# 下载新版本并解压
# 更新配置文件
# 启动服务
sudo systemctl start sonarqube
```

## 最佳实践

1. **定期分析**: 每次代码提交后自动运行分析
2. **质量门禁**: 配置质量门禁，阻止低质量代码合并
3. **技术债务管理**: 定期审查和修复技术债务
4. **团队协作**: 分配问题给团队成员，跟踪修复进度
5. **持续改进**: 根据分析结果持续改进代码质量

## 故障排查

### 服务无法启动
```bash
# 检查日志
sudo journalctl -u sonarqube -n 100

# 检查Java版本
java -version

# 检查数据库连接
sudo -u postgres psql -d sonarqube -c "\conninfo"
```

### 分析失败
- 检查网络连接
- 验证Token是否正确
- 检查项目配置是否正确
- 查看SonarQube日志

### 性能问题
- 增加Java堆内存
- 优化数据库配置
- 清理旧的分析数据

## 相关资源

- [SonarQube官方文档](https://docs.sonarqube.org/)
- [SonarQube Python插件](https://docs.sonarqube.org/latest/analysis/languages/python/)
- [质量门禁配置](https://docs.sonarqube.org/latest/user-guide/quality-gates/)

