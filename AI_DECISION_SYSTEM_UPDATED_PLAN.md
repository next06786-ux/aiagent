# AI模拟人生决策系统 - 更新集成方案（集成LoRA）

## 核心变更

将原计划中的【新增2】个性化Prompt引擎替换为已有的**LoRA自动化微调系统**

```
原方案: 个性化Prompt引擎 = 性格基座 + RAG记忆 + 知识图谱 + 强化学习
新方案: LoRA个性化模型 = 性格基座 + RAG对话数据 + 自动微调
```

---

## 系统架构（更新版）

```
┌─────────────────────────────────────────────────────────────┐
│                    用户首次使用                              │
│              ↓                                               │
│         【已实现】心理测评系统 (20题)                        │
│              ↓                                               │
│         构建用户性格基座 (决策风格/风险偏好/价值观)           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    日常使用阶段                              │
│                                                              │
│  【已有】多模态数据采集 → RAG记忆系统 → 知识图谱            │
│              ↓                                               │
│  【已有】LoRA自动化训练系统                                  │
│    ├─ 自动收集用户对话数据（从RAG）                          │
│    ├─ 每周自动训练个性化模型                                 │
│    ├─ 基于Qwen-0.8B + LoRA（RTX 3050友好）                  │
│    └─ 模型版本管理（v1, v2, v3...）                         │
│              ↓                                               │
│  【新增】决策时使用LoRA模型                                  │
│    = 性格基座 + 个性化LoRA + 实时状态                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  重大决策场景                                │
│  用户: "我要不要考研?" "要不要换工作?"                      │
│              ↓                                               │
│  【已实现】平行宇宙模拟器                                    │
│    ├─ 基于digital_twin.py                                   │
│    ├─ 模拟多个选项的未来12个月                              │
│    └─ 使用LoRA模型生成个性化分析                            │
│              ↓                                               │
│  【新增】LoRA增强的决策分析                                  │
│    ├─ 使用用户专属LoRA模型                                  │
│    ├─ 结合性格画像                                          │
│    ├─ 生成个性化建议                                        │
│    └─ 风险评估 + 缓解方案                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 实施步骤

### 步骤1: 增强决策模拟API（集成LoRA）✅ 已完成

**文件**: `backend/main.py` - `/api/decision/simulate` 端点

**功能**:
- 接收 `use_lora` 参数（默认True）
- 如果用户有LoRA模型,使用个性化模型
- 否则降级到基础模型

**已实现**: 当前系统已支持此功能

---

### 步骤2: 创建LoRA增强的决策分析器 🔄 进行中

**新建文件**: `backend/decision/lora_decision_analyzer.py`

**功能**:
```python
class LoRADecisionAnalyzer:
    """使用LoRA模型进行个性化决策分析"""
    
    def analyze_with_lora(self, user_id, question, options, personality_profile):
        """
        使用用户的LoRA模型分析决策
        
        输入:
        - user_id: 用户ID
        - question: 决策问题
        - options: 选项列表
        - personality_profile: 性格画像
        
        输出:
        - 每个选项的个性化分析
        - 推荐方案
        - 风险评估
        """
```

**集成点**:
- 在 `parallel_universe_simulator.py` 中调用
- 为每个选项生成个性化的时间线事件
- 基于用户性格和LoRA模型预测反应

---

### 步骤3: 优化LoRA训练触发机制 📋 待实现

**文件**: `backend/lora/auto_lora_trainer.py`

**优化内容**:
1. **智能触发**:
   - 原: 固定7天 + 20条对话
   - 新: 动态调整（重大决策后立即训练）

2. **决策数据优先**:
   - 决策相关对话权重更高
   - 自动标注决策类对话

3. **增量训练**:
   - 不是每次从头训练
   - 基于上一版本继续训练

---

### 步骤4: 创建决策验证与LoRA反馈循环 📋 待实现

**新建文件**: `backend/decision/decision_feedback_loop.py`

**功能**:
```python
class DecisionFeedbackLoop:
    """决策验证与LoRA优化循环"""
    
    def track_decision_outcome(self, decision_id, actual_result):
        """追踪决策实际结果"""
        
    def generate_training_data(self, decision_id):
        """
        从决策结果生成训练数据
        - 如果预测准确 → 正样本
        - 如果预测失败 → 负样本 + 纠正
        """
        
    def trigger_lora_update(self, user_id):
        """触发LoRA模型更新"""
