# 快速开始：使用OpenAI接口

## 安装依赖

```bash
cd aikg
pip install -r requirements.txt
```

新的依赖包括：
- `openai`: OpenAI官方Python客户端
- `pydantic`: 数据验证和序列化
- `jinja2`: 模板引擎（已有）

## 基本使用

### 1. 创建Agent

```python
from ai_kernel_generator.core.agent.agent_base import AgentBase
from ai_kernel_generator.utils.prompt_template import PromptTemplate

class MyAgent(AgentBase):
    def __init__(self):
        super().__init__(agent_name="MyAgent")

# 创建agent实例
agent = MyAgent()
```

### 2. 使用提示模板

```python
# 简单模板
template = PromptTemplate.from_template("你好，{name}！")
formatted = template.format(name="世界")
print(formatted)  # 输出: 你好，世界！

# Jinja2模板
template = PromptTemplate("你好，{{ name }}！今天是{{ date }}", template_format="jinja2")
formatted = template.format(name="用户", date="2025年")
print(formatted)  # 输出: 你好，用户！今天是2025年
```

### 3. 调用LLM

```python
import asyncio

async def main():
    agent = MyAgent()
    
    # 创建提示模板
    prompt = PromptTemplate.from_template("请介绍一下{topic}")
    
    # 准备输入
    input_data = {"topic": "人工智能"}
    
    # 调用LLM
    content, formatted_prompt, reasoning = await agent.run_llm(
        prompt, input_data, "sflow_ds_r1_default"
    )
    
    print(f"输入: {formatted_prompt}")
    print(f"输出: {content}")
    if reasoning:
        print(f"推理: {reasoning}")

# 运行
asyncio.run(main())
```

### 4. 使用输出解析器

```python
from ai_kernel_generator.utils.output_parser import PydanticOutputParser
from pydantic import BaseModel

# 定义输出结构
class Response(BaseModel):
    summary: str
    confidence: float
    keywords: list[str]

# 创建解析器
parser = PydanticOutputParser(Response)

# 解析JSON输出
json_text = '''
{
    "summary": "这是一个总结",
    "confidence": 0.95,
    "keywords": ["AI", "机器学习", "深度学习"]
}
'''

result = parser.parse(json_text)
print(f"总结: {result.summary}")
print(f"置信度: {result.confidence}")
print(f"关键词: {result.keywords}")
```

## 模型配置

支持的模型类型和配置示例：

### DeepSeek官方API
```yaml
deepseek_r1_default:
  api_base: "https://api.deepseek.com/beta"
  model: "deepseek-reasoner"
  api_key_env: "AIKG_DEEPSEEK_API_KEY"
  max_tokens: 16384
  temperature: 0.6
```

### 硅流平台
```yaml
sflow_ds_r1_default:
  api_base: "https://api.siliconflow.cn/v1/"
  model: "Pro/deepseek-ai/DeepSeek-R1"
  api_key_env: "AIKG_SILICONFLOW_API_KEY"
  max_tokens: 8192
  temperature: 0.6
```

### 本地VLLM
```yaml
vllm_deepseek_r1_default:
  api_base: "http://localhost:8001/v1"
  model: "deepseek-r1-distill-qwen-32b"
  max_tokens: 6144
  temperature: 0.7
```

### 本地Ollama
```yaml
ollama_qwen_coder_7b_default:
  api_base: "http://localhost:11434/v1"
  model: "qwen2.5-coder:7b"
  max_tokens: 8192
  temperature: 0.7
```

## 环境变量

设置必要的环境变量：

```bash
# DeepSeek官方API
export AIKG_DEEPSEEK_API_KEY="your-deepseek-api-key"

# 硅流平台API
export AIKG_SILICONFLOW_API_KEY="your-siliconflow-api-key"

# 火山引擎API
export AIKG_HUOSHAN_API_KEY="your-huoshan-api-key"

# 月之暗面API
export AIKG_MOONSHOT_API_KEY="your-moonshot-api-key"

# 本地服务端点（可选）
export AIKG_OLLAMA_API_BASE="http://localhost:11434"
export AIKG_VLLM_API_BASE="http://localhost:8001/v1"
```

## 流式输出

启用流式输出：

```bash
export STREAM_OUTPUT_MODE=on
```

或在代码中：

```python
import os
os.environ["STREAM_OUTPUT_MODE"] = "on"

# 调用时会实时打印输出
content, prompt, reasoning = await agent.run_llm(prompt, input_data, model_name)
```

## 完整示例

```python
import asyncio
import os
from ai_kernel_generator.core.agent.agent_base import AgentBase
from ai_kernel_generator.utils.prompt_template import PromptTemplate
from ai_kernel_generator.utils.output_parser import PydanticOutputParser
from pydantic import BaseModel

class CodeAnalysis(BaseModel):
    language: str
    complexity: str
    suggestions: list[str]

class CodeAgent(AgentBase):
    def __init__(self):
        super().__init__(agent_name="CodeAgent")
    
    async def analyze_code(self, code: str):
        # 创建提示模板
        template = PromptTemplate("""
请分析以下代码：

```
{{ code }}
```

请以JSON格式返回分析结果：
{
    "language": "编程语言",
    "complexity": "复杂度评估（低/中/高）",
    "suggestions": ["改进建议1", "改进建议2"]
}
""", template_format="jinja2")
        
        # 调用LLM
        content, _, _ = await self.run_llm(
            template, 
            {"code": code}, 
            "sflow_ds_r1_default"
        )
        
        # 解析结果
        parser = PydanticOutputParser(CodeAnalysis)
        return parser.parse(content)

async def main():
    # 设置API密钥
    os.environ["AIKG_SILICONFLOW_API_KEY"] = "your-api-key-here"
    
    agent = CodeAgent()
    
    code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""
    
    try:
        result = await agent.analyze_code(code)
        print(f"语言: {result.language}")
        print(f"复杂度: {result.complexity}")
        print("建议:")
        for suggestion in result.suggestions:
            print(f"- {suggestion}")
    except Exception as e:
        print(f"分析失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 故障排除

### 常见问题

1. **模块未找到错误**
   ```bash
   pip install openai pydantic jinja2
   ```

2. **API密钥错误**
   - 检查环境变量设置
   - 确认API密钥有效

3. **连接错误**
   - 检查网络连接
   - 确认服务端点地址正确

4. **模型不存在错误**
   - 检查模型名称是否正确
   - 确认模型在服务提供商处可用

### 调试技巧

1. **启用调试日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **检查配置**
   ```python
   from ai_kernel_generator.core.llm.openai_model_loader import create_openai_model
   model = create_openai_model("your-model-name")
   print(f"Model: {model.model_name}")
   print(f"Base URL: {model.client.base_url}")
   ```

3. **测试连接**
   ```python
   import asyncio
   
   async def test_connection():
       model = create_openai_model("sflow_ds_r1_default")
       messages = [{"role": "user", "content": "Hello"}]
       result = await model.generate(messages)
       print(result['content'])
   
   asyncio.run(test_connection())
   ```

## 更多信息

- 详细迁移指南: `MIGRATION_TO_OPENAI.md`
- 迁移总结: `MIGRATION_SUMMARY.md`
- 配置文件: `python/ai_kernel_generator/core/llm/llm_config.yaml`