#!/bin/bash
# Jenkins部署配置脚本

echo "=== 配置SSH密钥 ==="
# 创建.ssh目录
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 如果已有部署密钥，复制到Jenkins用户
if [ -f /home/ubuntu/.ssh/deploy_key ]; then
    sudo cp /home/ubuntu/.ssh/deploy_key /var/lib/jenkins/.ssh/deploy_key
    sudo chown jenkins:jenkins /var/lib/jenkins/.ssh/deploy_key
    sudo chmod 600 /var/lib/jenkins/.ssh/deploy_key
    echo "✅ 部署密钥已配置"
fi

echo "=== 安装Jenkins插件 ==="
echo "需要在Jenkins Web界面安装以下插件:"
echo "  - SSH Pipeline Steps"
echo "  - SSH Agent Plugin"
echo "  - Git Plugin"
echo "  - Docker Pipeline Plugin"

echo ""
echo "=== 创建部署Pipeline脚本 ==="
cat > /tmp/jenkins-deploy-pipeline.groovy <<'DEPLOYEOF'
pipeline {
    agent any
    
    environment {
        DEPLOY_SERVER = '43.143.139.197'
        DEPLOY_USER = 'ubuntu'
        DEPLOY_KEY = credentials('deploy-ssh-key')
        PROJECT_DIR = '/opt/enterprise-ai-platform'
    }
    
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/PMLiuyubin/enterprise-ai-platform.git'
            }
        }
        
        stage('Deploy') {
            steps {
                script {
                    sshagent([DEPLOY_KEY]) {
                        sh '''
                            ssh -o StrictHostKeyChecking=no \@\ << 'ENDSSH'
                                cd \
                                git pull origin main
                                docker compose down
                                docker compose build --parallel
                                docker compose up -d
                                docker compose ps
                            ENDSSH
                        '''
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo '部署成功！'
        }
        failure {
            echo '部署失败！'
        }
    }
}
DEPLOYEOF

echo "✅ Pipeline脚本已创建: /tmp/jenkins-deploy-pipeline.groovy"
echo ""
echo "=== 配置步骤 ==="
echo "1. 在Jenkins中添加SSH凭据（deploy-ssh-key）"
echo "2. 创建新的Pipeline任务"
echo "3. 将/tmp/jenkins-deploy-pipeline.groovy的内容复制到Pipeline脚本中"
echo "4. 保存并运行"