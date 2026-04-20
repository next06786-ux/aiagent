#!/bin/bash
# 更新代码并重启后端服务

echo "=========================================="
echo "更新代码并重启后端"
echo "=========================================="

cd /opt/aiagent/

echo "1. 拉取最新代码..."
git pull origin main

echo ""
echo "2. 重启后端服务..."
docker compose restart backend

echo ""
echo "3. 等待服务启动..."
sleep 5

echo ""
echo "4. 查看后端日志（最后30行）..."
docker logs --tail 30 lifeswarm-backend

echo ""
echo "=========================================="
echo "✅ 完成！"
echo "=========================================="
echo ""
echo "提示：在前端访问职业规划视图，然后运行以下命令查看调试日志："
echo "docker logs -f lifeswarm-backend | grep '_build_company_layer'"
