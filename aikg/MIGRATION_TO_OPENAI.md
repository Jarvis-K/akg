# 从LangChain迁移到OpenAI接口

本文档说明如何将项目从LangChain技术栈迁移到直接使用OpenAI接口。

## 迁移概述

### 主要变化

1. **模型加载器**: `model_loader.py` → `openai_model_loader.py`
2. **提示模板**: `langchain.prompts.PromptTemplate` → `ai_kernel_generator.utils.prompt_template.PromptTemplate`
3. **输出解析器**: `langchain.output_parsers.PydanticOutputParser` → `ai_kernel_generator.utils.output_parser.PydanticOutputParser`
4. **Agent基类**: 更新`agent_base.py`以使用OpenAI接口

### 依赖变化

**移除的依赖**:
- langchain
- langchain-deepseek
- langchain-ollama
- langchain_ollama
- langchain_community

**新增的依赖**:
- openai
- pydantic (如果之前没有)

## 新组件说明

### 1. OpenAI模型加载器 (`openai_model_loader.py`)

提供统一的OpenAI接口包装器，支持：
- DeepSeek官方API
- 硅流平台API
- 火山引擎API
- VLLM本地部署
- Ollama本地部署

```python
from ai_kernel_generator.core.llm.openai_model_loader import create_openai_model

# 创建模型实例
model = create_openai_model("sflow_ds_r1_default")

# 生成响应
messages = [{"role": "user", "content": "Hello"}]
result = await model.generate(messages)
print(result['content'])
```

### 2. 提示模板 (`prompt_template.py`)

简化的提示模板实现，支持Jinja2和f-string格式：

```python
from ai_kernel_generator.utils.prompt_template import PromptTemplate

# 使用f-string格式
template = PromptTemplate.from_template("Hello {name}!")
formatted = template.format(name="World")

# 使用Jinja2格式
template = PromptTemplate("Hello {{ name }}!", template_format="jinja2")
formatted = template.format(name="World")
```

### 3. 输出解析器 (`output_parser.py`)

Pydantic输出解析器，支持JSON格式解析：

```python
from ai_kernel_generator.utils.output_parser import PydanticOutputParser
from pydantic import BaseModel

class Response(BaseModel):
    message: str
    confidence: float

parser = PydanticOutputParser(Response)
result = parser.parse('{"message": "Hello", "confidence": 0.95}')
```

## 迁移步骤

### 自动迁移

使用提供的迁移脚本：

```bash
# 干运行，查看需要迁移的文件
python tools/migrate_to_openai.py --dry-run

# 执行迁移
python tools/migrate_to_openai.py
```

### 手动迁移

1. **更新导入语句**:
   ```python
   # 旧的
   from langchain.prompts import PromptTemplate
   from langchain.output_parsers import PydanticOutputParser
   from ai_kernel_generator.core.llm.model_loader import create_model
   
   # 新的
   from ai_kernel_generator.utils.prompt_template import PromptTemplate
   from ai_kernel_generator.utils.output_parser import PydanticOutputParser
   from ai_kernel_generator.core.llm.openai_model_loader import create_openai_model
   ```

2. **更新函数调用**:
   ```python
   # 旧的
   model = create_model(model_name)
   
   # 新的
   model = create_openai_model(model_name)
   ```

3. **更新Agent基类使用**:
   ```python
   # Agent中的run_llm方法现在直接使用OpenAI接口
   # 无需修改调用方式，接口保持兼容
   ```

### 更新requirements.txt

```txt
# 移除
langchain
langchain-deepseek
langchain-ollama
langchain_ollama
langchain_community

# 添加
openai
pydantic
```

## 配置说明

模型配置文件 `llm_config.yaml` 保持不变，所有现有配置都兼容新的OpenAI接口。

## 测试

运行新的测试文件验证迁移结果：

```bash
# 测试OpenAI接口
python tests/utils/test_openai_run_llm.py

# 测试原有接口（现在使用OpenAI实现）
python tests/utils/test_run_llm.py
```

## 兼容性

- **向后兼容**: 现有的Agent代码无需修改，接口保持一致
- **配置兼容**: 所有模型配置继续有效
- **功能兼容**: 支持流式输出、reasoning内容等所有原有功能

## 优势

1. **简化依赖**: 移除了复杂的LangChain依赖链
2. **更好的控制**: 直接使用OpenAI接口，更容易调试和定制
3. **性能提升**: 减少中间层，提高执行效率
4. **更好的兼容性**: 支持更多OpenAI兼容的模型服务

## 故障排除

### 常见问题

1. **导入错误**: 确保新的工具类文件在正确位置
2. **模型配置错误**: 检查`llm_config.yaml`中的配置是否正确
3. **API密钥问题**: 确保环境变量设置正确

### 调试建议

1. 启用调试日志查看详细信息
2. 使用测试文件验证各组件功能
3. 检查网络连接和API访问权限

## 回滚方案

如果需要回滚到LangChain：

1. 恢复原有的`requirements.txt`
2. 恢复原有的导入语句
3. 使用原有的`model_loader.py`

建议在迁移前备份重要文件。