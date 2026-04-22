"""
大模型服务
LLM Service - 为智能体提供大模型增强能力
"""
import os
from typing import Dict, List, Optional, Any
from enum import Enum
import json
from dotenv import load_dotenv
import logging

# 配置日志
logger = logging.getLogger(__name__)

# 加载环境变量 - 先加载根目录的.env，再加载backend/.env
_root_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
_backend_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')

# 先加载根目录的.env（优先级低）
if os.path.exists(_root_env_path):
    load_dotenv(_root_env_path)
    
# 再加载backend/.env（优先级高，会覆盖根目录的同名变量）
if os.path.exists(_backend_env_path):
    load_dotenv(_backend_env_path, override=True)


class LLMProvider(Enum):
    """大模型提供商"""
    OPENAI = "openai"
    QWEN = "qwen"  # 通义千问
    TRANSFORMERS = "transformers"  # Transformers 原生推理（本地 GPU）
    LOCAL_QUANTIZED = "local_quantized"  # 本地量化模型（备用方案）
    REMOTE_MODEL = "remote_model"  # 远程模型服务（服务器推理）


class LLMService:
    """大模型服务 - 支持云端API和本地量化模型自动切换"""
    
    def __init__(self, provider: str = "qwen", api_key: Optional[str] = None, enable_fallback: bool = True):
        self.provider = LLMProvider(provider)
        # 特殊处理 Qwen，使用 DASHSCOPE_API_KEY
        if provider == "qwen":
            self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        elif provider == "transformers":
            self.api_key = "local"  # 本地模型不需要API key
        elif provider == "local_quantized":
            self.api_key = "local_quantized"
        else:
            self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")
        
        self.client = None
        self.enabled = False
        self.enable_fallback = enable_fallback  # 是否启用降级到本地模型
        self.local_model_service = None  # 本地量化模型服务
        self.fallback_count = 0  # 降级次数统计
        
        self._initialize()
    
    def _initialize(self):
        """初始化大模型客户端"""
        if self.provider == LLMProvider.OPENAI:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                self.model = "gpt-3.5-turbo"
                self.enabled = True  # 初始化成功
            except ImportError:
                print("⚠️ OpenAI 未安装，请运行: pip install openai")
                self.enabled = False
        
        elif self.provider == LLMProvider.QWEN:
            try:
                from openai import OpenAI
                import httpx
                
                # 从环境变量读取并发配置（支持动态调整）
                max_connections = int(os.getenv("LLM_MAX_CONNECTIONS", "500"))
                max_keepalive = int(os.getenv("LLM_MAX_KEEPALIVE", "100"))
                timeout = float(os.getenv("LLM_TIMEOUT", "120"))
                max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
                
                # 创建支持极高并发的httpx同步客户端（OpenAI需要同步客户端）
                http_client = httpx.Client(
                    limits=httpx.Limits(
                        max_connections=max_connections,
                        max_keepalive_connections=max_keepalive,
                    ),
                    timeout=httpx.Timeout(timeout, connect=15.0),
                )
                
                # 使用 OpenAI 兼容接口
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    http_client=http_client,
                    max_retries=max_retries,
                )
                self.model = "qwen-plus"  # 使用plus版本，性能更强
                self.enable_thinking = True
                self.enabled = True
                
                logger.info(f"✅ Qwen LLM服务初始化成功 (模型: qwen-plus)")
                logger.info(f"   并发配置: max_connections={max_connections}, keepalive={max_keepalive}")
                logger.info(f"   超时配置: timeout={timeout}s, retries={max_retries}")
                logger.info(f"   🚀 极致并发模式已启用，准备处理大规模并发请求")
            except ImportError:
                print("⚠️ OpenAI 未安装，请运行: pip install openai")
                self.enabled = False
        
        elif self.provider == LLMProvider.TRANSFORMERS:
            try:
                from backend.llm.model_config import get_model_hf_name, get_quantization_config, get_current_model_config
                from backend.model_compression.inference_integration import QuantizedModelLoader
                import torch
                
                model_cfg = get_current_model_config()
                model_name = get_model_hf_name()
                quant_config = get_quantization_config()
                loader = QuantizedModelLoader()
                
                # OBR 压缩模型：需要原始模型路径来初始化结构
                obr_weights = os.path.join(model_name, "quantized_model.pt") if os.path.isdir(model_name) else None
                if obr_weights and os.path.exists(obr_weights):
                    print(f"🔧 检测到 OBR 压缩模型，加载中...")
                    original_model = os.environ.get(
                        "LOCAL_BASE_MODEL_PATH",
                        "/root/autodl-tmp/models/base/Qwen3.5-9B"
                    )
                    self.client, self.tokenizer = loader.load_obr_compressed_model(
                        model_dir=model_name,
                        original_model_name=original_model,
                    )
                else:
                    # OBR 压缩模型尚未生成，使用原始 FP16 加载
                    # 运行 compress_base_model.py 生成压缩模型后将自动切换
                    original_model = os.environ.get(
                        "LOCAL_BASE_MODEL_PATH",
                        "/root/autodl-tmp/models/base/Qwen3.5-9B"
                    )
                    print(f"ℹ️  未找到 OBR 压缩模型，使用原始 FP16 模型: {original_model}")
                    self.client, self.tokenizer = loader.load_without_quantization(original_model)
                
                self.model = model_name
                self.enabled = True
                
                vram_gb = torch.cuda.memory_allocated() / 1024**3 if torch.cuda.is_available() else 0
                print(f"✓ Transformers 模型已加载: {model_name} (VRAM: {vram_gb:.2f}GB)")
            except Exception as e:
                print(f"⚠️ Transformers 模型加载失败: {e}")
                self.enabled = False
        
        elif self.provider == LLMProvider.LOCAL_QUANTIZED:
            try:
                from backend.llm.local_quantized_model import get_local_model_service
                self.local_model_service = get_local_model_service()
                self.model = "Qwen3-8B-4bit"
                self.enabled = True
                logger.info("✅ 本地量化模型服务已就绪")
            except Exception as e:
                logger.error(f"⚠️ 本地量化模型初始化失败: {e}")
                self.enabled = False
        
        elif self.provider == LLMProvider.REMOTE_MODEL:
            try:
                from backend.llm.remote_model_client import get_remote_model_client
                self.remote_client = get_remote_model_client()
                self.model = "Remote-Qwen3-8B-4bit"
                self.enabled = self.remote_client.is_available
                if self.enabled:
                    logger.info(f"✅ 远程模型服务已连接: {self.remote_client.base_url}")
                else:
                    logger.warning(f"⚠️ 远程模型服务不可用: {self.remote_client.base_url}")
            except Exception as e:
                logger.error(f"⚠️ 远程模型初始化失败: {e}")
                self.enabled = False
        
        # 如果启用降级，初始化本地量化模型作为备用
        if self.enable_fallback and self.provider != LLMProvider.LOCAL_QUANTIZED:
            try:
                from backend.llm.local_quantized_model import get_local_model_service
                self.local_model_service = get_local_model_service()
                logger.info("✅ 本地量化模型已加载作为备用方案")
            except Exception as e:
                logger.warning(f"⚠️ 本地量化模型备用方案加载失败: {e}")
                self.local_model_service = None
    
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7, 
        response_format: Optional[str] = None, 
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = "auto"
    ) -> str:
        """
        对话接口 - 支持自动降级到本地模型 + Function Calling
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数（0-1，越高越随机）
            response_format: 响应格式，可选 "json_object"
            model: 指定模型名称（可选），如果不指定则使用默认模型
            tools: 工具定义列表（Function Calling）
            tool_choice: 工具选择策略 ("auto" | "none" | {"type": "function", "function": {"name": "..."}})
        
        Returns:
            大模型回复（可能包含工具调用）
        """
        # 临时保存原模型，使用指定模型
        original_model = self.model
        if model:
            self.model = model
        
        try:
            if self.provider == LLMProvider.OPENAI:
                return self._chat_openai(messages, temperature, response_format, tools, tool_choice)
            elif self.provider == LLMProvider.QWEN:
                return self._chat_qwen(messages, temperature, response_format, tools, tool_choice)
            elif self.provider == LLMProvider.TRANSFORMERS:
                return self._chat_transformers(messages, temperature)
            elif self.provider == LLMProvider.LOCAL_QUANTIZED:
                return self._chat_local_quantized(messages, temperature)
            elif self.provider == LLMProvider.REMOTE_MODEL:
                return self._chat_remote_model(messages, temperature)
            else:
                return "大模型未配置"
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            
            # 如果启用了降级且本地模型可用，自动切换
            if self.enable_fallback and self.local_model_service:
                logger.warning(f"⚠️ {self.provider.value} 调用失败，自动切换到本地量化模型")
                self.fallback_count += 1
                try:
                    return self._chat_local_quantized(messages, temperature)
                except Exception as fallback_error:
                    logger.error(f"本地模型降级也失败: {fallback_error}")
                    return f"大模型调用失败: {str(e)}"
            else:
                return f"大模型调用失败: {str(e)}"
        finally:
            # 恢复原模型
            self.model = original_model
    
    async def chat_async(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7, 
        response_format: Optional[str] = None, 
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = "auto"
    ) -> str:
        """
        异步对话接口 - 在线程池中执行同步调用，避免阻塞事件循环
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数（0-1，越高越随机）
            response_format: 响应格式，可选 "json_object"
            model: 指定模型名称（可选），如果不指定则使用默认模型
            tools: 工具定义列表（Function Calling）
            tool_choice: 工具选择策略 ("auto" | "none" | {"type": "function", "function": {"name": "..."}})
        
        Returns:
            大模型回复（可能包含工具调用）
        """
        import asyncio
        # 在线程池中执行同步的 chat 方法，避免阻塞事件循环
        return await asyncio.to_thread(
            self.chat,
            messages,
            temperature,
            response_format,
            model,
            tools,
            tool_choice
        )
    
    def _chat_openai(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float, 
        response_format: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = "auto"
    ) -> str:
        """OpenAI 对话 - 支持Function Calling"""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "timeout": 15
        }
        
        if response_format == "json_object":
            kwargs["response_format"] = {"type": "json_object"}
        
        # 添加Function Calling支持
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice
        
        response = self.client.chat.completions.create(**kwargs)
        
        # 检查是否有工具调用
        if response.choices[0].message.tool_calls:
            # 返回包含工具调用的JSON
            tool_calls = []
            for tool_call in response.choices[0].message.tool_calls:
                tool_calls.append({
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                })
            
            return json.dumps({
                "tool_calls": tool_calls,
                "content": response.choices[0].message.content
            })
        
        return response.choices[0].message.content
    
    def _chat_qwen(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float, 
        response_format: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = "auto"
    ) -> str:
        """通义千问对话（使用 OpenAI 兼容接口）- 支持Function Calling"""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "timeout": 45
        }
        
        # 启用深度思考模式（如果支持）
        if hasattr(self, 'enable_thinking') and self.enable_thinking:
            kwargs["extra_body"] = {"enable_search": False}
        
        # 添加 JSON 响应格式支持
        if response_format == "json_object":
            kwargs["response_format"] = {"type": "json_object"}
        
        # 添加Function Calling支持
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice
        
        # 不在这里捕获异常，让外层的降级逻辑处理
        response = self.client.chat.completions.create(**kwargs)
        
        # 检查是否有工具调用
        if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
            # 返回包含工具调用的JSON
            tool_calls = []
            for tool_call in response.choices[0].message.tool_calls:
                tool_calls.append({
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                })
            
            return json.dumps({
                "tool_calls": tool_calls,
                "content": response.choices[0].message.content
            })
        
        return response.choices[0].message.content
    
    def chat_stream(self, messages: List[Dict[str, str]], temperature: float = 0.7):
        """
        流式对话接口（支持思考过程展示）
        
        Args:
            messages: 消息列表
            temperature: 温度参数
        
        Yields:
            {"type": "thinking", "content": "..."} 或 {"type": "answer", "content": "..."}
        """
        try:
            if self.provider == LLMProvider.QWEN:
                yield from self._chat_qwen_stream(messages, temperature)
            elif self.provider == LLMProvider.TRANSFORMERS:
                yield from self._chat_transformers_stream(messages, temperature)
            else:
                # 其他提供商暂不支持流式
                content = self.chat(messages, temperature)
                yield {"type": "answer", "content": content}
        except Exception as e:
            print(f"LLM 流式调用失败: {e}")
            yield {"type": "error", "content": str(e)}
    
    def _chat_qwen_stream(self, messages: List[Dict[str, str]], temperature: float):
        """通义千问流式对话（支持深度思考模式）"""
        try:
            completion = self.client.chat.completions.create(
                model="qwen-plus",  # 深度思考模型
                messages=messages,
                temperature=temperature,
                stream=True,
                extra_body={"enable_thinking": True},  # 启用深度思考
                timeout=30
            )
            
            is_answering = False  # 是否进入回复阶段
            
            for chunk in completion:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    
                    # 检查思考过程（reasoning_content）
                    if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                        if not is_answering:
                            # 发送思考过程
                            yield {"type": "thinking", "content": delta.reasoning_content}
                    
                    # 检查回答内容（content）
                    if hasattr(delta, "content") and delta.content:
                        if not is_answering:
                            # 第一次收到回答内容，标记进入回复阶段
                            is_answering = True
                        # 发送回答内容
                        yield {"type": "answer", "content": delta.content}
        
        except Exception as e:
            print(f"Qwen深度思考模式失败: {e}")
            # 降级到普通模式
            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    stream=True,
                    timeout=30
                )
                
                for chunk in completion:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, "content") and delta.content:
                            yield {"type": "answer", "content": delta.content}
            except Exception as e2:
                print(f"Qwen普通模式也失败: {e2}")
                yield {"type": "error", "content": str(e2)}
    
    def _chat_transformers(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """Transformers 原生对话"""
        try:
            from backend.llm.model_config import get_inference_config
            
            inference_cfg = get_inference_config()
            
            # 使用 tokenizer 的 chat template
            text = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self.tokenizer(text, return_tensors="pt").to(self.client.device)
            
            import torch
            with torch.no_grad():
                outputs = self.client.generate(
                    **inputs,
                    max_new_tokens=inference_cfg.get("max_new_tokens", 2048),
                    temperature=max(temperature, 0.01),
                    top_p=inference_cfg.get("top_p", 0.9),
                    do_sample=inference_cfg.get("do_sample", True),
                )
            
            # 只取生成的部分
            generated_ids = outputs[0][inputs["input_ids"].shape[-1]:]
            response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
            
            return response
        except Exception as e:
            print(f"Transformers 推理失败: {e}")
            return f"本地模型推理失败: {str(e)}"
    
    def _chat_local_quantized(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """本地量化模型对话"""
        if not self.local_model_service:
            raise RuntimeError("本地量化模型服务不可用")
        
        logger.info("[LLM] 使用本地量化模型")
        return self.local_model_service.chat(messages, temperature=temperature)
    
    def _chat_remote_model(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """远程模型对话"""
        if not hasattr(self, 'remote_client') or not self.remote_client:
            raise RuntimeError("远程模型客户端不可用")
        
        logger.info("[LLM] 使用远程模型")
        return self.remote_client.chat(messages, temperature=temperature)
    
    def get_backend_status(self) -> Dict[str, Any]:
        """获取后端状态信息"""
        status = {
            "primary_backend": self.provider.value,
            "primary_enabled": self.enabled,
            "fallback_enabled": self.enable_fallback,
            "fallback_available": self.local_model_service is not None,
            "fallback_count": self.fallback_count,
        }
        
        if self.local_model_service:
            status["local_model_info"] = self.local_model_service.get_model_info()
        
        return status
    
    def force_use_local_model(self):
        """强制切换到本地模型（用于演示）"""
        if not self.local_model_service:
            raise RuntimeError("本地量化模型不可用")
        
        logger.info("[LLM] 强制切换到本地量化模型")
        self.provider = LLMProvider.LOCAL_QUANTIZED
        self.enabled = True
    
    def _chat_transformers_stream(self, messages: List[Dict[str, str]], temperature: float):
        """Transformers 流式对话"""
        try:
            from transformers import TextIteratorStreamer
            from threading import Thread
            from backend.llm.model_config import get_inference_config
            
            inference_cfg = get_inference_config()
            
            text = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self.tokenizer(text, return_tensors="pt").to(self.client.device)
            
            streamer = TextIteratorStreamer(
                self.tokenizer, skip_prompt=True, skip_special_tokens=True
            )
            
            generation_kwargs = {
                **inputs,
                "max_new_tokens": inference_cfg.get("max_new_tokens", 2048),
                "temperature": max(temperature, 0.01),
                "top_p": inference_cfg.get("top_p", 0.9),
                "do_sample": inference_cfg.get("do_sample", True),
                "streamer": streamer,
            }
            
            thread = Thread(target=self.client.generate, kwargs=generation_kwargs)
            thread.start()
            
            for new_text in streamer:
                if new_text:
                    yield {"type": "answer", "content": new_text}
            
            thread.join()
        except Exception as e:
            print(f"Transformers 流式推理失败: {e}")
            yield {"type": "error", "content": str(e)}
    
    def analyze_health(self, health_data: Dict[str, Any], prediction: Dict[str, Any]) -> str:
        """
        健康分析增强
        
        Args:
            health_data: 健康数据
            prediction: 预测结果
        
        Returns:
            大模型分析结果
        """
        prompt = f"""
你是一个专业的健康顾问。请分析以下健康数据和预测结果，给出专业建议。

当前健康数据：
- 睡眠时间: {health_data.get('sleep_hours', 0)} 小时
- 运动时间: {health_data.get('exercise_minutes', 0)} 分钟
- 压力水平: {health_data.get('stress_level', 0)}/10

预测结果：
- 健康分数: {prediction.get('health_score', 0)}
- 睡眠债务: {prediction.get('sleep_debt', 0)} 小时
- 免疫力: {prediction.get('immunity', 0)}

请提供：
1. 当前健康状况评估（2-3句话）
2. 主要健康风险（如果有）
3. 具体改善建议（3-5条）

要求：专业、简洁、可操作。
"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的健康顾问，擅长分析健康数据并给出实用建议。"},
            {"role": "user", "content": prompt}
        ]
        
        return self.chat(messages, temperature=0.7)
    
    def analyze_time(self, time_data: Dict[str, Any], prediction: Dict[str, Any]) -> str:
        """时间管理分析增强"""
        prompt = f"""
你是一个时间管理专家。请分析以下时间使用数据和预测结果。

当前时间数据：
- 工作时间: {time_data.get('work_hours', 0)} 小时
- 任务数量: {time_data.get('task_count', 0)} 个
- 完成率: {time_data.get('completion_rate', 0)}%

预测结果：
- 效率分数: {prediction.get('efficiency_score', 0)}
- 认知负荷: {prediction.get('cognitive_load', 0)}
- 时间压力: {prediction.get('time_pressure', 0)}

请提供：
1. 时间使用效率评估
2. 存在的时间管理问题
3. 优化建议（3-5条）

要求：实用、具体、可执行。
"""
        
        messages = [
            {"role": "system", "content": "你是一个时间管理专家，擅长帮助人们提高效率。"},
            {"role": "user", "content": prompt}
        ]
        
        return self.chat(messages, temperature=0.7)
    
    def analyze_emotion(self, emotion_data: Dict[str, Any], prediction: Dict[str, Any]) -> str:
        """情绪分析增强"""
        prompt = f"""
你是一个心理咨询师。请分析以下情绪数据和预测结果。

当前情绪数据：
- 心情评分: {emotion_data.get('mood_score', 0)}/10
- 焦虑水平: {emotion_data.get('anxiety_level', 0)}/10
- 压力来源: {emotion_data.get('stress_source', '未知')}

预测结果：
- 情绪稳定性: {prediction.get('emotional_stability', 0)}
- 情绪调节能力: {prediction.get('regulation_ability', 0)}

请提供：
1. 情绪状态评估
2. 潜在情绪风险
3. 情绪管理建议（3-5条）

要求：温和、专业、有同理心。
"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的心理咨询师，擅长情绪分析和心理疏导。"},
            {"role": "user", "content": prompt}
        ]
        
        return self.chat(messages, temperature=0.8)
    
    def analyze_social(self, social_data: Dict[str, Any], prediction: Dict[str, Any]) -> str:
        """社交分析增强"""
        prompt = f"""
你是一个人际关系专家。请分析以下社交数据和预测结果。

当前社交数据：
- 社交时间: {social_data.get('social_hours', 0)} 小时
- 见面人数: {social_data.get('friends_met', 0)} 人
- 社交质量: {social_data.get('interaction_quality', 0)}/10

预测结果：
- 孤独感: {prediction.get('loneliness', 0)}
- 社交满意度: {prediction.get('social_satisfaction', 0)}

请提供：
1. 社交状况评估
2. 人际关系建议（3-5条）

要求：实用、温暖、鼓励性。
"""
        
        messages = [
            {"role": "system", "content": "你是一个人际关系专家，擅长帮助人们改善社交生活。"},
            {"role": "user", "content": prompt}
        ]
        
        return self.chat(messages, temperature=0.7)
    
    def analyze_finance(self, finance_data: Dict[str, Any], prediction: Dict[str, Any]) -> str:
        """财务分析增强"""
        prompt = f"""
你是一个理财顾问。请分析以下财务数据和预测结果。

当前财务数据：
- 收入: ¥{finance_data.get('income', 0)}
- 支出: ¥{finance_data.get('spending', 0)}
- 储蓄: ¥{finance_data.get('savings', 0)}

预测结果：
- 储蓄率: {prediction.get('savings_rate', 0)}%
- 财务健康度: {prediction.get('financial_health', 0)}

请提供：
1. 财务状况评估
2. 理财建议（3-5条）

要求：专业、实用、保守。
"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的理财顾问，擅长个人财务规划。"},
            {"role": "user", "content": prompt}
        ]
        
        return self.chat(messages, temperature=0.6)
    
    def analyze_learning(self, learning_data: Dict[str, Any], prediction: Dict[str, Any]) -> str:
        """学习分析增强"""
        prompt = f"""
你是一个学习教练。请分析以下学习数据和预测结果。

当前学习数据：
- 学习时间: {learning_data.get('study_hours', 0)} 小时
- 完成课程: {learning_data.get('courses_completed', 0)} 门
- 知识掌握度: {learning_data.get('knowledge_retention', 0)}%

预测结果：
- 学习效率: {prediction.get('learning_efficiency', 0)}
- 知识保持率: {prediction.get('retention_rate', 0)}%

请提供：
1. 学习状况评估
2. 学习方法建议（3-5条）

要求：鼓励性、具体、科学。
"""
        
        messages = [
            {"role": "system", "content": "你是一个学习教练，擅长帮助人们提高学习效率。"},
            {"role": "user", "content": prompt}
        ]
        
        return self.chat(messages, temperature=0.7)
    
    def explain_emergent_pattern(self, pattern: Dict[str, Any]) -> str:
        """
        解释涌现模式
        
        Args:
            pattern: 涌现模式数据
        
        Returns:
            大模型解释
        """
        pattern_type = pattern.get('type', 'unknown')
        domains = pattern.get('domains', [])
        description = pattern.get('description', '')
        
        prompt = f"""
你是一个数据分析专家。请用通俗易懂的语言解释以下涌现模式。

模式类型: {pattern_type}
涉及领域: {', '.join(domains)}
系统描述: {description}

请提供：
1. 这个模式是什么意思？（用日常语言解释）
2. 为什么会出现这个模式？
3. 这对用户意味着什么？
4. 应该如何应对？

要求：通俗易懂、有洞察力、可操作。
"""
        
        messages = [
            {"role": "system", "content": "你是一个数据分析专家，擅长用简单的语言解释复杂的模式。"},
            {"role": "user", "content": prompt}
        ]
        
        return self.chat(messages, temperature=0.7)


# 全局 LLM 服务实例
llm_service = None

def get_llm_service() -> Optional[LLMService]:
    """获取 LLM 服务实例"""
    global llm_service
    
    if llm_service is None:
        # 确保加载环境变量
        from dotenv import load_dotenv
        _env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        load_dotenv(_env)
        
        # 从环境变量读取配置
        provider = os.getenv('LLM_PROVIDER', 'qwen')
        
        # 根据provider获取对应的API key
        if provider == 'qwen':
            api_key = os.getenv('DASHSCOPE_API_KEY')
            key_name = 'DASHSCOPE_API_KEY'
        elif provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            key_name = 'OPENAI_API_KEY'
        elif provider == 'transformers':
            # Transformers 本地推理不需要 API key
            api_key = 'local'
            key_name = 'LOCAL_MODEL'
        else:
            api_key = os.getenv(f'{provider.upper()}_API_KEY')
            key_name = f'{provider.upper()}_API_KEY'
        
        if api_key:
            llm_service = LLMService(provider=provider, api_key=api_key)
            print(f"✓ LLM 服务已启用: {provider}")
        else:
            print(f"⚠️ LLM 未配置，请设置 {key_name}")
    
    return llm_service
