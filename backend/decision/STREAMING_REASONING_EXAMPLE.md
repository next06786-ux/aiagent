# 流式推理实现示例

## 概述

当前的决策流程已经支持完整的4阶段模式，但推理过程还不是流式输出。本文档展示如何在未来实现流式推理。

## 当前实现

当前的实现中，每个阶段的推理是一次性返回的：

```python
# 独立思考阶段
thinking_result = await persona._phase_independent_thinking(option, context)

# 深度反思阶段
reflection_result = await persona._phase_deep_reflection(
    option, context, other_views, thinking_result
)
```

## 流式推理实现

### 1. 修改阶段方法

在 `DecisionPersona` 类中添加流式分析方法：

```python
async def _analyze_with_streaming(
    self,
    option: Dict[str, Any],
    context: Dict[str, Any],
    skill_results: Dict[str, Any],
    other_views: Optional[Dict[str, Any]],
    phase: str  # 'independent_thinking' or 'deep_reflection'
) -> Dict[str, Any]:
    """
    流式分析 - 实时推送推理过程
    
    Args:
        option: 决策选项
        context: 上下文
        skill_results: 技能执行结果
        other_views: 其他persona的观点（仅深度反思阶段）
        phase: 当前阶段
    
    Returns:
        分析结果
    """
    from backend.llm.llm_service import get_llm_service
    
    llm = get_llm_service()
    if not llm or not llm.enabled:
        # 降级到非流式
        return await self.analyze_option(option, context, other_views or {})
    
    status_callback = context.get('status_callback')
    
    # 构建提示词
    prompt = self._build_analysis_prompt(
        option, context, skill_results, other_views, phase
    )
    
    # 流式调用LLM
    full_response = ""
    chunk_count = 0
    
    async for chunk in llm.chat_stream_async(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    ):
        full_response += chunk
        chunk_count += 1
        
        # 实时推送到前端（每5个chunk推送一次，减少网络开销）
        if status_callback and chunk_count % 5 == 0:
            await status_callback('reasoning_stream', {
                'persona_id': self.persona_id,
                'persona_name': self.name,
                'phase': phase,
                'chunk': chunk,
                'accumulated': full_response,
                'timestamp': __import__('time').time()
            })
    
    # 推送最后的内容
    if status_callback:
        await status_callback('reasoning_stream_complete', {
            'persona_id': self.persona_id,
            'persona_name': self.name,
            'phase': phase,
            'full_content': full_response,
            'timestamp': __import__('time').time()
        })
    
    # 解析结果
    result = self._parse_analysis_result(full_response)
    
    return result

def _build_analysis_prompt(
    self,
    option: Dict[str, Any],
    context: Dict[str, Any],
    skill_results: Dict[str, Any],
    other_views: Optional[Dict[str, Any]],
    phase: str
) -> str:
    """构建分析提示词"""
    
    if phase == 'independent_thinking':
        # 独立思考阶段的提示词
        prompt = f"""
你是{self.name}，{self.description}

请分析以下决策选项：
{option.get('title')}
{option.get('description', '')}

决策问题：{context.get('question', '')}

技能执行结果：
{json.dumps(skill_results, ensure_ascii=False, indent=2)}

请从你的角度进行独立分析，输出JSON格式：
{{
    "stance": "你的立场（支持/反对/中立）",
    "score": 评分（0-100）,
    "confidence": 信心度（0-1）,
    "reasoning": "详细的推理过程",
    "key_points": ["关键要点1", "关键要点2", ...]
}}
"""
    else:  # deep_reflection
        # 深度反思阶段的提示词
        other_views_text = "\n".join([
            f"- {view.get('name')}: {view.get('stance')} ({view.get('score')}分)\n  理由: {view.get('reasoning', '')[:100]}..."
            for view in (other_views or {}).values()
        ])
        
        prompt = f"""
你是{self.name}，{self.description}

你之前的分析：
立场: {context.get('previous_result', {}).get('stance')}
评分: {context.get('previous_result', {}).get('score')}
推理: {context.get('previous_result', {}).get('reasoning', '')[:200]}...

其他persona的观点：
{other_views_text}

补充技能执行结果：
{json.dumps(skill_results, ensure_ascii=False, indent=2)}

请基于其他persona的观点进行深度反思，输出JSON格式：
{{
    "stance": "你的立场（可能调整）",
    "score": 评分（可能调整）,
    "confidence": 信心度（0-1）,
    "reasoning": "深度反思的过程",
    "key_points": ["关键要点1", "关键要点2", ...],
    "stance_changed": true/false
}}
"""
    
    return prompt

def _parse_analysis_result(self, response: str) -> Dict[str, Any]:
    """解析LLM返回的分析结果"""
    try:
        # 尝试解析JSON
        result = json.loads(response)
        return result
    except json.JSONDecodeError:
        # 如果不是JSON，尝试提取关键信息
        logger.warning(f"[{self.name}] 无法解析JSON，使用降级解析")
        
        # 简单的降级解析
        return {
            "stance": "中立",
            "score": 50,
            "confidence": 0.5,
            "reasoning": response,
            "key_points": []
        }
```

