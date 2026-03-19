# 回复内容显示修复

## 问题
思考过程能实时更新，但看不到正文回复内容。

## 原因
回复内容的外层条件判断有问题：
```typescript
if (msg.content && msg.content !== '...') {
  // 显示内容
}
```

对于最新的AI消息：
- 使用 `currentAnswer` 存储实时内容
- `msg.content` 可能是空的或 `'...'`
- 导致整个内容区域不显示

## 修复方案
分离最新消息和历史消息的判断逻辑：

```typescript
// 最新AI消息 - 检查 currentAnswer
if (msg.role === 'assistant' && 
    this.messages.length > 0 && 
    this.messages[this.messages.length - 1].id === msg.id) {
  if (this.currentAnswer.length > 0) {
    // 显示 currentAnswer
  }
}
// 其他消息 - 检查 msg.content
else if (msg.content && msg.content !== '...') {
  // 显示 msg.content
}
```

## 测试
1. 重新编译运行
2. 发送消息"你好吗"
3. 应该能看到：
   - 思考过程实时更新 ✅
   - 回复内容逐字显示 ✅
   - 顶部计数器：T:1026 A:150 F:25 ✅
