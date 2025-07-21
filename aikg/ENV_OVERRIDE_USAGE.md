# 环境变量覆盖使用说明

## 概述

新的模型加载器现在支持通过环境变量动态覆盖配置文件中的参数，Agent也支持默认读取llm_config中的默认模型配置。

## 功能特性

### 1. 默认模型配置

Agent现在会自动从`llm_config.yaml`中读取`default_preset`作为默认模型：

```python
# Agent会自动使用配置文件中的default_preset
agent = MyAgent()
print(f"默认模型: {agent.default_model}")

# 也可以手动指定默认模型
agent = MyAgent(default_model="vllm_deepseek_r1_default")
```

### 2. 环境变量优先级

环境变量的优先级高于配置文件，支持以下覆盖：

1. **特定模型的环境变量** (最高优先级)
2. **通用环境变量** (中等优先级)  
3. **配置文件中的值** (最低优先级)

## 支持的环境变量

### API Base URL

| 模型前缀 | 环境变量 | 示例 |
|---------|---------|------|
| deepseek | `AIKG_DEEPSEEK_API_BASE` | https://api.deepseek.com/v1 |
| sflow | `AIKG_SILICONFLOW_API_BASE` | https://api.siliconflow.cn/v1 |
| volc | `AIKG_HUOSHAN_API_BASE` | https://ark.cn-beijing.volces.com/api/v3 |
| moonshot | `AIKG_MOONSHOT_API_BASE` | https://api.moonshot.cn/v1 |
| ollama | `AIKG_OLLAMA_API_BASE` | http://localhost:11434/v1 |
| vllm | `AIKG_VLLM_API_BASE` | http://localhost:8001/v1 |

### 模型名称

| 模型前缀 | 环境变量 | 示例 |
|---------|---------|------|
| deepseek | `AIKG_DEEPSEEK_MODEL` | deepseek-reasoner |
| sflow | `AIKG_SILICONFLOW_MODEL` | Pro/deepseek-ai/DeepSeek-R1 |
| volc | `AIKG_HUOSHAN_MODEL` | deepseek-r1-250120 |
| moonshot | `AIKG_MOONSHOT_MODEL` | kimi-k2-0711-preview |
| ollama | `AIKG_OLLAMA_MODEL` | qwen2.5-coder:7b |
| vllm | `AIKG_VLLM_MODEL` | deepseek-r1-distill-qwen-32b |

### 通用参数

| 参数 | 环境变量 | 类型 | 示例 |
|-----|---------|------|------|
| Temperature | `AIKG_TEMPERATURE` | float | 0.7 |
| Max Tokens | `AIKG_MAX_TOKENS` | int | 8192 |
| Top P | `AIKG_TOP_P` | float | 0.95 |
| Frequency Penalty | `AIKG_FREQUENCY_PENALTY` | float | 0.5 |
| Presence Penalty | `AIKG_PRESENCE_PENALTY` | float | 0.5 |

## 使用示例

### 1. 基本使用

```bash
# 设置硅流平台的API地址和模型
export AIKG_SILICONFLOW_API_BASE="https://api.siliconflow.cn/v1"
export AIKG_SILICONFLOW_MODEL="Pro/deepseek-ai/DeepSeek-R1"
export AIKG_SILICONFLOW_API_KEY="your-api-key"

# 设置通用参数
export AIKG_TEMPERATURE="0.8"
export AIKG_MAX_TOKENS="4096"
```

```python
from ai_kernel_generator.core.agent.agent_base import AgentBase
from ai_kernel_generator.utils.prompt_template import PromptTemplate

class MyAgent(AgentBase):
    def __init__(self):
        super().__init__(agent_name="MyAgent")

async def main():
    agent = MyAgent()
    
    # 使用默认模型（从配置文件读取）
    prompt = PromptTemplate.from_template("请介绍{topic}")
    content, _, _ = await agent.run_llm(
        prompt, 
        {"topic": "人工智能"}, 
        # 不指定模型名，使用默认模型
    )
    print(content)

asyncio.run(main())
```

### 2. 本地部署覆盖

```bash
# 覆盖VLLM服务地址
export AIKG_VLLM_API_BASE="http://192.168.1.100:8001/v1"
export AIKG_VLLM_MODEL="my-custom-model"

# 覆盖Ollama服务地址
export AIKG_OLLAMA_API_BASE="http://192.168.1.101:11434/v1"
export AIKG_OLLAMA_MODEL="llama3:8b"
```

### 3. 开发环境配置

```bash
# 开发环境使用不同的API端点
export AIKG_DEEPSEEK_API_BASE="https://dev-api.deepseek.com/v1"
export AIKG_TEMPERATURE="0.1"  # 开发环境使用更确定的输出
export AIKG_MAX_TOKENS="2048"  # 开发环境使用较少的token
```

### 4. 生产环境配置

