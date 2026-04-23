# WebSocket消息流测试

## 问题
消息气泡完全没有渲染出来

## 可能原因

### 1. 后端没有发送事件
- 检查后端日志，确认是否真的调用了 `status_callback`
- 检查 `status_callback` 是否正确传递到了 `analyze_decision` 方法

### 2. 前端没有接收到事件
- 检查浏览器控制台的 `[WebSocket]` 日志
- 检查是否有 `[Agent事件]` 日志

### 3. 事件数据结构不匹配
- 后端发送的事件类型和前端期望的不一致
- 事件数据字段名称不匹配

## 调试步骤

### 步骤1: 检查后端是否发送事件
在后端 `persona_decision_api.py` 的 `ws_status_callback` 函数中添加日志：

```python
async def ws_status_callback(event_type: str, data: Dict[str, Any]):
    """实时推送Agent状态到前端"""
    try:
        logger.info(f"[WS推送] 准备发送事件: {event_type}, persona_id={data.get('persona_id')}")
        # 直接发送，不嵌套在agent_event中
        await safe_send({
            "type": event_type,
            "option_id": option_id,
            **data
        })
        logger.info(f"[WS推送] ✅ 事件已发送: {event_type}")
    except Exception as e:
        logger.error(f"WebSocket推送失败: {e}")
```

### 步骤2: 检查前端是否接收事件
在前端 `DecisionSimulationPage.tsx` 的 WebSocket 消息处理中添加日志：

```typescript
socket.addEventListener('message', (event) => {
  try {
    const parsed = JSON.parse(String(event.data)) as Record<string, unknown>;
    console.log('[WebSocket] 收到原始消息:', parsed);
    console.log('[WebSocket] 消息类型:', parsed.type);
    console.log('[WebSocket] 完整数据:', JSON.stringify(parsed, null, 2));
    
    if (parsed.type === 'error') {
      handlers.onError?.(String(parsed.content || '推演流式连接异常'));
    }
    handlers.onEvent?.(parsed);
  } catch (error) {
    console.error('[WebSocket] 解析消息失败:', error, event.data);
  }
});
```

### 步骤3: 检查事件处理逻辑
确认前端的事件处理代码是否被执行：

```typescript
// 在 phase_complete 事件处理开始处添加
if (eventType === 'phase_complete') {
  console.log('🔍 [DEBUG] phase_complete事件触发');
  console.log('🔍 [DEBUG] personaId:', personaId);
  console.log('🔍 [DEBUG] phase:', event.phase);
  console.log('🔍 [DEBUG] event.result:', event.result);
  
  // ... 后续处理
}
```

## 预期结果

如果一切正常，应该看到：
1. 后端日志：`[WS推送] ✅ 事件已发送: phase_complete`
2. 前端日志：`[WebSocket] 收到原始消息: {type: 'phase_complete', ...}`
3. 前端日志：`🔍 [DEBUG] phase_complete事件触发`
4. 前端日志：`[Agent事件] 最终 displayMessage: ✅ 独立思考: ...`
5. PersonaInteractionView 渲染消息气泡

## 当前状态
- [ ] 后端发送事件日志
- [ ] 前端接收事件日志
- [ ] 前端处理事件日志
- [ ] 消息气泡渲染
