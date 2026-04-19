"""
提示词管理系统

统一管理所有决策相关的提示词，支持：
1. 从YAML配置文件加载提示词
2. 变量替换和模板渲染
3. 提示词版本管理
4. 缓存机制

作者: AI System
版本: 1.0
日期: 2026-04-18
"""
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PromptManager:
    """提示词管理器"""
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        初始化提示词管理器
        
        Args:
            prompts_dir: 提示词配置文件目录，默认为当前目录下的 prompts/
        """
        if prompts_dir is None:
            prompts_dir = os.path.join(os.path.dirname(__file__), "configs")
        
        self.prompts_dir = Path(prompts_dir)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_all_prompts()
        
        logger.info(f"✅ 提示词管理器已初始化: {self.prompts_dir}")
    
    def _load_all_prompts(self):
        """加载所有提示词配置文件"""
        if not self.prompts_dir.exists():
            logger.warning(f"提示词目录不存在: {self.prompts_dir}")
            return
        
        loaded_count = 0
        for yaml_file in self.prompts_dir.glob("**/*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    
                    # 使用相对路径作为key，统一使用正斜杠
                    relative_path = yaml_file.relative_to(self.prompts_dir)
                    config_key = str(relative_path.with_suffix('')).replace('\\', '/')
                    
                    self._cache[config_key] = config
                    loaded_count += 1
                    logger.info(f"✓ 加载提示词: {config_key}")
            
            except Exception as e:
                logger.error(f"✗ 加载提示词配置失败 {yaml_file}: {e}")
        
        logger.info(f"✅ 提示词管理器加载完成: {loaded_count} 个配置文件")
    
    def get_prompt(
        self,
        category: str,
        prompt_name: str,
        variables: Optional[Dict[str, Any]] = None,
        version: str = "default"
    ) -> str:
        """
        获取提示词
        
        Args:
            category: 提示词类别（如 info_collection, persona_analysis）
            prompt_name: 提示词名称（如 targeted_question, rational_analyst）
            variables: 变量字典，用于替换提示词中的占位符
            version: 版本号，默认为 "default"
        
        Returns:
            渲染后的提示词
        
        Example:
            prompt = manager.get_prompt(
                "info_collection",
                "targeted_question",
                variables={"user_context": "...", "question": "..."}
            )
        """
        config_key = f"{category}/{prompt_name}"
        
        # 从缓存获取配置
        if config_key not in self._cache:
            logger.warning(f"提示词配置不存在: {config_key}")
            logger.debug(f"可用的配置: {list(self._cache.keys())}")
            return self._get_fallback_prompt(category, prompt_name)
        
        config = self._cache[config_key]
        
        # 获取指定版本的提示词
        if version not in config.get("versions", {}):
            logger.warning(f"版本不存在: {version}，使用默认版本")
            version = "default"
        
        prompt_data = config["versions"].get(version, {})
        
        # 获取系统提示词和用户提示词
        system_prompt = prompt_data.get("system", "")
        user_prompt = prompt_data.get("user", "")
        
        # 变量替换
        if variables:
            system_prompt = self._render_template(system_prompt, variables)
            user_prompt = self._render_template(user_prompt, variables)
        
        # 返回格式
        return_format = prompt_data.get("return_format", "text")
        
        return {
            "system": system_prompt,
            "user": user_prompt,
            "return_format": return_format,
            "temperature": prompt_data.get("temperature", 0.7),
            "metadata": config.get("metadata", {})
        }
    
    def _render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """
        渲染模板，替换变量
        
        支持的占位符格式：
        - {variable_name}
        - {{variable_name}}
        
        Args:
            template: 模板字符串
            variables: 变量字典
        
        Returns:
            渲染后的字符串
        """
        try:
            # 使用 format 方法替换变量
            # 先处理双花括号（转义）
            rendered = template
            for key, value in variables.items():
                # 处理 None 值
                if value is None:
                    value = ""
                # 转换为字符串
                value_str = str(value)
                # 替换占位符
                rendered = rendered.replace(f"{{{key}}}", value_str)
                rendered = rendered.replace(f"{{{{{key}}}}}", value_str)
            
            return rendered
        
        except Exception as e:
            logger.error(f"模板渲染失败: {e}")
            return template
    
    def _get_fallback_prompt(self, category: str, prompt_name: str) -> Dict[str, Any]:
        """获取降级提示词"""
        fallback_prompts = {
            "info_collection": {
                "targeted_question": {
                    "system": "你是一个决策顾问，请提出一个有针对性的问题。",
                    "user": "请生成一个问题。",
                    "return_format": "text",
                    "temperature": 0.7
                },
                "free_talk_followup": {
                    "system": "你是一个决策顾问，请自然地跟进用户的表达。",
                    "user": "请生成一个跟进问题。",
                    "return_format": "text",
                    "temperature": 0.8
                }
            },
            "option_generation": {
                "generate_options": {
                    "system": "你是一个决策顾问，请生成决策选项。",
                    "user": "请生成3个决策选项。",
                    "return_format": "json_object",
                    "temperature": 0.7
                }
            }
        }
        
        return fallback_prompts.get(category, {}).get(prompt_name, {
            "system": "你是一个AI助手。",
            "user": "请帮助用户。",
            "return_format": "text",
            "temperature": 0.7
        })
    
    def reload(self):
        """重新加载所有提示词配置"""
        self._cache.clear()
        self._load_all_prompts()
        logger.info("✅ 提示词配置已重新加载")
    
    def list_prompts(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        列出所有提示词
        
        Args:
            category: 可选，只列出指定类别的提示词
        
        Returns:
            提示词列表
        """
        if category:
            return {
                k: v for k, v in self._cache.items()
                if k.startswith(category + "/")
            }
        return self._cache
    
    def get_metadata(self, category: str, prompt_name: str) -> Dict[str, Any]:
        """
        获取提示词元数据
        
        Args:
            category: 提示词类别
            prompt_name: 提示词名称
        
        Returns:
            元数据字典
        """
        config_key = f"{category}/{prompt_name}"
        
        if config_key not in self._cache:
            return {}
        
        return self._cache[config_key].get("metadata", {})


# 全局单例
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """获取全局提示词管理器实例"""
    global _prompt_manager
    
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    
    return _prompt_manager


def reload_prompts():
    """重新加载提示词配置"""
    global _prompt_manager
    
    if _prompt_manager is not None:
        _prompt_manager.reload()
    else:
        _prompt_manager = PromptManager()


# 便捷函数
def get_prompt(
    category: str,
    prompt_name: str,
    variables: Optional[Dict[str, Any]] = None,
    version: str = "default"
) -> Dict[str, Any]:
    """
    便捷函数：获取提示词
    
    Example:
        prompt = get_prompt(
            "info_collection",
            "targeted_question",
            variables={"user_context": "...", "question": "..."}
        )
    """
    manager = get_prompt_manager()
    return manager.get_prompt(category, prompt_name, variables, version)
