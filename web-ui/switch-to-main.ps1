# 切换到main分支并拉取所有文件
$env:GIT_PAGER = ""
git fetch origin main
git checkout main
git pull origin main

