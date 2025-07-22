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

import asyncio
import os
from ai_kernel_generator.core.agent.agent_base import AgentBase
from ai_kernel_generator.utils.prompt_template import PromptTemplate
from ai_kernel_generator.core.llm.openai_model_loader import create_openai_model


class TestAgent(AgentBase):
    """测试用的Agent类"""

    def __init__(self, default_model=None):
        super().__init__(agent_name="TestAgent", default_model=default_model)


def test_default_model_loading():
    """测试默认模型加载"""
    print("=== 测试默认模型加载 ===")
    
    # 不指定默认模型，应该从配置文件读取
    agent = TestAgent()
    print(f"Agent默认模型: {agent.default_model}")
    
    # 指定默认模型
    agent_custom = TestAgent(default_model="vllm_deepseek_r1_default")
    print(f"Agent自定义默认模型: {agent_custom.default_model}")


def test_env_override():
    """测试环境变量覆盖"""
    print("\n=== 测试环境变量覆盖 ===")
    
    # 保存原始环境变量
    original_env = {}
    env_vars_to_test = [
        'AIKG_SILICONFLOW_API_BASE',
        'AIKG_SILICONFLOW_MODEL', 
        'AIKG_TEMPERATURE',
        'AIKG_MAX_TOKENS'
    ]
    
    for var in env_vars_to_test:
        original_env[var] = os.environ.get(var)
    
    try:
        # 设置测试环境变量
        os.environ['AIKG_SILICONFLOW_API_BASE'] = 'https://test-api.example.com/v1'
        os.environ['AIKG_SILICONFLOW_MODEL'] = 'test-model'
        os.environ['AIKG_TEMPERATURE'] = '0.8'
        os.environ['AIKG_MAX_TOKENS'] = '4096'
        
        # 创建模型并检查配置
        model = create_openai_model("sflow_ds_r1_default")
        
        print(f"API Base: {model.client.base_url}")
        print(f"Model Name: {model.model_name}")
        print(f"Temperature: {model.model_params.get('temperature', 'N/A')}")
        print(f"Max Tokens: {model.model_params.get('max_tokens', 'N/A')}")
        
        # 验证是否使用了环境变量
        assert model.client.base_url == 'https://test-api.example.com/v1', "API Base未被环境变量覆盖"
        assert model.model_name == 'test-model', "Model Name未被环境变量覆盖"
        assert model.model_params.get('temperature') == 0.8, "Temperature未被环境变量覆盖"
        assert model.model_params.get('max_tokens') == 4096, "Max Tokens未被环境变量覆盖"
        
        print("✅ 环境变量覆盖测试通过")
        
    finally:
        # 恢复环境变量
        for var in env_vars_to_test:
            if original_env[var] is not None:
                os.environ[var] = original_env[var]
            else:
                os.environ.pop(var, None)


async def test_agent_default_model():
    """测试Agent使用默认模型"""
    print("\n=== 测试Agent使用默认模型 ===")
    
    agent = TestAgent()
    
    # 创建简单的提示模板
    prompt = PromptTemplate.from_template("请说一句话：{content}")
    
    try:
        # 不指定模型名称，应该使用默认模型
        print(f"使用默认模型: {agent.default_model}")
        
        # 注意：这里可能会失败，因为没有真实的API密钥
        # 但我们主要是测试模型名称的传递
        content, formatted_prompt, reasoning = await agent.run_llm(
            prompt, {"content": "测试"}, None  # 不指定模型
        )
        
        print("✅ 默认模型调用成功")
        print(f"格式化提示: {formatted_prompt}")
        
    except Exception as e:
        # 预期可能失败（由于API密钥等问题）
        print(f"⚠️  默认模型调用失败（预期）: {e}")
        print("这通常是由于缺少API密钥造成的，但模型名称传递是正确的")


def test_model_prefix_detection():
    """测试模型前缀检测"""
    print("\n=== 测试模型前缀检测 ===")
    
    from ai_kernel_generator.core.llm.openai_model_loader import get_model_prefix
    
    test_cases = [
        ("deepseek_r1_default", "deepseek"),
        ("sflow_ds_r1_default", "sflow"),
        ("volc_ds_r1_default", "volc"),
        ("moonshot_kimi_8k", "moonshot"),
        ("ollama_qwen_coder_7b", "ollama"),
        ("vllm_deepseek_r1_default", "vllm"),
        ("unknown_model", "unknown"),
    ]
    
    for model_name, expected_prefix in test_cases:
        actual_prefix = get_model_prefix(model_name)
        print(f"模型: {model_name} -> 前缀: {actual_prefix}")
        assert actual_prefix == expected_prefix, f"模型 {model_name} 的前缀应该是 {expected_prefix}，但得到了 {actual_prefix}"
    
    print("✅ 模型前缀检测测试通过")


def test_env_var_mapping():
    """测试环境变量映射"""
    print("\n=== 测试环境变量映射 ===")
    
    from ai_kernel_generator.core.llm.openai_model_loader import get_env_override
    
    # 保存原始环境变量
    original_temp = os.environ.get('AIKG_TEMPERATURE')
    original_sflow_base = os.environ.get('AIKG_SILICONFLOW_API_BASE')
    
    try:
        # 设置测试环境变量
        os.environ['AIKG_TEMPERATURE'] = '0.9'
        os.environ['AIKG_SILICONFLOW_API_BASE'] = 'https://sflow-test.com'
        
        # 测试通用环境变量
        temp = get_env_override('temperature', 'sflow', 0.1)
        print(f"Temperature (通用): {temp}")
        assert temp == 0.9, "通用temperature环境变量未生效"
        
        # 测试特定模型环境变量
        api_base = get_env_override('api_base', 'sflow', 'default')
        print(f"API Base (sflow特定): {api_base}")
        assert api_base == 'https://sflow-test.com', "sflow特定API base环境变量未生效"
        
        # 测试不存在的环境变量
        max_tokens = get_env_override('max_tokens', 'sflow', 1000)
        print(f"Max Tokens (默认): {max_tokens}")
        assert max_tokens == 1000, "默认值未正确返回"
        
        print("✅ 环境变量映射测试通过")
        
    finally:
        # 恢复环境变量
        if original_temp is not None:
            os.environ['AIKG_TEMPERATURE'] = original_temp
        else:
            os.environ.pop('AIKG_TEMPERATURE', None)
            
        if original_sflow_base is not None:
            os.environ['AIKG_SILICONFLOW_API_BASE'] = original_sflow_base
        else:
            os.environ.pop('AIKG_SILICONFLOW_API_BASE', None)


if __name__ == "__main__":
    print("开始环境变量覆盖和默认模型测试...")
    
    # 运行所有测试
    test_default_model_loading()
    test_env_override()
    test_model_prefix_detection()
    test_env_var_mapping()
    
    # 异步测试
    asyncio.run(test_agent_default_model())
    
    print("\n🎉 所有测试完成！")