```

**工作流**:
1. 用户做决策 → 记录AI建议
2. 3个月后 → 询问实际结果
3. 对比预测 vs 实际 → 生成训练样本
4. 触发LoRA训练 → 模型优化

---

### 步骤5: 前端集成LoRA状态显示 📋 待实现

**新建组件**: `harmonyos/entry/src/main/ets/components/LoRAStatusCard.ets`

**显示内容**:
- LoRA模型状态（已训练/训练中/未训练）
- 模型版本（v1, v2, v3...）
- 训练数据量
- 上次训练时间
- 下次训练时间
- 个性化程度（0-100%）

**位置**: 决策页面顶部

---

## 技术优势

### 1. 真正的个性化
- 不是简单的Prompt工程
- 是模型级别的个性化
- 每个用户有专属的神经网络权重

### 2. 持续进化
- 用户越用越准
- 自动学习用户偏好
- 决策反馈闭环优化

### 3. 隐私保护
- 本地训练（RTX 3050）
- 数据不出本地
- 模型文件加密存储

### 4. 资源友好
- LoRA轻量级（~10MB/用户）
- 训练快速（3-5分钟）
- 推理高效（20 tokens/s）

---

## 开发计划（更新）

### 第1周: LoRA集成 ✅ 已完成
- [x] 心理测评系统
- [x] 平行宇宙模拟器
- [x] 基础LoRA系统

### 第2周: 决策分析增强 🔄 进行中
- [ ] LoRA决策分析器
- [ ] 个性化时间线生成
- [ ] 风险评估引擎

### 第3周: 反馈循环
- [ ] 决策追踪系统
- [ ] LoRA训练数据生成
- [ ] 自动优化机制

### 第4周: 前端完善
- [ ] LoRA状态显示
- [ ] 决策可视化
- [ ] 用户测试

---

## API设计

### 1. 决策模拟（已实现）
```
POST /api/decision/simulate
{
  "user_id": "user_001",
  "question": "要不要考研？",
  "options": [...],
  "use_lora": true  // 使用LoRA模型
}
```

### 2. LoRA状态查询
```
GET /api/lora/status/{user_id}
返回:
{
  "has_lora": true,
  "model_version": 3,
  "training_data_size": 150,
  "last_train_time": "2026-03-10",
  "next_train_time": "2026-03-17",
  "personalization_score": 85
}
```

### 3. 手动触发训练
```
POST /api/lora/train/{user_id}
{
  "priority": "high"  // 高优先级（决策后）
}
```

### 4. 决策反馈
```
POST /api/decision/feedback
{
  "decision_id": "dec_123",
  "actual_result": "选择了考研，目前进展顺利",
  "satisfaction": 8  // 1-10分
}
```

---

## 数据库扩展

### 新增表: decision_feedback
```sql
CREATE TABLE decision_feedback (
    id INTEGER PRIMARY KEY,
    user_id TEXT,
    decision_id TEXT,
    predicted_option TEXT,
    actual_option TEXT,
    predicted_score REAL,
    actual_satisfaction INTEGER,
    feedback_time TIMESTAMP,
    used_for_training BOOLEAN
);
```

### 新增表: lora_training_log
```sql
CREATE TABLE lora_training_log (
    id INTEGER PRIMARY KEY,
    user_id TEXT,
    model_version INTEGER,
    training_data_size INTEGER,
    training_duration REAL,
    training_loss REAL,
    train_time TIMESTAMP
);
```

---

## 答辩亮点（更新）

### 技术创新
1. **LoRA个性化** - 每个用户专属AI模型
2. **决策数字孪生** - 模拟平行宇宙
3. **闭环学习** - 决策反馈自动优化模型
4. **多模态融合** - 传感器+对话+图像
5. **本地化部署** - RTX 3050可运行

### 实用价值
1. 真正理解用户个性
2. 预测准确率持续提升
3. 隐私保护（本地训练）
4. 资源友好（轻量级）

### 完整性
- 前端: HarmonyOS
- 后端: FastAPI + LoRA
- AI: Qwen + 个性化微调
- 数据: 自动采集 + 自动训练

---

## 下一步行动

1. ✅ 测试当前决策系统
2. 🔄 创建LoRA决策分析器
3. 📋 实现决策反馈循环
4. 📋 优化LoRA训练策略
5. 📋 前端集成LoRA状态

---

## 总结

通过集成已有的LoRA系统,我们实现了:
- ✅ 真正的个性化（模型级别）
- ✅ 持续进化（自动学习）
- ✅ 隐私保护（本地训练）
- ✅ 资源友好（RTX 3050）
- ✅ 技术先进（LoRA微调）

这比原计划的"Prompt工程"更加先进和实用!
