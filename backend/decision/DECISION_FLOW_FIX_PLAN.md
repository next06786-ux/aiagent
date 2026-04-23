# 决策流程修复方案

## 问题分析

当前实现的问题：
1. 流程不完整：每轮只有"独立思考"或"深度反思"，缺少完整的4个阶段
2. 观察他人的时机不对：应该在独立思考后、深度反思前观察他人
3. 决策阶段缺失：每轮应该有一个明确的决策输出
4. 流式显示不完整：文字推理应该流式显示

## 正确的流程

### 每一轮的完整流程（4个阶段）

```
第N轮：
├── 1. 独立思考阶段
│   ├── 智能选择技能
│   ├── 执行技能
│   ├── 基于技能结果进行分析
│   └── 流式输出推理过程
│
├── 2. 查看他人观点阶段
│   ├── 从共享存储读取其他persona的观点
│   └── 展示其他persona的立场和理由
│
├── 3. 深度反思阶段
│   ├── 基于他人观点进行反思
│   ├── 智能选择补充技能（如果需要）
│   ├── 执行补充技能
│   ├── 调整自己的立场
│   └── 流式输出反思过程
│
└── 4. 决策阶段
    ├── 做出当前轮次的决策
    ├── 输出立场、评分、信心度
    └── 写入共享存储供其他persona查看
```

### 多轮执行

```
轮次1 → 轮次2 → ... → 轮次N → 最终结论
```

## 修复方案

### 1. 修改 `_run_persona_with_sharing` 方法

```python
async def _run_persona_with_sharing(
    self,
    persona: DecisionPersona,
    persona_id: str,
    option: Dict[str, Any],
    context: Dict[str, Any],
    rounds: int,
    shared_views: Dict[str, Any],
    shared_views_lock: asyncio.Lock
) -> Dict[str, Any]:
    """
    运行智能体生命周期 - 完整的4阶段流程
    
    每一轮包含：
    1. 独立思考（可执行技能，流式输出）
    2. 查看他人观点
    3. 深度反思（可执行技能，流式输出）
    4. 决策（输出立场和评分）
    """
    
    final_result = None
    status_callback = context.get('status_callback')
    
    for round_num in range(1, rounds + 1):
        # 推送轮次开始
        if status_callback:
            await status_callback('round_start', {
                'persona_id': persona_id,
                'round': round_num,
                'total_rounds': rounds
            })
        
        # ========== 阶段1: 独立思考 ==========
        thinking_result = await persona._phase_independent_thinking_streaming(
            option, context, round_num
        )
        
        # ========== 阶段2: 查看他人观点 ==========
        other_views = await persona._phase_observe_others(
            option, context, shared_views, shared_views_lock
        )
        
        # ========== 阶段3: 深度反思 ==========
        reflection_result = await persona._phase_deep_reflection_streaming(
            option, context, round_num, other_views, thinking_result
        )
        
        # ========== 阶段4: 决策 ==========
        decision_result = await persona._phase_make_decision(
            option, context, round_num, thinking_result, reflection_result
        )
        
        # 写入共享存储
        async with shared_views_lock:
            shared_views[persona_id] = {
                'name': persona.name,
                'round': round_num,
                'stance': decision_result.get('stance'),
                'score': decision_result.get('score'),
                'confidence': decision_result.get('confidence'),
                'reasoning': decision_result.get('reasoning'),
                'key_points': decision_result.get('key_points')
            }
        
        final_result = decision_result
        
        # 推送轮次完成
        if status_callback:
            await status_callback('round_complete', {
                'persona_id': persona_id,
                'round': round_num
            })
    
    return final_result
```

### 2. 新增流式输出方法

