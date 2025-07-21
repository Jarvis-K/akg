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

# 环境变量
OLLAMA_API_BASE_ENV = "AIKG_OLLAMA_API_BASE"
VLLM_API_BASE_ENV = "AIKG_VLLM_API_BASE"


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
    根据预设名称创建OpenAI模型

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

    # 在调试级别打印配置
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"使用预设 '{name}' 的配置:")
        for key, value in preset_config.items():
            if key == "api_key_env":
                logger.debug(f"  {key}: {value} (环境变量)")
            else:
                logger.debug(f"  {key}: {value}")

    # 提取基础参数
    api_base = preset_config.pop("api_base", "https://api.openai.com/v1")
    model_name = preset_config.pop("model")
    api_key_env = preset_config.pop("api_key_env", None)
    
    # 处理不同类型的模型
    if name.startswith("ollama_"):
        # Ollama模型
        if OLLAMA_API_BASE_ENV in os.environ:
            api_base = os.environ[OLLAMA_API_BASE_ENV]
            logger.debug(f"使用环境变量 {OLLAMA_API_BASE_ENV} 覆盖 api_base: {api_base}")
        else:
            api_base = "http://localhost:11434/v1"
            logger.debug(f"未设置环境变量 {OLLAMA_API_BASE_ENV}，使用默认 api_base: {api_base}")
        
        api_key = "dummy"  # Ollama不需要真实的API key
        
    elif name.startswith("vllm_"):
        # VLLM模型
        if VLLM_API_BASE_ENV in os.environ:
            api_base = os.environ[VLLM_API_BASE_ENV]
            logger.debug(f"使用环境变量 {VLLM_API_BASE_ENV} 覆盖 api_base: {api_base}")
        else:
            api_base = "http://localhost:8001/v1"
            logger.debug(f"未设置环境变量 {VLLM_API_BASE_ENV}，使用默认 api_base: {api_base}")
        
        api_key = "dummy"  # VLLM不需要真实的API key
        
    else:
        # 其他模型（需要真实的API key）
        if not api_key_env:
            raise ValueError(f"预设 '{name}' 未配置 api_key_env")

        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"API密钥未找到。请设置环境变量 {api_key_env}")

    # 设置超时
    timeout = httpx.Timeout(60, read=60 * 20)
    
    # 创建OpenAI客户端
    client = openai.AsyncOpenAI(
        base_url=api_base,
        api_key=api_key,
        http_client=httpx.AsyncClient(verify=False, timeout=timeout)
    )

    return OpenAIModelWrapper(client, model_name, **preset_config)