```bash
# 生产环境配置
export AIKG_SILICONFLOW_API_BASE="https://api.siliconflow.cn/v1"
export AIKG_SILICONFLOW_API_KEY="prod-api-key"
export AIKG_TEMPERATURE="0.6"
export AIKG_MAX_TOKENS="8192"
```

## 配置优先级示例

假设配置文件中有：
```yaml
sflow_ds_r1_default:
  api_base: "https://api.siliconflow.cn/v1/"
  model: "Pro/deepseek-ai/DeepSeek-R1"
  temperature: 0.6
  max_tokens: 8192
```

设置环境变量：
```bash
export AIKG_SILICONFLOW_API_BASE="https://custom-api.example.com/v1"
export AIKG_TEMPERATURE="0.8"
```

最终使用的配置：
- `api_base`: `https://custom-api.example.com/v1` (环境变量覆盖)
- `model`: `Pro/deepseek-ai/DeepSeek-R1` (配置文件)
- `temperature`: `0.8` (环境变量覆盖)
- `max_tokens`: `8192` (配置文件)

## Agent默认模型

### 配置文件设置

在`llm_config.yaml`中：
```yaml
# 设置默认模型
default_preset: "sflow_ds_r1_default"

# 其他模型配置...
sflow_ds_r1_default:
  api_base: "https://api.siliconflow.cn/v1/"
  model: "Pro/deepseek-ai/DeepSeek-R1"
  # ...
```

### Agent使用

```python
# Agent自动读取默认模型
agent = MyAgent()
print(f"默认模型: {agent.default_model}")  # 输出: sflow_ds_r1_default

# 使用默认模型
await agent.run_llm(prompt, input_data)  # 不指定model_name

# 覆盖默认模型
await agent.run_llm(prompt, input_data, "vllm_deepseek_r1_default")
```

### 自定义默认模型

```python
# 在Agent初始化时指定默认模型
agent = MyAgent(default_model="ollama_qwen_coder_7b_default")
```

## 调试和验证

### 启用调试日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 现在会看到详细的配置加载和覆盖信息
model = create_openai_model("sflow_ds_r1_default")
```

### 检查最终配置

```python
from ai_kernel_generator.core.llm.openai_model_loader import create_openai_model

model = create_openai_model("sflow_ds_r1_default")
print(f"API Base: {model.client.base_url}")
print(f"Model Name: {model.model_name}")
print(f"Parameters: {model.model_params}")
```

## 最佳实践

### 1. 环境分离

```bash
# 开发环境 (.env.dev)
AIKG_SILICONFLOW_API_BASE="https://dev-api.siliconflow.cn/v1"
AIKG_TEMPERATURE="0.1"

# 测试环境 (.env.test)
AIKG_SILICONFLOW_API_BASE="https://test-api.siliconflow.cn/v1"
AIKG_TEMPERATURE="0.5"

# 生产环境 (.env.prod)
AIKG_SILICONFLOW_API_BASE="https://api.siliconflow.cn/v1"
AIKG_TEMPERATURE="0.6"
```

### 2. Docker部署

```dockerfile
# Dockerfile
ENV AIKG_SILICONFLOW_API_BASE="https://api.siliconflow.cn/v1"
ENV AIKG_TEMPERATURE="0.6"
ENV AIKG_MAX_TOKENS="8192"
```

### 3. Kubernetes部署

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aikg-config
data:
  AIKG_SILICONFLOW_API_BASE: "https://api.siliconflow.cn/v1"
  AIKG_TEMPERATURE: "0.6"
  AIKG_MAX_TOKENS: "8192"
```

## 故障排除

### 1. 环境变量不生效

- 检查环境变量名称是否正确
- 确认环境变量已正确设置：`echo $AIKG_SILICONFLOW_API_BASE`
- 启用调试日志查看覆盖过程

### 2. 类型转换错误

环境变量都是字符串，系统会自动转换：
- `temperature`, `top_p`, `frequency_penalty`, `presence_penalty` → `float`
- `max_tokens` → `int`
- 其他参数 → `str`

如果转换失败，会使用配置文件中的默认值。

### 3. 模型前缀不匹配

确保模型名称以正确的前缀开头：
- `deepseek_*` → deepseek前缀
- `sflow_*` → sflow前缀
- `volc_*` → volc前缀
- 等等

## 迁移指南

从旧版本迁移时：

1. **更新Agent初始化**：
   ```python
   # 旧版本
   agent = MyAgent()
   
   # 新版本（可选指定默认模型）
   agent = MyAgent(default_model="your-preferred-model")
   ```

2. **设置环境变量**：
   ```bash
   # 根据使用的模型设置相应的环境变量
   export AIKG_SILICONFLOW_API_BASE="your-api-base"
   export AIKG_SILICONFLOW_API_KEY="your-api-key"
   ```

3. **更新调用方式**：
   ```python
   # 现在可以不指定模型名称，使用默认模型
   await agent.run_llm(prompt, input_data)  # 使用默认模型
   ```

这样的设计提供了最大的灵活性，既支持配置文件的集中管理，也支持环境变量的动态覆盖。