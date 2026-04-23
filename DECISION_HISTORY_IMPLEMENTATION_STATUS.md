# 决策历史功能实现状态

## 已完成

### 1. 后端实现 ✅
- ✅ 创建 `backend/decision/decision_history.py` - 历史记录管理器
  - 数据库表自动创建
  - 保存历史记录
  - 查询历史列表
  - 获取历史详情
  - 删除历史记录

- ✅ 创建 `backend/decision/report_generator.py` - 报告生成器
  - 使用 LLM 生成综合报告
  - 包含总体评价、关键洞察、优势、风险、建议
  - 备用报告机制（LLM 失败时）

- ✅ 在 `backend/main.py` 添加 API 路由
  - POST `/api/decision/history/save` - 保存历史
  - GET `/api/decision/history/list` - 获取列表
  - GET `/api/decision/history/detail/{history_id}` - 获取详情
  - DELETE `/api/decision/history/delete/{history_id}` - 删除历史
  - POST `/api/decision/generate-report` - 生成报告

### 2. 前端服务层 ✅
- ✅ 创建 `web/src/services/decisionHistory.ts`
  - 所有 API 调用封装
  - TypeScript 类型定义

### 3. 动画功能 ✅
- ✅ 移除所有 emoji 表情，替换为文字标签
- ✅ 添加观察连线动画（查看他人观点时）
- ✅ 添加分数影响中心球体动画

## 待实现

### 1. 前端 UI 组件

#### A. 决策报告弹窗 (DecisionReportModal.tsx)
**位置**: `web/src/components/decision/DecisionReportModal.tsx`

**功能**:
- 显示选项的综合报告
- 包含：总体评价、关键洞察、优势、风险、建议
- 显示各 Agent 的评估结果
- 提供"保存到历史"按钮

**Props**:
```typescript
interface DecisionReportModalProps {
  visible: boolean;
  onClose: () => void;
  report: DecisionReport;
  optionTitle: string;
  onSaveHistory?: () => void;
}
```

#### B. 历史决策列表页面 (DecisionHistoryPage.tsx)
**位置**: `web/src/pages/DecisionHistoryPage.tsx`

**功能**:
- 显示用户的所有历史决策
- 按时间倒序排列
- 显示：问题、时间、选项数量
- 点击查看详情
- 删除功能

#### C. 历史决策详情/还原页面
**功能**:
- 还原历史决策的最终场景
- 使用 PersonaInteractionView 组件
- 显示所有 Agent 的最终状态
- 只读模式（不能再次推演）

### 2. 集成到现有页面

#### A. DecisionSimulationPage.tsx 修改
**需要添加**:
1. "查看报告"按钮（在分析完成后显示）
2. 点击后调用 `generateDecisionReport` API
3. 显示 DecisionReportModal
4. 报告中提供"保存到历史"功能
5. 保存时调用 `saveDecisionHistory` API

**实现位置**:
- 在 `completedOptions` 状态更新后显示按钮
- 在每个选项的 PersonaInteractionView 下方

#### B. HomePage.tsx 修改
**需要添加**:
1. "查看历史决策"按钮/入口
2. 点击后导航到 DecisionHistoryPage

**实现位置**:
- 在决策副本功能球体附近
- 或在顶部导航栏

### 3. 数据流程

```
用户完成决策推演
  ↓
点击"查看报告"
  ↓
调用 generateDecisionReport API
  ↓
显示 DecisionReportModal
  ↓
用户点击"保存到历史"
  ↓
收集所有选项数据（agents、scores、history等）
  ↓
调用 saveDecisionHistory API
  ↓
保存成功提示
  ↓
用户可在"历史决策"中查看
  ↓
点击历史记录
  ↓
调用 getDecisionHistoryDetail API
  ↓
还原场景（使用 PersonaInteractionView）
```

## 下一步实现顺序

1. **创建 DecisionReportModal 组件** - 报告弹窗
2. **修改 DecisionSimulationPage** - 添加"查看报告"按钮和保存功能
3. **创建 DecisionHistoryPage** - 历史列表页面
4. **修改 HomePage** - 添加"查看历史决策"入口
5. **测试完整流程**
6. **优化 UI/UX**

## 技术要点

### 保存的数据结构
```typescript
{
  user_id: string;
  session_id: string;
  question: string;
  decision_type: string;
  options_data: {
    [optionId: string]: {
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
        // ... 其他 Agent 数据
      }>;
    }
  };
}
```

### 场景还原
使用现有的 `PersonaInteractionView` 组件，传入历史数据：
- `personas`: 从历史数据中的 agents 恢复
- `optionTitle`: 从历史数据中获取
- `totalScore`: 从历史数据中获取
- `isComplete`: 设为 true（只读模式）

## 文件清单

### 已创建
- ✅ `backend/decision/decision_history.py`
- ✅ `backend/decision/report_generator.py`
- ✅ `web/src/services/decisionHistory.ts`
- ✅ `backend/main.py` (已修改)

### 待创建
- ⏳ `web/src/components/decision/DecisionReportModal.tsx`
- ⏳ `web/src/components/decision/DecisionReportModal.css`
- ⏳ `web/src/pages/DecisionHistoryPage.tsx`
- ⏳ `web/src/styles/DecisionHistoryPage.css`

### 待修改
- ⏳ `web/src/pages/DecisionSimulationPage.tsx`
- ⏳ `web/src/pages/HomePage.tsx`

## 测试计划

1. 后端 API 测试
   - 保存历史记录
   - 查询历史列表
   - 获取历史详情
   - 生成报告

2. 前端功能测试
   - 查看报告弹窗
   - 保存到历史
   - 历史列表显示
   - 场景还原

3. 集成测试
   - 完整流程测试
   - 多用户测试
   - 性能测试

## 预计工作量

- DecisionReportModal: 2-3小时
- DecisionSimulationPage 修改: 1-2小时
- DecisionHistoryPage: 3-4小时
- HomePage 修改: 0.5小时
- 测试和优化: 2-3小时

**总计**: 约 8-12 小时
