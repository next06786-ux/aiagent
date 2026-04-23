# 动画功能实现计划

## 已完成
1. ✅ 移除前端消息气泡和记录面板中的 emoji，替换为文字标签
   - DecisionSimulationPage.tsx: 所有阶段消息的 emoji 已替换
   - AgentThinkingPanel.tsx: 状态图标 emoji 已替换
   - DecisionGraphStage.tsx: 状态图标 emoji 已替换
   - PersonaInteractionView.tsx: 立场改变检测已更新

## 待实现

### 2. 查看他人观点时的连线动画
**需求**: 当 Agent 进入"查看他人观点"阶段时，从当前 Agent 向被观察的其他 Agent 画连线动画

**实现方案**:
1. 在 PersonaInteractionView 中添加状态跟踪观察关系:
   ```typescript
   const [observationLines, setObservationLines] = useState<Array<{
     from: string;  // 观察者 persona id
     to: string[];  // 被观察者 persona ids
     timestamp: number;
   }>>([]);
   ```

2. 在 DecisionSimulationPage 的 `observe_others` 事件处理中，提取观察关系并传递给 PersonaInteractionView

3. 在 PersonaInteractionView 中渲染连线:
   - 使用 SVG line 元素
   - 添加动画效果 (stroke-dasharray + stroke-dashoffset)
   - 连线颜色使用观察者的颜色
   - 连线持续时间 2-3 秒后自动消失

4. CSS 动画:
   ```css
   @keyframes observation-line {
     0% {
       stroke-dashoffset: 100;
       opacity: 0;
     }
     20% {
       opacity: 1;
     }
     80% {
       opacity: 1;
     }
     100% {
       stroke-dashoffset: 0;
       opacity: 0;
     }
   }
   ```

### 3. 决策影响总分时的中心球体动画
**需求**: 每个 Agent 的每轮决策后，如果对总分数有影响，要有一个对中间球体的动画效果

**实现方案**:
1. 在 PersonaInteractionView 中已有 `scoreImpactAnimations` 状态

2. 在 DecisionSimulationPage 的 `decision` 阶段完成事件中:
   - 检测分数变化 (event.score_impact)
   - 触发中心球体动画

3. 渲染中心球体动画:
   - 从 Agent 节点向中心发射粒子/光束
   - 中心球体脉冲效果
   - 显示分数变化 (+X 或 -X)
   - 根据分数正负使用不同颜色 (绿色/红色)

4. CSS 动画:
   ```css
   @keyframes score-impact-pulse {
     0% {
       transform: scale(1);
       opacity: 1;
     }
     50% {
       transform: scale(1.3);
       opacity: 0.8;
     }
     100% {
       transform: scale(1);
       opacity: 1;
     }
   }
   
   @keyframes score-particle {
     0% {
       transform: translate(0, 0) scale(1);
       opacity: 1;
     }
     100% {
       transform: translate(var(--tx), var(--ty)) scale(0);
       opacity: 0;
     }
   }
   ```

## 文件修改清单

### 需要修改的文件:
1. `web/src/components/decision/PersonaInteractionView.tsx`
   - 添加观察连线状态和渲染逻辑
   - 完善中心球体动画效果

2. `web/src/components/decision/PersonaInteractionView.css`
   - 添加连线动画 CSS
   - 添加中心球体动画 CSS

3. `web/src/pages/DecisionSimulationPage.tsx`
   - 在 observe_others 事件中提取观察关系
   - 在 decision 事件中提取分数影响

## 下一步
继续实现连线动画和中心球体动画功能
