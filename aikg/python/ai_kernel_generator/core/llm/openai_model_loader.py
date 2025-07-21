# Copyright 2025 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import httpx
import openai


# 配置文件路径
CONFIG_PATH = Path(__file__).parent / "llm_config.yaml"

# 设置日志
logger = logging.getLogger(__name__)

# 环境变量定义
OLLAMA_API_BASE_ENV = "AIKG_OLLAMA_API_BASE"
VLLM_API_BASE_ENV = "AIKG_VLLM_API_BASE"

# 通用环境变量映射
ENV_VAR_MAPPING = {
    # API Base URL环境变量
    'api_base': {
        'deepseek': 'AIKG_DEEPSEEK_API_BASE',
        'sflow': 'AIKG_SILICONFLOW_API_BASE', 
        'volc': 'AIKG_HUOSHAN_API_BASE',
        'moonshot': 'AIKG_MOONSHOT_API_BASE',
        'ollama': OLLAMA_API_BASE_ENV,
        'vllm': VLLM_API_BASE_ENV,
    },
    # 模型名称环境变量
    'model': {
        'deepseek': 'AIKG_DEEPSEEK_MODEL',
        'sflow': 'AIKG_SILICONFLOW_MODEL',
        'volc': 'AIKG_HUOSHAN_MODEL', 
        'moonshot': 'AIKG_MOONSHOT_MODEL',
        'ollama': 'AIKG_OLLAMA_MODEL',
        'vllm': 'AIKG_VLLM_MODEL',
    },
    # 其他参数环境变量
    'temperature': 'AIKG_TEMPERATURE',
    'max_tokens': 'AIKG_MAX_TOKENS',
    'top_p': 'AIKG_TOP_P',
    'frequency_penalty': 'AIKG_FREQUENCY_PENALTY',
    'presence_penalty': 'AIKG_PRESENCE_PENALTY',
}


def get_model_prefix(model_name: str) -> str:
    """从模型名称获取前缀"""
    if model_name.startswith("deepseek_"):
        return "deepseek"
    elif model_name.startswith("sflow_"):
        return "sflow"
    elif model_name.startswith("volc_"):
        return "volc"
    elif model_name.startswith("moonshot_"):
        return "moonshot"
    elif model_name.startswith("ollama_"):
        return "ollama"
    elif model_name.startswith("vllm_"):
        return "vllm"
    else:
        return "unknown"


def get_env_override(param_name: str, model_prefix: str, default_value: Any = None) -> Any:
    """
    获取环境变量覆盖值
    
    Args:
        param_name: 参数名称 (如 'api_base', 'model', 'temperature')
        model_prefix: 模型前缀 (如 'deepseek', 'sflow')
        default_value: 默认值
        
    Returns:
        环境变量值或默认值
    """
    # 优先查找特定模型的环境变量
    if param_name in ENV_VAR_MAPPING and model_prefix in ENV_VAR_MAPPING[param_name]:
        env_var = ENV_VAR_MAPPING[param_name][model_prefix]
        env_value = os.getenv(env_var)
        if env_value:
            logger.debug(f"使用环境变量 {env_var}={env_value} 覆盖 {param_name}")
            # 尝试转换类型
            if param_name in ['temperature', 'top_p', 'frequency_penalty', 'presence_penalty']:
                try:
                    return float(env_value)
                except ValueError:
                    logger.warning(f"环境变量 {env_var} 值 '{env_value}' 无法转换为float，使用默认值")
                    return default_value
            elif param_name == 'max_tokens':
                try:
                    return int(env_value)
                except ValueError:
                    logger.warning(f"环境变量 {env_var} 值 '{env_value}' 无法转换为int，使用默认值")
                    return default_value
            return env_value
    
    # 查找通用环境变量
    if param_name in ENV_VAR_MAPPING and isinstance(ENV_VAR_MAPPING[param_name], str):
        env_var = ENV_VAR_MAPPING[param_name]
        env_value = os.getenv(env_var)
        if env_value:
            logger.debug(f"使用通用环境变量 {env_var}={env_value} 覆盖 {param_name}")
            # 类型转换逻辑同上
            if param_name in ['temperature', 'top_p', 'frequency_penalty', 'presence_penalty']:
                try:
                    return float(env_value)
                except ValueError:
                    return default_value
            elif param_name == 'max_tokens':
                try:
                    return int(env_value)
                except ValueError:
                    return default_value
            return env_value
    
    return default_value


