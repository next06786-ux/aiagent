# 1. 添加所有变更（包括删除的文件、修改的文件、新增的文件）
git add -A

# 2. 提交
git commit -m "优化"

# 3. 推送到 GitHub
git push origin main
# clone 仓库
 git pull origin main
git clone https://github.com/next06786-ux/aiagent.git aiagent

# 进入项目目录
cd aiagent
git config --global url."https://mirror.ghproxy.com/https://".insteadOf "https://"

git config --global --unset url."https://mirror.ghproxy.com/https://".insteadOf

git config --global --unset url."https://github.moeyy.xyz/https://".insteadOf "https://"