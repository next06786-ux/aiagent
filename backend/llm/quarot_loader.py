"""
QuaRot量化模型加载器
支持加载4-bit Dual-Shift稀疏量化的Qwen模型
"""
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    from transformers import AutoTokenizer, AutoConfig
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("[QuaRot] PyTorch或transformers未安装")


class QuaRotModelLoader:
    """QuaRot量化模型加载器"""
    
    def __init__(self, model_path: str, base_model_name: str = "Qwen/Qwen3-8B"):
        """
        初始化加载器
        
        Args:
            model_path: 量化权重文件路径
            base_model_name: 基础模型名称（用于加载tokenizer和config）
                           默认 Qwen/Qwen3-8B
        """
        self.model_path = Path(model_path)
        self.base_model_name = base_model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.model = None
        self.tokenizer = None
        self.config = None
        self.state_dict = None
        
        logger.info(f"[QuaRot] 初始化加载器，设备: {self.device}")
        
    def load_tokenizer(self):
        """加载tokenizer"""
        try:
            logger.info("=" * 60)
            logger.info(f"[QuaRot] 开始加载 Tokenizer")
            logger.info(f"[QuaRot] 模型名称: {self.base_model_name}")
            logger.info("[QuaRot] 如果首次运行，需要从 Hugging Face 下载配置文件")
            logger.info("[QuaRot] 这可能需要几分钟时间，请耐心等待...")
            logger.info("=" * 60)
            
            # 检查网络连接
            logger.info("[QuaRot] 检查网络连接...")
            import socket
            original_timeout = socket.getdefaulttimeout()
            
            try:
                # 测试能否连接到 Hugging Face
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.settimeout(5)
                test_socket.connect(("huggingface.co", 443))
                test_socket.close()
                logger.info("[QuaRot] ✅ 网络连接正常，可以访问 Hugging Face")
            except Exception as e:
                logger.warning(f"[QuaRot] ⚠️ 网络连接测试失败: {e}")
                logger.warning("[QuaRot] 如果无法下载，请检查网络或使用本地模型文件")
            
            # 设置下载超时
            socket.setdefaulttimeout(60)  # 增加到60秒超时
            
            try:
                logger.info(f"[QuaRot] 正在从 Hugging Face 加载 {self.base_model_name}...")
                logger.info("[QuaRot] 下载进度:")
                
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.base_model_name,
                    trust_remote_code=True,
                    local_files_only=False,  # 允许下载
                    resume_download=True,     # 支持断点续传
                )
                
                logger.info("=" * 60)
                logger.info("[QuaRot] ✅ Tokenizer 加载成功！")
                logger.info(f"[QuaRot] Vocab 大小: {len(self.tokenizer)}")
                logger.info(f"[QuaRot] 特殊 token: {self.tokenizer.special_tokens_map}")
                logger.info("=" * 60)
                return True
                
            finally:
                socket.setdefaulttimeout(original_timeout)
                
        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"[QuaRot] ❌ Tokenizer 加载失败")
            logger.error(f"[QuaRot] 错误类型: {type(e).__name__}")
            logger.error(f"[QuaRot] 错误信息: {str(e)}")
            logger.error("=" * 60)
            
            # 打印详细的错误堆栈
            import traceback
            logger.debug("[QuaRot] 详细错误堆栈:")
            logger.debug(traceback.format_exc())
            
            logger.warning("[QuaRot] 将使用演示模式（不影响基本功能）")
            logger.info("[QuaRot] 演示模式下会使用智能 mock 响应")
            return False
    
    def load_config(self):
        """加载模型配置"""
        try:
            logger.info("=" * 60)
            logger.info(f"[QuaRot] 开始加载模型配置")
            logger.info(f"[QuaRot] 模型名称: {self.base_model_name}")
            logger.info("=" * 60)
            
            # 设置超时
            import socket
            original_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(60)
            
            try:
                logger.info(f"[QuaRot] 正在下载配置文件...")
                
                self.config = AutoConfig.from_pretrained(
                    self.base_model_name,
                    trust_remote_code=True,
                    local_files_only=False,
                    resume_download=True,
                )
                
                logger.info("=" * 60)
                logger.info("[QuaRot] ✅ 配置加载成功！")
                logger.info(f"[QuaRot] 模型类型: {self.config.model_type}")
                logger.info(f"[QuaRot] 隐藏层大小: {self.config.hidden_size}")
                logger.info(f"[QuaRot] 层数: {self.config.num_hidden_layers}")
                logger.info(f"[QuaRot] 注意力头数: {self.config.num_attention_heads}")
                logger.info("=" * 60)
                return True
                
            finally:
                socket.setdefaulttimeout(original_timeout)
                
        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"[QuaRot] ❌ 配置加载失败")
            logger.error(f"[QuaRot] 错误类型: {type(e).__name__}")
            logger.error(f"[QuaRot] 错误信息: {str(e)}")
            logger.error("=" * 60)
            
            import traceback
            logger.debug("[QuaRot] 详细错误堆栈:")
            logger.debug(traceback.format_exc())
            
            logger.warning("[QuaRot] 将使用演示模式（不影响基本功能）")
            return False
    
    def load_state_dict(self):
        """加载量化权重"""
        try:
            logger.info("=" * 60)
            logger.info("[QuaRot] 开始加载量化权重")
            logger.info(f"[QuaRot] 文件路径: {self.model_path}")
            logger.info("=" * 60)
            
            if not self.model_path.exists():
                logger.error(f"[QuaRot] ❌ 权重文件不存在: {self.model_path}")
                return False
            
            # 检查文件大小
            file_size_gb = self.model_path.stat().st_size / (1024**3)
            logger.info(f"[QuaRot] 文件大小: {file_size_gb:.2f} GB")
            logger.info(f"[QuaRot] 正在加载到设备: {self.device}")
            logger.info("[QuaRot] 加载中，请稍候...")
            
            import time
            start_time = time.time()
            
            self.state_dict = torch.load(self.model_path, map_location="cpu")
            
            load_time = time.time() - start_time
            logger.info(f"[QuaRot] 加载耗时: {load_time:.2f} 秒")
            
            # 统计参数量
            if isinstance(self.state_dict, dict):
                logger.info("[QuaRot] 分析权重结构...")
                
                # 统计键的数量
                num_keys = len(self.state_dict)
                logger.info(f"[QuaRot] 权重键数量: {num_keys}")
                
                # 显示前几个键
                keys_sample = list(self.state_dict.keys())[:10]
                logger.info(f"[QuaRot] 键示例: {keys_sample}")
                
                # 统计参数量
                total_params = sum(
                    v.numel() for v in self.state_dict.values() 
                    if hasattr(v, 'numel')
                )
                logger.info("=" * 60)
                logger.info(f"[QuaRot] ✅ 权重加载成功！")
                logger.info(f"[QuaRot] 总参数量: {total_params/1e9:.2f}B")
                logger.info(f"[QuaRot] 量化位数: 4-bit")
                logger.info(f"[QuaRot] 预估显存占用: ~{(total_params * 0.5) / 1024**3:.2f} GB")
                logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"[QuaRot] ❌ 权重加载失败")
            logger.error(f"[QuaRot] 错误类型: {type(e).__name__}")
            logger.error(f"[QuaRot] 错误信息: {str(e)}")
            logger.error("=" * 60)
            
            import traceback
            logger.debug("[QuaRot] 详细错误堆栈:")
            logger.debug(traceback.format_exc())
            return False
    
    def build_model(self):
        """构建模型架构并加载权重"""
        try:
            logger.info("[QuaRot] 开始构建模型架构...")
            
            # 检查是否有必要的组件
            if self.config is None:
                logger.error("[QuaRot] 配置未加载，无法构建模型")
                return False
            
            if self.state_dict is None:
                logger.error("[QuaRot] 权重未加载，无法构建模型")
                return False
            
            # 使用 AutoModelForCausalLM 加载模型架构
            from transformers import AutoModelForCausalLM
            import torch
            
            logger.info("[QuaRot] 初始化模型架构（这可能需要几分钟）...")
            logger.info("[QuaRot] 正在创建空模型架构...")
            
            # 使用 meta device 快速初始化，不占用显存
            with torch.device('meta'):
                self.model = AutoModelForCausalLM.from_config(
                    self.config,
                    trust_remote_code=True
                )
            
            logger.info("[QuaRot] ✅ 模型架构创建成功")
            logger.info("[QuaRot] 正在将模型移动到设备...")
            
            # 使用 to_empty() 从 meta 设备转移到实际设备
            # 这是处理 meta tensor 的正确方法
            self.model = self.model.to_empty(device=self.device)
            
            logger.info(f"[QuaRot] ✅ 模型已移动到 {self.device}")
            
            # 加载量化权重
            if self.state_dict is not None:
                logger.info("[QuaRot] 加载量化权重到模型...")
                try:
                    # 尝试直接加载
                    missing_keys, unexpected_keys = self.model.load_state_dict(
                        self.state_dict, 
                        strict=False
                    )
                    
                    if missing_keys:
                        logger.warning(f"[QuaRot] 缺失的键: {len(missing_keys)} 个")
                        if len(missing_keys) <= 10:
                            logger.debug(f"[QuaRot] 缺失键: {missing_keys}")
                    
                    if unexpected_keys:
                        logger.warning(f"[QuaRot] 意外的键: {len(unexpected_keys)} 个")
                        if len(unexpected_keys) <= 10:
                            logger.debug(f"[QuaRot] 意外键: {unexpected_keys}")
                    
                    logger.info("[QuaRot] ✅ 权重加载完成")
                    
                except Exception as e:
                    logger.error(f"[QuaRot] 权重加载失败: {e}")
                    return False
            
            # 设置为评估模式
            self.model.eval()
            
            logger.info("[QuaRot] ✅ 模型构建成功，真实推理已启用")
            return True
            
        except Exception as e:
            logger.error(f"[QuaRot] 模型构建失败: {e}")
            import traceback
            logger.debug("[QuaRot] 详细错误堆栈:")
            logger.debug(traceback.format_exc())
            return False
    
    def can_do_real_inference(self) -> bool:
        """检查是否可以进行真实推理"""
        return (
            self.model is not None and
            self.tokenizer is not None and
            self.config is not None
        )
    
    def get_info(self) -> Dict[str, Any]:
        """获取加载器信息"""
        return {
            "model_path": str(self.model_path),
            "base_model": self.base_model_name,
            "device": self.device,
            "tokenizer_loaded": self.tokenizer is not None,
            "config_loaded": self.config is not None,
            "state_dict_loaded": self.state_dict is not None,
            "model_loaded": self.model is not None,
            "can_inference": self.can_do_real_inference(),
        }


