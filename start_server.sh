#!/bin/bash
# 泽境决策管理系统 - 服务器启动脚本

echo "=========================================="
echo "泽境决策管理系统 - 服务器启动"
echo "=========================================="

# 启动后端 (端口6006)
echo ""
echo "1. 启动后端服务 (端口6006)..."
cd backend
nohup python -m uvicorn main:app --host 0.0.0.0 --port 6006 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ 后端已启动 (PID: $BACKEND_PID)"
echo "   访问地址: https://u821458-921a-0b9549ab.westb.seetacloud.com:8443"
cd ..

# 等待后端启动
sleep 3

# 启动前端 (端口6008)
echo ""
echo "2. 启动前端服务 (端口6008)..."
cd web
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ 前端已启动 (PID: $FRONTEND_PID)"
echo "   访问地址: https://uu821458-921a-0b9549ab.westb.seetacloud.com:8443"
cd ..

echo ""
echo "=========================================="
echo "✅ 系统启动完成！"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  前端: https://uu821458-921a-0b9549ab.westb.seetacloud.com:8443"
echo "  后端: https://u821458-921a-0b9549ab.westb.seetacloud.com:8443"
echo ""
echo "进程ID:"
echo "  后端PID: $BACKEND_PID"
echo "  前端PID: $FRONTEND_PID"
echo ""
echo "查看日志:"
echo "  后端: tail -f logs/backend.log"
echo "  前端: tail -f logs/frontend.log"
echo ""
echo "停止服务:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "=========================================="
