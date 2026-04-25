#!/bin/bash
# 测试AutoDL端口映射是否正确配置

echo "=========================================="
echo "测试AutoDL端口映射"
echo "=========================================="
echo ""
echo "外部地址: https://u821458-b49a-bdca5515.westc.seetacloud.com:8443"
echo "容器端口: 6006"
echo ""

# 测试健康检查
echo "测试 /health 端点..."
response=$(curl -k -s -w "\n%{http_code}" https://u821458-b49a-bdca5515.westc.seetacloud.com:8443/health 2>&1)
status_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | head -n -1)

echo "HTTP状态码: $status_code"
echo "响应内容: $body"
echo ""

if [ "$status_code" = "200" ]; then
    echo "✅ 端口映射配置正确！"
    echo ""
    echo "下一步："
    echo "1. 重启后端容器: docker compose restart backend"
    echo "2. 在前端界面切换到'本地量化模型'"
elif [ "$status_code" = "404" ]; then
    echo "❌ 端口映射配置错误！"
    echo ""
    echo "问题：AutoDL端口映射未正确配置"
    echo ""
    echo "解决方案："
    echo "1. 登录AutoDL控制台: https://www.autodl.com/console/instance/list"
    echo "2. 找到你的实例，点击'自定义服务'"
    echo "3. 添加端口映射:"
    echo "   - 容器端口: 6006"
    echo "   - 外部端口: 8443"
    echo "4. 保存后等待30秒"
    echo "5. 重新运行此脚本测试"
else
    echo "⚠️  连接失败"
    echo ""
    echo "可能的原因："
    echo "1. GPU服务器未启动模型服务"
    echo "2. 网络连接问题"
    echo "3. AutoDL端口映射未配置"
    echo ""
    echo "请检查GPU服务器上的服务是否正在运行："
    echo "  ps aux | grep remote_model_server"
fi

echo ""
echo "=========================================="