```python
async def _phase_independent_thinking_streaming(
    self,
    option: Dict[str, Any],
    context: Dict[str, Any],
    round_num: int
) -> Dict[str, Any]:
    """
    独立思考阶段 - 流式输出
    """
    status_callback = context.get('status_callback')
    
    # 推送阶段开始
    if status_callback:
        await status_callback('phase_start', {
            'persona_id': self.persona_id,
            'phase': 'independent_thinking',
            'round': round_num
        })
    
    # 1. 智能选择技能
    selected_skills = await self._intelligent_skill_selection(
        option, context, "independent_thinking"
    )
    
    # 2. 执行技能
    skill_results = {}
    if selected_skills:
        skill_results = await self._execute_selected_skills(
            selected_skills, context, status_callback
        )
    
    # 3. 流式分析
    result = await self._analyze_with_streaming(
        option, context, skill_results, None, status_callback
    )
    
    # 推送阶段完成
    if status_callback:
        await status_callback('phase_complete', {
            'persona_id': self.persona_id,
            'phase': 'independent_thinking',
            'round': round_num
        })
    
    return result

async def _phase_deep_reflection_streaming(
    self,
    option: Dict[str, Any],
    context: Dict[str, Any],
    round_num: int,
    other_views: Dict[str, Any],
    thinking_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    深度反思阶段 - 流式输出
    """
    status_callback = context.get('status_callback')
    
    # 推送阶段开始
    if status_callback:
        await status_callback('phase_start', {
            'persona_id': self.persona_id,
            'phase': 'deep_reflection',
            'round': round_num,
            'other_views_count': len(other_views)
        })
    
    # 1. 智能选择补充技能
    selected_skills = await self._intelligent_skill_selection(
        option, context, "deep_reflection", other_views, thinking_result
    )
    
    # 2. 执行补充技能
    skill_results = {}
    if selected_skills:
        skill_results = await self._execute_selected_skills(
            selected_skills, context, status_callback
        )
    
    # 3. 流式反思
    result = await self._analyze_with_streaming(
        option, context, skill_results, other_views, status_callback
    )
    
    # 推送阶段完成
    if status_callback:
        await status_callback('phase_complete', {
            'persona_id': self.persona_id,
            'phase': 'deep_reflection',
            'round': round_num
        })
    
    return result

async def _analyze_with_streaming(
    self,
    option: Dict[str, Any],
    context: Dict[str, Any],
    skill_results: Dict[str, Any],
    other_views: Optional[Dict[str, Any]],
    status_callback: Optional[Callable]
) -> Dict[str, Any]:
    """
    流式分析 - 实时推送推理过程
    """
    from backend.llm.llm_service import get_llm_service
    
    llm = get_llm_service()
    if not llm or not llm.enabled:
        # 降级到非流式
        return await self.analyze_option(option, context, other_views or {})
    
    # 构建提示词
    prompt = self._build_analysis_prompt(
        option, context, skill_results, other_views
    )
    
    # 流式调用LLM
    full_response = ""
    async for chunk in llm.chat_stream_async(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    ):
        full_response += chunk
        
        # 实时推送到前端
        if status_callback:
            await status_callback('reasoning_stream', {
                'persona_id': self.persona_id,
                'chunk': chunk,
                'accumulated': full_response
            })
    
    # 解析结果
    result = self._parse_analysis_result(full_response)
    
    return result
```

### 3. 前端WebSocket事件类型

```typescript
// 新增事件类型
type DecisionEvent = 
  | { type: 'round_start', round: number, total_rounds: number }
  | { type: 'phase_start', phase: 'independent_thinking' | 'observe_others' | 'deep_reflection' | 'decision' }
  | { type: 'reasoning_stream', persona_id: string, chunk: string }  // 流式推理
  | { type: 'skill_execution', persona_id: string, skill: string }
  | { type: 'observation', persona_id: string, observed_count: number }
  | { type: 'phase_complete', phase: string }
  | { type: 'round_complete', round: number }
```

## 实施步骤

1. 修改 `DecisionPersona` 类，添加流式方法
2. 修改 `PersonaCouncil._run_persona_with_sharing` 方法
3. 更新WebSocket事件推送
4. 前端适配新的事件流
5. 测试完整流程

## 预期效果

- 每个persona执行N轮完整的4阶段流程
- 推理过程实时流式显示在前端
- 技能执行在独立思考和深度反思阶段
- 每轮都有明确的决策输出
- 前后端实时同步
