#!/bin/bash
# LifeSwarm 一键部署脚本 - 服务器 152.136.13.236

set -e

echo "🚀 开始部署 LifeSwarm..."

# 1. 安装 Docker
echo "📦 安装 Docker..."
curl -fsSL https://get.docker.com | bash
systemctl start docker
systemctl enable docker

# 2. 安装 Docker Compose
echo "📦 安装 Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 3. 配置环境变量
echo "⚙️  配置环境变量..."
if [ ! -f .env ]; then
    cp .env.production .env
    echo "❗ 请编辑 .env 文件，填写以下配置："
    echo "   - MYSQL_PASSWORD"
    echo "   - MYSQL_ROOT_PASSWORD"
    echo "   - NEO4J_PASSWORD"
    echo "   - QWEN_API_KEY"
    echo ""
    read -p "按回车继续编辑 .env 文件..." 
    nano .env
fi

# 4. 构建并启动服务
echo "🐳 构建并启动 Docker 容器..."
docker-compose up -d --build

# 5. 等待数据库启动
echo "⏳ 等待数据库启动..."
sleep 30

# 6. 初始化数据库
echo "💾 初始化数据库..."
docker-compose exec -T backend python backend/database/init_db.py
docker-compose exec -T backend python backend/database/init_neo4j.py

# 7. 检查服务状态
echo "✅ 检查服务状态..."
docker-compose ps

# 8. 测试健康检查
echo "🔍 测试后端健康检查..."
sleep 10
curl http://localhost:8000/health

echo ""
echo "🎉 部署完成！"
echo "📱 前端访问: http://152.136.13.236"
echo "🔧 后端API: http://152.136.13.236:8000"
echo ""
echo "📊 查看日志: docker-compose logs -f"
echo "🔄 重启服务: docker-compose restart"
echo "🛑 停止服务: docker-compose stop"
