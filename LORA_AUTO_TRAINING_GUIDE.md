# LoRA 自动训练系统使用指南

## 📚 系统概述

你的 AI 系统有一个完整的 LoRA 自动训练机制，可以根据你的对话历史自动训练个性化模型。

## 🔄 数据流程

```
你的对话 
    ↓
[自动保存到两个地方]
    ↓
┌─────────────────┬─────────────────┐
│  MySQL 数据库    │   RAG 系统      │
│  (结构化存储)    │   (语义检索)    │
└─────────────────┴─────────────────┘
    ↓                    ↓
    └────────┬───────────┘
             ↓
    [LoRA 训练器自动读取]
             ↓
    [训练个性化模型]
             ↓
    [用于决策分析]
```

## ✅ 对话数据自动保存

### 1. 数据库保存 (ConversationStorage)
- **位置**: MySQL `conversation_history` 表
- **触发**: 每次对话自动保存
- **内容**: 
  - 用户消息
  - AI 回复
  - 时间戳
  - 会话 ID
  - 思考过程（可选）

### 2. RAG 系统保存 (ProductionRAGSystem)
- **位置**: `backend/data/production_rag/` 目录
- **触发**: 对话结束后自动存储
- **内容**:
  - 对话记忆
  - 语义向量
  - 上下文信息

## 🤖 LoRA 自动训练机制

### 方式一：定时自动训练（推荐）

系统有一个 **LoRA 调度器** (`LoRAScheduler`)，会自动训练：

```python
# 在 backend/main.py 中自动启动
scheduler = LoRAScheduler()
scheduler.start()
```

**训练时机**：
- 每周日凌晨 2:00 自动训练所有活跃用户
- 检查训练队列，处理高优先级任务
- 满足条件时自动触发训练

**训练条件**：
1. 新增对话数 ≥ 20 条
2. 距离上次训练 ≥ 7 天
3. 总对话数 ≥ 50 条

### 方式二：手动立即训练

使用新的统一训练脚本：

```bash
python train_lora_unified.py
```

**功能**：
- ✅ 自动从数据库读取对话
- ✅ 自动从 RAG 系统读取记忆
- ✅ 合并去重数据
- ✅ 立即开始训练
- ✅ 强制重新训练（忽略时间间隔）

### 方式三：通过 API 触发

```python
from backend.lora.lora_scheduler import get_scheduler

scheduler = get_scheduler()
scheduler.add_training_task(
    user_id="你的用户ID",
    priority="high"  # 高优先级，立即训练
)
```

## 📊 训练数据要求

| 数据量 | 状态 | 说明 |
|--------|------|------|
| < 5 对对话 | ❌ 无法训练 | 数据太少 |
| 5-20 对对话 | ⚠️ 可以训练 | 效果一般 |
| 20-50 对对话 | ✅ 良好 | 推荐 |
| > 50 对对话 | ✅ 优秀 | 最佳效果 |

## 🎯 使用场景

### 1. 决策分析
训练后的 LoRA 模型会用于：
- 生成个性化的决策建议
- 模拟你的思维方式
- 预测你的选择倾向

### 2. 对话风格
模型会学习：
- 你的表达习惯
- 你的关注点
- 你的价值观

### 3. 平行宇宙模拟
在决策模拟中：
- 生成符合你性格的时间线
- 预测不同选择的结果
- 提供个性化的风险评估

## 🔧 配置文件

训练配置在 `backend/data/lora_status/{user_id}_status.json`：

```json
{
  "user_id": "你的ID",
  "model_version": 1,
  "last_training_time": "2024-01-15T10:30:00",
  "training_samples": 45,
  "training_config": {
    "min_conversations": 20,
    "train_interval_days": 7,
    "max_samples": 1000
  }
}
```

## 🐛 故障排查

### 问题 1: KeyError: 'session_id'
**原因**: 代码使用了错误的字段名  
**解决**: 已修复，使用 `session['id']` 而不是 `session['session_id']`

### 问题 2: 训练数据不足
**原因**: 对话历史太少  
**解决**: 
1. 多与 AI 对话几轮
2. 确保对话被保存到数据库
3. 检查 RAG 系统是否正常工作

### 问题 3: 找不到模型
**原因**: 训练失败或路径错误  
**解决**:
```bash
# 检查模型目录
ls backend/data/lora_models/

# 查看训练日志
python train_lora_unified.py
```

## 📝 最佳实践

1. **积累数据**: 先正常使用系统，积累至少 20 对对话
2. **定期训练**: 让调度器自动运行，每周训练一次
3. **手动触发**: 重要决策前，可以手动训练最新模型
4. **监控状态**: 通过 API 查看训练状态

```python
# 查看训练状态
from backend.lora.lora_scheduler import get_scheduler
status = get_scheduler().get_status()
print(status)
```

## 🚀 快速开始

1. **确保系统运行**:
```bash
python start_system.py
```

2. **与 AI 对话**:
- 打开前端界面
- 进行至少 5-10 轮对话
- 对话会自动保存

3. **手动训练**（可选）:
```bash
python train_lora_unified.py
```

4. **使用决策功能**:
- 打开决策模拟页面
- 输入决策问题
- 系统会使用你的个性化模型

## 💡 提示

- 对话质量比数量更重要
- 多样化的对话主题会提升模型效果
- 训练需要几分钟，请耐心等待
- 模型会随着使用不断改进

---

**现在你可以放心使用了！** 系统会自动保存你的对话，并在合适的时候训练个性化模型。🎉
