# 暂停/继续功能修复说明

## 问题描述
点击顶部选项栏的暂停按钮后，推演并没有真正暂停，Agent 仍在继续思考和更新。

## 根本原因

### 原因1: 前端只发送暂停消息，但继续处理接收到的消息
即使发送了 `{"action":"pause"}` 消息给后端，前端的 WebSocket 监听器仍然会接收并处理所有消息，导致界面继续更新。

### 原因2: 后端可能不支持暂停/继续控制
需要确认后端是否真的会响应 `{"action":"pause"}` 和 `{"action":"resume"}` 消息。

## 修复方案

### 修复1: 在消息处理时检查暂停状态

在 `onMessage` 回调中添加暂停状态检查：

```kotlin
override fun onMessage(webSocket: WebSocket, text: String) {
    try {
        val json = JSONObject(text)
        val eventType = json.optString("type")
        
        // 检查是否已暂停
        val currentState = optionStates[optionId]
        if (currentState?.isPaused == true) {
            Log.d(TAG, "[WebSocket-$optionId] 选项已暂停，忽略消息: $eventType")
            return  // 直接返回，不处理消息
        }
        
        handleWebSocketMessage(optionId, eventType, json)
    } catch (e: Exception) {
        Log.e(TAG, "[WebSocket-$optionId] 解析消息失败", e)
    }
}
```

**工作原理**:
- 当用户点击暂停按钮时，`isPaused` 状态被设置为 `true`
- WebSocket 仍然接收消息，但在处理前检查暂停状态
- 如果已暂停，直接忽略消息，不更新 UI
- 当用户点击继续按钮时，`isPaused` 被设置为 `false`，消息处理恢复

### 修复2: 添加详细日志

在 `pauseOption` 和 `resumeOption` 方法中添加详细日志：

```kotlin
fun pauseOption(optionId: String) {
    Log.d(TAG, "[暂停] 暂停选项: $optionId")
    
    // 更新状态
    optionStates[optionId] = currentState.copy(isPaused = true)
    Log.d(TAG, "[暂停] 状态已更新为暂停")
    
    // 发送暂停消息
    val pauseMessage = """{"action":"pause"}"""
    val sendResult = ws.send(pauseMessage)
    Log.d(TAG, "[暂停] 发送暂停消息: $pauseMessage, 结果: $sendResult")
}
```

## 验证步骤

### 步骤1: 查看暂停日志

点击暂停按钮后，查看 Logcat 日志：

```bash
adb logcat -s EnhancedSimulation:D
```

应该看到：
```
[暂停] 暂停选项: option_1
[暂停] 状态已更新为暂停
[暂停] 发送暂停消息: {"action":"pause"}, 结果: true
```

### 步骤2: 确认消息被忽略

暂停后，继续接收的消息应该被忽略：

```
[WebSocket-option_1] 收到消息: agent_thinking
[WebSocket-option_1] 选项已暂停，忽略消息: agent_thinking
[WebSocket-option_1] 收到消息: agent_thinking
[WebSocket-option_1] 选项已暂停，忽略消息: agent_thinking
```

### 步骤3: 验证界面不再更新

暂停后：
- ✅ Agent 球体不再显示新的思考消息
- ✅ 评分不再变化
- ✅ 状态指示器（loading spinner）停止
- ✅ 选项标签显示播放图标（▶）而不是暂停图标（||）

### 步骤4: 验证继续功能

点击继续按钮后：

```
[继续] 继续选项: option_1
[继续] 状态已更新为继续
[继续] 发送继续消息: {"action":"resume"}, 结果: true
```

然后消息处理恢复：
```
[WebSocket-option_1] 收到消息: agent_thinking
[消息处理-option_1] 类型: agent_thinking
[updateOptionState-option_1] 更新状态: agents=7, score=72.0, complete=false
```

## 后端支持检查

如果后端不支持 `{"action":"pause"}` 和 `{"action":"resume"}` 消息，可能需要：

### 方案A: 纯前端暂停（当前实现）
- 优点：不依赖后端支持，立即生效
- 缺点：后端仍在计算，浪费资源；暂停期间的消息会丢失

### 方案B: 关闭 WebSocket 连接
```kotlin
fun pauseOption(optionId: String) {
    // 关闭 WebSocket 连接
    webSocketInstances[optionId]?.close(1000, "Paused by user")
    webSocketInstances.remove(optionId)
}

fun resumeOption(optionId: String) {
    // 重新建立连接
    val index = optionId.removePrefix("option_").toIntOrNull()?.minus(1) ?: 0
    connectOption(optionId, index)
}
```
- 优点：完全停止后端计算，节省资源
- 缺点：继续时需要重新连接，可能丢失进度

### 方案C: 后端支持暂停/继续（推荐）
需要后端实现：
- 接收 `{"action":"pause"}` 消息时，暂停 Agent 思考
- 接收 `{"action":"resume"}` 消息时，恢复 Agent 思考
- 保持 WebSocket 连接，但不发送新消息

## 当前实现

当前使用 **方案A（纯前端暂停）**：
- 发送暂停消息给后端（如果后端支持会暂停计算）
- 前端忽略暂停期间接收到的所有消息
- 界面停止更新，给用户暂停的体验

## 建议

1. **短期方案**：使用当前的纯前端暂停实现，已经可以满足用户需求
2. **长期方案**：与后端协调，实现真正的暂停/继续控制，节省计算资源
3. **备选方案**：如果后端不支持暂停，可以考虑关闭 WebSocket 连接的方式

## 测试场景

### 场景1: 暂停单个选项
1. 启动推演，选项1开始运行
2. 点击选项1的暂停按钮
3. 验证：选项1的 Agent 停止更新，但其他选项（如果启动）继续运行

### 场景2: 暂停后切换选项
1. 暂停选项1
2. 切换到选项2
3. 验证：选项2正常显示和更新

### 场景3: 暂停后继续
1. 暂停选项1
2. 等待几秒
3. 点击继续按钮
4. 验证：选项1恢复更新（从暂停时的状态继续）

### 场景4: 多选项并行暂停
1. 启动选项1和选项2
2. 暂停选项1
3. 验证：选项1停止，选项2继续
4. 暂停选项2
5. 验证：两个选项都停止