class OpenAIModelWrapper:
    """OpenAI客户端包装器，统一不同模型的接口"""
    
    def __init__(self, client: openai.AsyncOpenAI, model_name: str, **model_params):
        self.client = client
        self.model_name = model_name
        self.model_params = model_params
        
    async def generate(self, messages: list, **kwargs) -> Dict[str, Any]:
        """生成响应"""
        # 合并参数
        params = {**self.model_params, **kwargs}
        params.pop('api_base', None)  # 移除api_base，它不是chat.completions.create的参数
        
        stream = kwargs.get('stream', False)
        
        if stream:
            # 流式输出
            content = ""
            reasoning_content = ""
            
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True,
                **{k: v for k, v in params.items() if k != 'stream'}
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    chunk_content = chunk.choices[0].delta.content
                    content += chunk_content
                    print(chunk_content, end='', flush=True)
                
                # 处理reasoning_content（如果有的话）
                if chunk.choices and hasattr(chunk.choices[0].delta, 'reasoning_content'):
                    reasoning_chunk = chunk.choices[0].delta.reasoning_content
                    if reasoning_chunk:
                        reasoning_content += reasoning_chunk
                        print(reasoning_chunk, end='', flush=True)
            
            print()  # 换行
            
            return {
                'content': content,
                'reasoning_content': reasoning_content,
                'usage': None
            }
        else:
            # 非流式输出
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **params
            )
            
            return {
                'content': response.choices[0].message.content,
                'reasoning_content': getattr(response.choices[0].message, 'reasoning_content', ''),
                'usage': response.usage.model_dump() if response.usage else None
            }


def create_openai_model(name: Optional[str] = None, config_path: Optional[str] = None) -> OpenAIModelWrapper:
    """
    根据预设名称创建OpenAI模型，优先使用环境变量配置

    Args:
        name: 预设配置名称，如果为None则使用默认配置
        config_path: 配置文件路径，如果为None则使用默认路径

    Returns:
        OpenAIModelWrapper: 创建的模型实例包装器
    """
    # 使用默认路径或指定路径
    config_path = config_path or CONFIG_PATH

    # 检查配置文件是否存在
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件未找到: {config_path}")

    # 加载配置
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 如果未指定预设名称，使用默认预设
    name = name or config.get("default_preset")

    # 检查预设是否存在
    if name not in config:
        available_presets = [k for k in config.keys() if k != "default_preset"]
        raise ValueError(f"预设 '{name}' 未找到。可用预设: {', '.join(available_presets)}")

    # 获取预设配置
    preset_config = config[name].copy()
    
    # 获取模型前缀
    model_prefix = get_model_prefix(name)

    # 在调试级别打印配置
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"使用预设 '{name}' 的配置 (前缀: {model_prefix}):")
        for key, value in preset_config.items():
            if key == "api_key_env":
                logger.debug(f"  {key}: {value} (环境变量)")
            else:
                logger.debug(f"  {key}: {value}")

    # 提取并覆盖基础参数
    api_base = get_env_override("api_base", model_prefix, preset_config.get("api_base", "https://api.openai.com/v1"))
    model_name = get_env_override("model", model_prefix, preset_config.get("model"))
    api_key_env = preset_config.get("api_key_env")
    
    # 移除已处理的参数
    preset_config.pop("api_base", None)
    preset_config.pop("model", None)
    preset_config.pop("api_key_env", None)
    
    # 覆盖其他模型参数
    for param in ['temperature', 'max_tokens', 'top_p', 'frequency_penalty', 'presence_penalty']:
        if param in preset_config:
            preset_config[param] = get_env_override(param, model_prefix, preset_config[param])
    
    # 处理API密钥
    if model_prefix in ["ollama", "vllm"]:
        # 本地模型不需要真实的API key
        api_key = "dummy"
    else:
        # 云端模型需要真实的API key
        if not api_key_env:
            raise ValueError(f"预设 '{name}' 未配置 api_key_env")

        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"API密钥未找到。请设置环境变量 {api_key_env}")

    # 设置默认端点（如果环境变量未设置）
    if not api_base:
        if model_prefix == "ollama":
            api_base = "http://localhost:11434/v1"
        elif model_prefix == "vllm":
            api_base = "http://localhost:8001/v1"
        else:
            api_base = "https://api.openai.com/v1"
    
    logger.debug(f"最终使用的配置: api_base={api_base}, model={model_name}")

    # 设置超时
    timeout = httpx.Timeout(60, read=60 * 20)
    
    # 创建OpenAI客户端
    client = openai.AsyncOpenAI(
        base_url=api_base,
        api_key=api_key,
        http_client=httpx.AsyncClient(verify=False, timeout=timeout)
    )

    return OpenAIModelWrapper(client, model_name, **preset_config)