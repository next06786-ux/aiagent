# 推演界面调试指南

## 问题描述
推演界面显示"等待 Agent 启动..."，但 Agents 一直没有出现。

## 可能的原因

### 1. WebSocket 连接失败
- 检查网络连接
- 检查后端服务是否运行
- 检查 WebSocket URL 是否正确

### 2. 后端没有发送 agents_start 消息
- 后端可能在等待某些条件
- 后端可能发送了不同格式的消息

### 3. 消息格式不匹配
- 前端期望的字段名与后端发送的不一致
- JSON 解析失败

## 调试步骤

### 步骤 1: 查看 Logcat 日志

使用 Android Studio 的 Logcat，过滤标签 `EnhancedSimulation`：

```
adb logcat -s EnhancedSimulation:D
```

### 步骤 2: 检查关键日志

#### 2.1 初始化日志
```
[初始化] 创建 X 个选项
[连接] 连接选项 option_1: XXX
[连接] WebSocket URL: ws://82.157.195.238:8000/api/decision/persona/ws/simulate-option
```

#### 2.2 连接成功日志
```
[WebSocket-option_1] 连接已建立
[WebSocket-option_1] 发送初始化消息: {...}
[WebSocket-option_1] 消息发送结果: true
```

#### 2.3 收到消息日志
```
[WebSocket-option_1] 收到消息: status
[消息处理-option_1] 类型: status, 完整消息: {...}
```

#### 2.4 Agents 初始化日志
```
[WebSocket-option_1] 收到消息: agents_start
[消息处理-option_1] 收到 agents_start/personas_start 消息
[handleAgentsStart-option_1] agentsArray: [...], month: 1
[handleAgentsStart-option_1] 添加 Agent: XXX (id)
[handleAgentsStart-option_1] 总共添加了 X 个 Agents
[updateOptionState-option_1] 更新状态: agents=X, score=0.0, complete=false
```

### 步骤 3: 常见问题诊断

#### 问题 A: 没有看到"连接已建立"日志
**原因**: WebSocket 连接失败
**解决方案**:
1. 检查网络连接
2. 检查后端服务是否运行在 `82.157.195.238:8000`
3. 检查防火墙设置

#### 问题 B: 看到"连接已建立"但没有收到任何消息
**原因**: 后端没有响应初始化消息
**解决方案**:
1. 检查后端日志，看是否收到了初始化消息
2. 检查 `session_id` 和 `user_id` 是否有效
3. 检查 `collected_info` 数据是否完整

#### 问题 C: 收到消息但类型不是 agents_start
**原因**: 后端发送了不同的消息类型
**解决方案**:
1. 查看日志中的"未知消息类型"警告
2. 根据实际消息类型调整代码
3. 可能需要先处理其他消息类型（如 status）

#### 问题 D: 收到 agents_start 但 agentsArray 为 null
**原因**: 消息格式不匹配
**解决方案**:
1. 查看完整消息内容
2. 检查字段名是否为 "agents" 或 "personas"
3. 可能需要调整字段名

## 临时解决方案

如果需要快速测试，可以在 `initializeOptions()` 方法中添加模拟数据：

```kotlin
private fun initializeOptions() {
    // ... 现有代码 ...
    
    // 临时：添加模拟 Agents 用于测试
    val mockAgents = listOf(
        PersonaAgent(id = "1", name = "创新者", status = PersonaStatus.WAITING),
        PersonaAgent(id = "2", name = "冒险家", status = PersonaStatus.WAITING),
        PersonaAgent(id = "3", name = "实用主义者", status = PersonaStatus.WAITING)
    )
    
    optionStates["option_1"] = optionStates["option_1"]!!.copy(agents = mockAgents)
    _uiState.update { it.copy(optionStates = optionStates.toMap()) }
}
```

## 下一步

1. 运行应用并查看 Logcat 日志
2. 根据日志输出确定具体问题
3. 如果需要，提供日志内容以便进一步诊断
