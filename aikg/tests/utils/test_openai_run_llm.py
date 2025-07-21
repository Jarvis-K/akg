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
from ai_kernel_generator.core.agent.agent_base_openai import AgentBase
from ai_kernel_generator.utils.prompt_template import PromptTemplate


class TestAgent(AgentBase):
    """测试用的Agent类，继承自AgentBase（OpenAI版本）"""

    def __init__(self):
        super().__init__(agent_name="TestAgent")


async def test_simple_run_llm():
    """简单的OpenAI接口测试"""
    # 创建测试Agent
    agent = TestAgent()

    # 自定义prompt string
    prompt_string = "你好，请简单介绍一下自己"

    # 创建提示模板
    prompt = PromptTemplate.from_template(prompt_string)

    # 准备输入
    input_data = {}

    # 指定model name
    model_name = "vllm_deepseek_r1_default"

    # 跑run_llm
    content, formatted_prompt, reasoning_content = await agent.run_llm(
        prompt, input_data, model_name
    )

    # 输出结果
    print(f"\n=== OpenAI接口run_llm测试 ===")
    print(f"Prompt: {formatted_prompt}")
    if reasoning_content:
        print(f"Reasoning: {reasoning_content}")
    print(f"Model: {model_name}")
    print(f"Output: {content}")
    print("===================")


async def test_template_with_variables():
    """测试带变量的模板"""
    # 创建测试Agent
    agent = TestAgent()

    # 带变量的prompt
    prompt_string = "你好，我的名字是{name}，我想了解关于{topic}的信息。"

    # 创建提示模板
    prompt = PromptTemplate.from_template(prompt_string)

    # 准备输入
    input_data = {
        "name": "小明",
        "topic": "人工智能"
    }

    # 指定model name
    model_name = "sflow_ds_r1_default"

    # 跑run_llm
    content, formatted_prompt, reasoning_content = await agent.run_llm(
        prompt, input_data, model_name
    )

    # 输出结果
    print(f"\n=== 模板变量测试 ===")
    print(f"Prompt: {formatted_prompt}")
    if reasoning_content:
        print(f"Reasoning: {reasoning_content}")
    print(f"Model: {model_name}")
    print(f"Output: {content}")
    print("===================")


async def test_default_model():
    """测试使用默认模型"""
    # 创建测试Agent
    agent = TestAgent()

    # 自定义prompt string
    prompt_string = "你好，请简单介绍一下自己"

    # 创建提示模板
    prompt = PromptTemplate.from_template(prompt_string)

    # 准备输入
    input_data = {}

    print(f"\n=== 默认模型测试 ===")
    print(f"Agent默认模型: {agent.default_model}")

    try:
        # 不指定model_name，使用默认模型
        content, formatted_prompt, reasoning_content = await agent.run_llm(
            prompt, input_data  # 不传model_name参数
        )

        # 输出结果
        print(f"Prompt: {formatted_prompt}")
        if reasoning_content:
            print(f"Reasoning: {reasoning_content}")
        print(f"Output: {content}")
        print("===================")
        
    except Exception as e:
        print(f"默认模型测试失败（可能是API密钥问题）: {e}")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_simple_run_llm())
    asyncio.run(test_template_with_variables())
    asyncio.run(test_default_model())