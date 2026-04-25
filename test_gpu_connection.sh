#!/bin/bash
# 测试GPU服务器连接

echo "=========================================="
echo "测试GPU服务器连接"
echo "=========================================="
echo ""

REMOTE_URL="https://u821458-b49a-bdca5515.westc.seetacloud.com:8443"

echo "服务器地址: $REMOTE_URL"
echo ""

# 测试1: 根路径
echo "测试1: 根路径 /"
curl -k -s "$REMOTE_URL/" | head -n 5
echo ""
echo ""

# 测试2: 健康检查
echo "测试2: 健康检查 /health"
curl -k -s "$REMOTE_URL/health"
echo ""
echo ""

# 测试3: 模型信息
echo "测试3: 模型信息 /model/info"
curl -k -s "$REMOTE_URL/model/info"
echo ""
echo ""

# 测试4: 聊天接口
echo "测试4: 聊天接口 /chat"
curl -k -s -X POST "$REMOTE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"你好"}],"temperature":0.7,"max_tokens":50}'
echo ""
echo ""

echo "=========================================="
echo "如果所有测试都返回404，请检查AutoDL端口映射:"
echo "1. 登录AutoDL控制台"
echo "2. 找到你的实例，点击'自定义服务'"
echo "3. 添加端口映射: 容器端口6006 -> 外部端口8443"
echo "4. 保存后等待几秒钟生效"
echo "=========================================="
