pipeline {
    agent any
    
    environment {
        // 应用服务器
        APP_SERVER = '43.143.139.197'
        APP_USER = 'ubuntu'
        APP_DIR = '/opt/enterprise-ai-platform'
        
        // 图数据库服务器
        GRAPH_SERVER = '43.143.90.179'
        GRAPH_USER = 'ubuntu'
        GRAPH_DIR = '/opt/enterprise-ai-platform'
        
        // SSH密钥凭据ID（需要在Jenkins中配置）
        DEPLOY_KEY = credentials('deploy-ssh-key')
    }
    
    triggers {
        // 每5分钟检查一次代码变更
        pollSCM('H/5 * * * *')
        // 也可以手动触发
        // 建议配置GitHub Webhook实现实时自动部署
    }
    
    options {
        // 即使没有变更也允许手动触发构建
        skipDefaultCheckout(false)
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '📥 检出代码...'
                git branch: 'main', 
                    url: 'https://github.com/PMLiuyubin/enterprise-ai-platform.git',
                    credentialsId: 'github-credentials'  // 使用GitHub凭据（需要在Jenkins中配置）
            }
        }
        
        stage('Deploy to App Server') {
            steps {
                script {
                    echo '🚀 部署到应用服务器...'
                    sshagent([DEPLOY_KEY]) {
                        sh '''
                            ssh -o StrictHostKeyChecking=no ${APP_USER}@${APP_SERVER} << 'ENDSSH'
                                set -e
                                cd ${APP_DIR}
                                echo "当前目录: $(pwd)"
                                echo "当前Git提交: $(git rev-parse --short HEAD)"
                                echo ""
                                echo "📥 拉取最新代码..."
                                git fetch origin main
                                git reset --hard origin/main
                                echo "✅ 代码已更新"
                                echo ""
                                echo "🛑 停止旧服务..."
                                docker compose down --timeout 30 || true
                                echo "✅ 旧服务已停止"
                                echo ""
                                echo "🔨 构建新镜像..."
                                docker compose build --parallel
                                echo "✅ 镜像构建完成"
                                echo ""
                                echo "🚀 启动服务..."
                                docker compose up -d
                                echo "✅ 服务已启动"
                                echo ""
                                echo "⏳ 等待服务就绪..."
                                sleep 30
                                echo ""
                                echo "📊 服务状态:"
                                docker compose ps
                                echo ""
                            ENDSSH
                        '''
                    }
                }
            }
        }
        
        stage('Deploy to Graph Server') {
            when {
                // 如果配置了图数据库服务器密钥，则部署
                expression { 
                    return env.GRAPH_DEPLOY_KEY != null && env.GRAPH_DEPLOY_KEY != '' 
                }
            }
            steps {
                script {
                    echo '🚀 部署到图数据库服务器...'
                    sshagent([env.GRAPH_DEPLOY_KEY]) {
                        sh '''
                            ssh -o StrictHostKeyChecking=no ${GRAPH_USER}@${GRAPH_SERVER} << 'ENDSSH'
                                set -e
                                cd ${GRAPH_DIR}
                                echo "当前目录: $(pwd)"
                                echo "当前Git提交: $(git rev-parse --short HEAD)"
                                echo ""
                                echo "📥 拉取最新代码..."
                                git fetch origin main
                                git reset --hard origin/main
                                echo "✅ 代码已更新"
                                echo ""
                                echo "🛑 停止旧服务..."
                                docker compose down --timeout 30 || true
                                echo "✅ 旧服务已停止"
                                echo ""
                                echo "🔨 构建新镜像..."
                                docker compose build --parallel
                                echo "✅ 镜像构建完成"
                                echo ""
                                echo "🚀 启动服务..."
                                docker compose up -d
                                echo "✅ 服务已启动"
                                echo ""
                                echo "⏳ 等待服务就绪..."
                                sleep 30
                                echo ""
                                echo "📊 服务状态:"
                                docker compose ps
                                echo ""
                            ENDSSH
                        '''
                    }
                }
            }
        }
        
        stage('Health Check') {
            parallel {
                stage('App Server Health Check') {
                    steps {
                        script {
                            echo '🏥 检查应用服务器健康状态...'
                            sh '''
                                MAX_RETRIES=10
                                RETRY_COUNT=0
                                HEALTH_CHECK_PASSED=false
                                
                                while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
                                    if curl -f -s http://${APP_SERVER}:8080/health > /dev/null 2>&1; then
                                        echo "✅ 应用服务器健康检查通过"
                                        HEALTH_CHECK_PASSED=true
                                        break
                                    fi
                                    RETRY_COUNT=$((RETRY_COUNT + 1))
                                    echo "   等待中... ($RETRY_COUNT/$MAX_RETRIES)"
                                    sleep 5
                                done
                                
                                if [ "$HEALTH_CHECK_PASSED" != "true" ]; then
                                    echo "❌ 应用服务器健康检查失败"
                                    exit 1
                                fi
                            '''
                        }
                    }
                }
                stage('Graph Server Health Check') {
                    when {
                        expression { 
                            return env.GRAPH_DEPLOY_KEY != null && env.GRAPH_DEPLOY_KEY != '' 
                        }
                    }
                    steps {
                        script {
                            echo '🏥 检查图数据库服务器健康状态...'
                            sh '''
                                MAX_RETRIES=10
                                RETRY_COUNT=0
                                HEALTH_CHECK_PASSED=false
                                
                                while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
                                    if curl -f -s http://${GRAPH_SERVER}:8080/health > /dev/null 2>&1; then
                                        echo "✅ 图数据库服务器健康检查通过"
                                        HEALTH_CHECK_PASSED=true
                                        break
                                    fi
                                    RETRY_COUNT=$((RETRY_COUNT + 1))
                                    echo "   等待中... ($RETRY_COUNT/$MAX_RETRIES)"
                                    sleep 5
                                done
                                
                                if [ "$HEALTH_CHECK_PASSED" != "true" ]; then
                                    echo "⚠️  图数据库服务器健康检查失败（可能服务未运行或端口不同）"
                                    # 不退出，因为图数据库服务器可能使用不同的端口
                                fi
                            '''
                        }
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo '✅ 部署成功！'
            echo "应用服务器: http://${APP_SERVER}:8080"
            echo "图数据库服务器: http://${GRAPH_SERVER}:8080"
        }
        failure {
            echo '❌ 部署失败！'
            echo '请检查构建日志和服务器日志'
        }
        always {
            echo '🧹 清理工作空间...'
            cleanWs()
        }
    }
}