### 2. 修改阶段方法调用流式分析

```python
async def _phase_independent_thinking(
    self,
    option: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """独立思考阶段 - 支持流式输出"""
    
    # 智能技能选择
    selected_skills = await self._intelligent_skill_selection(
        option=option,
        context=context,
        phase="independent_thinking"
    )
    
    # 执行技能
    skill_results = {}
    if selected_skills:
        skill_results = await self._execute_selected_skills(
            selected_skills,
            context,
            context.get('status_callback')
        )
    
    # 流式分析
    result = await self._analyze_with_streaming(
        option=option,
        context=context,
        skill_results=skill_results,
        other_views=None,
        phase='independent_thinking'
    )
    
    return result

async def _phase_deep_reflection(
    self,
    option: Dict[str, Any],
    context: Dict[str, Any],
    other_views: Dict[str, Any],
    previous_result: Dict[str, Any]
) -> Dict[str, Any]:
    """深度反思阶段 - 支持流式输出"""
    
    # 智能技能选择
    selected_skills = await self._intelligent_skill_selection(
        option=option,
        context=context,
        phase="deep_reflection",
        other_views=other_views,
        previous_result=previous_result
    )
    
    # 执行补充技能
    skill_results = {}
    if selected_skills:
        skill_results = await self._execute_selected_skills(
            selected_skills,
            context,
            context.get('status_callback')
        )
    
    # 更新上下文
    context_with_previous = context.copy()
    context_with_previous['previous_result'] = previous_result
    
    # 流式分析
    result = await self._analyze_with_streaming(
        option=option,
        context=context_with_previous,
        skill_results=skill_results,
        other_views=other_views,
        phase='deep_reflection'
    )
    
    return result
```

## 前端适配

### 1. WebSocket事件处理

```typescript
// 推理流式输出
interface ReasoningStreamEvent {
  type: 'reasoning_stream';
  persona_id: string;
  persona_name: string;
  phase: 'independent_thinking' | 'deep_reflection';
  chunk: string;  // 文本片段
  accumulated: string;  // 累积文本
  timestamp: number;
}

// 推理流式完成
interface ReasoningStreamCompleteEvent {
  type: 'reasoning_stream_complete';
  persona_id: string;
  persona_name: string;
  phase: string;
  full_content: string;
  timestamp: number;
}

// 事件处理
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'reasoning_stream':
      // 实时更新推理内容
      updateReasoningContent(data.persona_id, data.phase, data.accumulated);
      break;
      
    case 'reasoning_stream_complete':
      // 推理完成，解析结果
      parseReasoningResult(data.persona_id, data.phase, data.full_content);
      break;
  }
};
```

### 2. UI展示

```tsx
// 推理内容组件
function ReasoningContent({ personaId, phase, content }) {
  return (
    <div className="reasoning-content">
      <div className="phase-header">
        {phase === 'independent_thinking' ? '🧠 独立思考' : '🤔 深度反思'}
      </div>
      <div className="reasoning-text">
        {content}
        <span className="cursor-blink">|</span>  {/* 打字机效果 */}
      </div>
    </div>
  );
}

// 状态管理
const [reasoningContent, setReasoningContent] = useState({});

// 更新推理内容
function updateReasoningContent(personaId, phase, content) {
  setReasoningContent(prev => ({
    ...prev,
    [personaId]: {
      ...prev[personaId],
      [phase]: content
    }
  }));
}
```

## 性能优化

### 1. 批量推送

不要每个chunk都推送，而是每N个chunk推送一次：

```python
if chunk_count % 5 == 0:  # 每5个chunk推送一次
    await status_callback('reasoning_stream', {...})
```

### 2. 压缩传输

对于长文本，可以考虑压缩：

```python
import gzip
import base64

compressed = gzip.compress(full_response.encode('utf-8'))
encoded = base64.b64encode(compressed).decode('ascii')

await status_callback('reasoning_stream', {
    'compressed': True,
    'content': encoded
})
```

### 3. 增量更新

只发送新增的内容，而不是累积内容：

```python
last_sent_length = 0

async for chunk in llm.chat_stream_async(...):
    full_response += chunk
    
    # 只发送新增部分
    if len(full_response) - last_sent_length > 50:  # 累积50个字符再发送
        new_content = full_response[last_sent_length:]
        await status_callback('reasoning_stream', {
            'chunk': new_content,
            'position': last_sent_length
        })
        last_sent_length = len(full_response)
```

## 总结

流式推理的实现需要：

1. ✅ LLM服务已支持流式输出（`chat_stream_async`）
2. ⏳ 添加 `_analyze_with_streaming` 方法
3. ⏳ 修改阶段方法调用流式分析
4. ⏳ 前端适配流式事件处理
5. ⏳ UI展示打字机效果

当前版本已经预留了接口，可以在需要时快速实现。
