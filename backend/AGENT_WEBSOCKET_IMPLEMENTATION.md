# Agent WebSocket实时推送实现方案

## 概述
实现WebSocket实时推送Agent工具调用状态，让前端能看到running→completed的动画过程。

## 架构设计

### 1. 后端改动
- 创建WebSocket端点：`/ws/agent-chat`
- 在MCP工具调用前后发送状态更新
- 推送消息格式：
  ```json
  {
    "type": "tool_start",
    "tool_name": "web_search",
    "server_name": "Web Search Server"
  }
  {
    "type": "tool_complete",
    "tool_name": "web_search", 
    "server_name": "Web Search Server",
    "result": "..."
  }
  {
    "type": "response",
    "content": "最终回复内容"
  }
  ```

### 2. 前端改动
- 建立WebSocket连接
- 监听工具调用事件
- 动态更新UI状态

## 实现步骤

### 阶段1：最小可行方案（推荐先实现）
保留现有HTTP API，添加简单的前端模拟动画：
- 前端收到响应后，先显示running状态
- 延迟1秒后更新为completed
- 优点：实现简单，立即可用
- 缺点：不是真实的实时推送

### 阶段2：完整WebSocket方案
完整实现WebSocket实时推送：
- 后端在工具调用时实时推送状态
- 前端通过WebSocket接收更新
- 优点：真实的实时体验
- 缺点：需要较大改动，增加复杂度

## 建议
考虑到当前系统的复杂度和开发时间，建议：
1. **先实现阶段1**（5分钟完成）
2. 验证用户体验是否满意
3. 如果需要更真实的体验，再实现阶段2

## 阶段1实现代码

### 前端修改（AgentChatDialog.tsx）
```typescript
// 在handleSend函数中，收到响应后
if (data.tool_calls && data.tool_calls.length > 0) {
  // 先显示running状态
  const runningMessage: Message = {
    role: 'assistant',
    content: '',
    timestamp: new Date(),
    toolCalls: data.tool_calls.map(tool => ({
      ...tool,
      status: 'running'
    }))
  };
  setMessages(prev => [...prev, runningMessage]);
  
  // 1秒后更新为completed并显示回复
  setTimeout(() => {
    setMessages(prev => prev.map((msg, idx) => 
      idx === prev.length - 1 
        ? {
            ...msg,
            content: data.response,
            toolCalls: data.tool_calls
          }
        : msg
    ));
  }, 1000);
} else {
  // 没有工具调用，直接显示回复
  const assistantMessage: Message = {
    role: 'assistant',
    content: data.response,
    timestamp: new Date(),
    retrievalStats: data.retrieval_stats
  };
  setMessages(prev => [...prev, assistantMessage]);
}
```

这样用户就能看到：
1. 发送消息
2. 工具调用动画（蓝色脉冲，running状态）
3. 1秒后变为绿色✓（completed状态）
4. 显示最终回复

## 决策
请确认要实现哪个阶段？
- [ ] 阶段1：前端模拟动画（快速，推荐）
- [ ] 阶段2：完整WebSocket（复杂，真实）