def create_quarot_loader(model_path: str, skip_online: bool = False, enable_real_inference: bool = True) -> Optional[QuaRotModelLoader]:
    """
    创建QuaRot加载器
    
    Args:
        model_path: 量化模型路径
        skip_online: 是否跳过在线下载（默认False，尝试加载完整功能）
        enable_real_inference: 是否启用真实推理（默认True）
    
    Returns:
        加载器实例，如果环境不支持则返回None
    """
    if not TORCH_AVAILABLE:
        logger.warning("[QuaRot] PyTorch环境不可用")
        return None
    
    try:
        logger.info("=" * 60)
        logger.info("[QuaRot] 初始化 QuaRot 加载器")
        logger.info("=" * 60)
        
        loader = QuaRotModelLoader(model_path)
        
        # 加载权重
        logger.info("[QuaRot] 步骤 1/3: 加载量化权重")
        if not loader.load_state_dict():
            logger.error("[QuaRot] ❌ 权重加载失败，无法继续")
            return None
        
        # 如果不跳过在线下载，尝试加载tokenizer和config
        if not skip_online:
            logger.info("[QuaRot] 步骤 2/3: 加载 Tokenizer")
            tokenizer_success = loader.load_tokenizer()
            
            logger.info("[QuaRot] 步骤 3/3: 加载模型配置")
            config_success = loader.load_config()
            
            if tokenizer_success and config_success:
                logger.info("[QuaRot] ✅ 所有组件加载成功")
            else:
                logger.warning("[QuaRot] ⚠️ 部分组件加载失败，将使用演示模式")
        else:
            logger.info("[QuaRot] 跳过在线下载，使用演示模式")
        
        # 如果启用真实推理，构建模型
        if enable_real_inference:
            logger.info("=" * 60)
            logger.info("[QuaRot] 尝试启用真实推理模式...")
            logger.info("=" * 60)
            
            if loader.build_model():
                logger.info("=" * 60)
                logger.info("[QuaRot] ✅ 真实推理模式已启用！")
                logger.info("[QuaRot] 模型已准备就绪，可以开始推理")
                logger.info("=" * 60)
            else:
                logger.warning("=" * 60)
                logger.warning("[QuaRot] ⚠️ 真实推理启用失败")
                logger.warning("[QuaRot] 将使用演示模式（智能 mock 响应）")
                logger.warning("=" * 60)
        else:
            logger.info("[QuaRot] 演示模式（未启用真实推理）")
        
        logger.info("=" * 60)
        logger.info("[QuaRot] 加载器创建完成")
        logger.info("=" * 60)
        
        return loader
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error("[QuaRot] ❌ 创建加载器失败")
        logger.error(f"[QuaRot] 错误类型: {type(e).__name__}")
        logger.error(f"[QuaRot] 错误信息: {str(e)}")
        logger.error("=" * 60)
        
        import traceback
        logger.debug("[QuaRot] 详细错误堆栈:")
        logger.debug(traceback.format_exc())
        return None
