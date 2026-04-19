# 智慧洞察系统 - 三层混合架构

## 系统概述

智慧洞察系统是一个基于真实数据的决策分析系统，采用三层混合架构：

1. **Layer 1: 规则引擎（涌现检测）** - 快速、可靠的模式识别
2. **Layer 2: 机器学习（量化评估）** - 准确的量化分析和预测
3. **Layer 3: LLM（深度解读）** - 智能的个性化建议和洞察

## 数据来源

系统从多个真实数据源获取数据：

- **MySQL**: 用户信息、学业数据（GPA、课程成绩）、行为历史（压力、健康、情绪等）
- **Neo4j**: 三种视图
  - 人物关系视图：人际网络、社交评分
  - 升学规划视图：教育路径、完成课程、技能
  - 职业发展视图：技术技能、软技能、职业准备度
- **RAG系统**: 相似案例检索、历史经验

## 系统架构

```
用户请求
    ↓
数据连接器 (data_connector.py)
    ↓ 获取真实数据
    ├─ MySQL: 用户信息、学业、行为
    ├─ Neo4j: 人际关系、教育路径、职业发展
    └─ RAG: 相似案例
    ↓
数据转换器 (data_transformer.py)
    ↓ 转换为标准格式
    ├─ 决策上下文
    ├─ 当前状态
    └─ 历史记录
    ↓
三层混合架构引擎 (hybrid_insights_engine.py)
    ↓
    ├─ Layer 1: 规则引擎 (emergence_adapter.py)
    │   └─ 涌现检测、模式识别
    │
    ├─ Layer 2: 机器学习 (ml_enhanced_insights.py)
    │   ├─ 可行性预测模型
    │   ├─ 风险评估模型
    │   ├─ 趋势预测模型
    │   └─ 个性化推荐模型
    │
    └─ Layer 3: LLM增强 (llm_enhancer.py)
        ├─ 深度洞察
        ├─ 个性化建议
        ├─ 评分解释
        ├─ 风险缓解方案
        └─ 对话式问答
    ↓
整合结果
    ↓
返回给用户
```

## 核心模块

### 1. 数据连接器 (`data_connector.py`)

负责从多个数据源获取真实数据：

```python
from insights.data_connector import get_data_connector

connector = get_data_connector()

# 获取综合数据
data = connector.get_comprehensive_data(
    user_id="user_001",
    decision_context={
        "decision_type": "education",
        "target_school": "清华大学",
        "target_major": "计算机科学"
    }
)
```

### 2. 数据转换器 (`data_transformer.py`)

将数据库数据转换为洞察引擎所需格式：

```python
from insights.data_transformer import get_data_transformer

transformer = get_data_transformer()

# 转换数据
decision_context = transformer.transform_to_decision_context(data, user_input)
current_status = transformer.transform_to_current_status(data)
history = transformer.transform_to_history(data)
```

### 3. 三层混合架构引擎 (`hybrid_insights_engine.py`)

整合三层分析结果：

```python
from insights.hybrid_insights_engine import get_hybrid_engine

engine = get_hybrid_engine()

# 执行分析
result = engine.analyze_comprehensive(
    decision_context=decision_context,
    current_status=current_status,
    history=history,
    enable_llm=True
)
```

### 4. 机器学习模型 (`ml_models.py`)

四个轻量级ML模型：

- **可行性预测模型**: 基于加权评分算法
- **风险评估模型**: 多因素分析
- **趋势预测模型**: 线性回归
- **个性化推荐模型**: 协同过滤

### 5. LLM增强器 (`llm_enhancer.py`)

提供深度智能分析：

- 深度洞察生成
- 个性化建议
- 评分解释
- 风险缓解方案
- 对话式问答

## API接口

### 1. 使用真实数据分析

```http
POST /api/insights/analyze-with-real-data
Authorization: Bearer <token>
Content-Type: application/json

{
  "decision_type": "education",
  "target_school": "清华大学",
  "target_major": "计算机科学",
  "target_gpa": 3.8,
  "estimated_cost": 100000,
  "enable_llm": true
}
```

响应：

```json
{
  "status": "success",
  "timestamp": "2024-01-01T00:00:00",
  "scores": {
    "feasibility": 0.85,
    "risk": 0.35,
    "comprehensive": 0.75,
    "grade": "B"
  },
  "key_findings": [...],
  "integrated_recommendations": [...],
  "action_plan": {...},
  "llm_enhancements": {...},
  "data_sources_info": {...}
}
```

### 2. 检查数据源状态

```http
GET /api/insights/data-sources-status
Authorization: Bearer <token>
```

### 3. 预览用户数据

```http
GET /api/insights/user-data-preview
Authorization: Bearer <token>
```

### 4. 健康检查

```http
GET /api/insights/health
```

## 前端使用

### 路由配置

```typescript
// web/src/App.tsx
import { DecisionInsightsPage } from './pages/DecisionInsightsPage';

<Route path="/insights" element={<DecisionInsightsPage />} />
```

### 服务调用

```typescript
import { analyzeWithRealData } from '../services/insightsService';

const result = await analyzeWithRealData({
  decision_type: 'education',
  target_school: '清华大学',
  target_major: '计算机科学',
  target_gpa: 3.8,
  estimated_cost: 100000,
  enable_llm: true
}, token);
```

## 测试

### 运行测试

```bash
# 测试三层混合架构
python backend/insights/test_hybrid_system.py

# 测试整合系统
python backend/insights/test_integrated_system.py

# 测试ML模型
python backend/insights/test_ml_insights.py
```

### 测试结果

测试会生成JSON文件，包含完整的分析结果：

- `test_hybrid_result.json` - 三层混合架构测试结果
- `test_integrated_result.json` - 整合系统测试结果
- `test_ml_result.json` - ML模型测试结果

## 配置

### 环境变量

```bash
# MySQL配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DATABASE=lifeswarm

# Neo4j配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# LLM配置（可选）
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key
```

## 特性

### 1. 无硬编码假数据

- 所有数据来源都是真实的数据库数据
- 没有硬编码的baseline值或默认数据
- 所有fallback方法基于真实数据动态生成

### 2. 三层混合架构

- Layer 1提供快速的模式识别
- Layer 2提供准确的量化分析
- Layer 3提供智能的个性化建议

### 3. 多数据源整合

- MySQL提供结构化数据
- Neo4j提供图数据和关系数据
- RAG系统提供相似案例和历史经验

### 4. 可扩展性

- 易于添加新的数据源
- 易于添加新的ML模型
- 易于添加新的分析维度

## 术语说明

系统采用"决策管理"风格的术语：

- **推演** → **分析**
- **模拟** → **规划**
- **预测结果** → **评估影响**
- **预测性** → **评估性**

## 文档

- `DECISION_MANAGEMENT_POSITIONING.md` - 系统定位说明
- `DECISION_MANAGEMENT_CHANGES.md` - 改造变更记录

## 注意事项

1. 确保数据库连接正常
2. LLM功能需要配置API密钥
3. 首次使用时会初始化ML模型
4. 建议先运行测试脚本验证系统

## 未来改进

- [ ] 添加更多ML模型
- [ ] 支持更多决策类型
- [ ] 优化LLM提示词
- [ ] 添加缓存机制
- [ ] 支持批量分析
- [ ] 添加可视化图表

## 联系方式

如有问题，请联系开发团队。
