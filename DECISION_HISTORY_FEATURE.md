# 决策历史功能实现计划

## 功能需求

### 1. 查看报告功能
- 在分析完成后，显示"查看报告"按钮
- 生成该选项的综合报告，包括：
  - 选项标题和描述
  - 总体评分
  - 各 Agent 的最终立场和评分
  - 关键观点汇总
  - 推演过程摘要
  - 优势和风险分析

### 2. 保存决策历史
- 保存内容：
  - 决策问题
  - 所有选项的数据
  - 每个 Agent 的完整推演历史
  - 最终场景快照（Agent 位置、状态、分数等）
  - 时间戳
- 存储位置：后端数据库（MySQL）

### 3. 查看历史决策
- 在决策副本主界面添加"查看历史决策"按钮
- 显示历史决策列表（按时间倒序）
- 点击某个历史决策，还原当时的最终场景

## 数据结构设计

### 前端数据结构
```typescript
interface DecisionHistory {
  id: string;
  userId: string;
  sessionId: string;
  question: string;
  decisionType: string;
  options: Array<{
    id: string;
    title: string;
    description: string;
    totalScore: number;
    agents: Array<{
      id: string;
      name: string;
      finalStance: string;
      finalScore: number;
      finalConfidence: number;
      thinkingHistory: any[];
    }>;
  }>;
  createdAt: string;
  completedAt: string;
}
```

### 后端数据库表
```sql
CREATE TABLE decision_histories (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  session_id VARCHAR(36) NOT NULL,
  question TEXT NOT NULL,
  decision_type VARCHAR(50),
  options_data JSON NOT NULL,  -- 存储所有选项的完整数据
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP,
  INDEX idx_user_id (user_id),
  INDEX idx_created_at (created_at)
);
```

## API 设计

### 1. 保存决策历史
```
POST /api/decision/history/save
Request:
{
  "session_id": "xxx",
  "user_id": "xxx",
  "question": "xxx",
  "decision_type": "xxx",
  "options_data": {...}
}
Response:
{
  "success": true,
  "history_id": "xxx"
}
```

### 2. 获取历史决策列表
```
GET /api/decision/history/list?user_id=xxx&limit=20&offset=0
Response:
{
  "success": true,
  "histories": [
    {
      "id": "xxx",
      "question": "xxx",
      "created_at": "xxx",
      "options_count": 3,
      "preview": {...}
    }
  ],
  "total": 100
}
```

### 3. 获取历史决策详情
```
GET /api/decision/history/detail?history_id=xxx
Response:
{
  "success": true,
  "history": {...}  // 完整的历史数据
}
```

### 4. 生成选项报告
```
POST /api/decision/generate-report
Request:
{
  "session_id": "xxx",
  "option_id": "xxx",
  "agents_data": [...]
}
Response:
{
  "success": true,
  "report": {
    "summary": "xxx",
    "key_insights": [...],
    "strengths": [...],
    "risks": [...],
    "recommendation": "xxx"
  }
}
```

## 实现步骤

### 阶段 1: 后端实现
1. 创建数据库表
2. 实现保存历史 API
3. 实现查询历史 API
4. 实现生成报告 API（使用 LLM）

### 阶段 2: 前端实现
1. 在 DecisionSimulationPage 添加"查看报告"按钮
2. 创建报告弹窗组件 (DecisionReportModal)
3. 实现保存历史功能
4. 创建历史决策列表页面 (DecisionHistoryPage)
5. 实现场景还原功能

### 阶段 3: 集成测试
1. 测试完整流程
2. 优化 UI/UX
3. 性能优化

## 文件清单

### 需要创建的文件
1. `backend/decision/decision_history.py` - 历史记录管理
2. `backend/decision/report_generator.py` - 报告生成器
3. `web/src/components/decision/DecisionReportModal.tsx` - 报告弹窗
4. `web/src/pages/DecisionHistoryPage.tsx` - 历史列表页面
5. `web/src/services/decisionHistory.ts` - 历史记录 API 服务

### 需要修改的文件
1. `backend/main.py` - 添加新的 API 路由
2. `web/src/pages/DecisionSimulationPage.tsx` - 添加查看报告和保存历史
3. `web/src/pages/HomePage.tsx` - 添加查看历史决策入口
4. `backend/database/schema.sql` - 添加数据库表

## 下一步
开始实现后端 API 和数据库表
