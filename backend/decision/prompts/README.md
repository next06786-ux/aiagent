# 提示词管理系统

统一管理所有决策相关的提示词，支持版本管理、变量替换和配置化管理。

## 目录结构

```
prompts/
├── prompt_manager.py          # 提示词管理器核心类
├── configs/                   # 提示词配置文件目录
│   ├── info_collection/       # 信息收集阶段提示词
│   │   ├── targeted_question.yaml
│   │   ├── free_talk_followup.yaml
│   │   └── next_question.yaml
│   ├── option_generation/     # 选项生成提示词
│   │   └── generate_options.yaml
│   └── persona_analysis/      # 人格分析提示词
│       ├── rational_analyst.yaml
│       ├── adventurer.yaml
│       ├── pragmatist.yaml
│       ├── idealist.yaml
│       ├── conservative.yaml
│       ├── social_navigator.yaml
│       └── innovator.yaml
└── README.md                  # 本文档
```

## 使用方法

### 1. 基本使用

```python
from backend.decision.prompts.prompt_manager import get_prompt

# 获取提示词
prompt_data = get_prompt(
    category="info_collection",
    prompt_name="targeted_question",
    variables={
        "initial_question": "我应该选择哪个大学？",
        "user_context": "用户背景信息...",
        "user_content": "用户已经说的内容..."
    }
)

# 使用提示词
system_prompt = prompt_data["system"]
user_prompt = prompt_data["user"]
temperature = prompt_data["temperature"]
return_format = prompt_data["return_format"]
```

### 2. 在信息收集器中使用

```python
from backend.decision.prompts.prompt_manager import get_prompt

def _generate_targeted_question(self, session: Dict) -> str:
    """生成针对性问题"""
    prompt_data = get_prompt(
        "info_collection",
        "targeted_question",
        variables={
            "initial_question": session['initial_question'],
            "user_context": session.get("user_context", ""),
            "user_content": "\n".join([
                msg["content"] for msg in session["conversation_history"] 
                if msg["role"] == "user"
            ])
        }
    )
    
    messages = [
        {"role": "system", "content": prompt_data["system"]},
        {"role": "user", "content": prompt_data["user"]}
    ]
    
    response = self.llm_service.chat(
        messages,
        temperature=prompt_data["temperature"]
    )
    return response.strip()
```

### 3. 在人格分析中使用

```python
from backend.decision.prompts.prompt_manager import get_prompt

async def analyze_option(self, option, context, other_personas_views):
    """分析选项"""
    prompt_data = get_prompt(
        "persona_analysis",
        "rational_analyst",  # 或其他人格ID
        variables={
            "emotional_state": self.emotional_state.to_dict(),
            "memory_context": memory_context,
            "shared_facts_text": shared_facts_text,
            "question": context.get('question', ''),
            "background_text": background_text,
            "option_title": option.get('title', ''),
            "option_description": option.get('description', ''),
            "other_views_text": other_views_text,
            "round_num": context.get('round', 0),
            "instruction": context.get('instruction', '')
        }
    )
    
    response = await asyncio.to_thread(
        llm.chat,
        messages=[{"role": "user", "content": prompt_data["user"]}],
        temperature=prompt_data["temperature"],
        response_format=prompt_data["return_format"]
    )
    return json.loads(response)
```

## YAML配置文件格式

```yaml
# 元数据
metadata:
  name: "提示词名称"
  description: "提示词描述"
  category: "类别"
  author: "作者"
  version: "版本号"
  created_at: "创建日期"

# 版本配置
versions:
  default:
    system: |
      系统提示词内容
      支持多行
      可以使用 {variable_name} 进行变量替换
    
    user: |
      用户提示词内容
      支持多行
      可以使用 {variable_name} 进行变量替换
    
    temperature: 0.7
    return_format: "text"  # 或 "json_object"
  
  v2:
    # 可以定义多个版本
    system: "..."
    user: "..."
```

## 变量替换

提示词中使用 `{variable_name}` 格式的占位符，在调用时通过 `variables` 参数传入实际值：

```python
prompt_data = get_prompt(
    "info_collection",
    "targeted_question",
    variables={
        "initial_question": "我的问题",
        "user_context": "背景信息"
    }
)
```

## 版本管理

可以为同一个提示词定义多个版本：

```python
# 使用默认版本
prompt_data = get_prompt("info_collection", "targeted_question")

# 使用指定版本
prompt_data = get_prompt(
    "info_collection",
    "targeted_question",
    version="v2"
)
```

## 重新加载配置

```python
from backend.decision.prompts.prompt_manager import reload_prompts

# 重新加载所有提示词配置
reload_prompts()
```

## 最佳实践

1. **集中管理**：所有提示词都应该放在配置文件中，避免硬编码
2. **版本控制**：重要的提示词修改应该创建新版本，保留旧版本
3. **变量命名**：使用清晰的变量名，如 `user_context` 而不是 `ctx`
4. **文档注释**：在YAML文件中添加注释说明提示词的用途
5. **测试验证**：修改提示词后要测试效果，确保符合预期

## 迁移指南

### 从硬编码迁移到配置文件

**之前（硬编码）：**
```python
prompt = f"""你是一个决策顾问。

用户问题：{question}
用户背景：{context}

请生成一个问题。"""
```

**之后（使用配置）：**
```python
prompt_data = get_prompt(
    "info_collection",
    "targeted_question",
    variables={"question": question, "context": context}
)
```

## 常见问题

### Q: 如何添加新的提示词？
A: 在对应的目录下创建新的YAML文件，按照格式编写配置即可。

### Q: 如何修改现有提示词？
A: 直接编辑对应的YAML文件，修改后调用 `reload_prompts()` 重新加载。

### Q: 变量替换失败怎么办？
A: 检查变量名是否正确，确保传入的 `variables` 字典包含所有需要的变量。

### Q: 如何查看所有可用的提示词？
A: 使用 `get_prompt_manager().list_prompts()` 查看所有已加载的提示词。

## 作者

AI System

## 版本

1.0 (2026-04-19)
