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

import json
import re
import logging
from typing import Type, TypeVar, Any
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class PydanticOutputParser:
    """Pydantic输出解析器，替换langchain的PydanticOutputParser"""
    
    def __init__(self, pydantic_object: Type[T]):
        """
        初始化解析器
        
        Args:
            pydantic_object: Pydantic模型类
        """
        self.pydantic_object = pydantic_object
    
    def parse(self, text: str) -> T:
        """
        解析文本为Pydantic对象
        
        Args:
            text: 要解析的文本
            
        Returns:
            解析后的Pydantic对象
            
        Raises:
            ValueError: 解析失败时抛出
        """
        try:
            # 尝试直接解析JSON
            if text.strip().startswith('{') and text.strip().endswith('}'):
                data = json.loads(text)
                return self.pydantic_object(**data)
            
            # 尝试提取JSON块
            json_match = self._extract_json_block(text)
            if json_match:
                data = json.loads(json_match)
                return self.pydantic_object(**data)
                
            # 如果都失败了，尝试直接用文本创建对象
            return self.pydantic_object(content=text)
            
        except (json.JSONDecodeError, ValidationError, TypeError) as e:
            raise ValueError(f"无法解析文本为 {self.pydantic_object.__name__}: {str(e)}")
    
    def _extract_json_block(self, text: str) -> str:
        """从文本中提取JSON块"""
        # 查找```json...```代码块
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        
        # 查找第一个完整的JSON对象
        brace_count = 0
        start_idx = text.find('{')
        if start_idx == -1:
            return None
            
        for i, char in enumerate(text[start_idx:], start_idx):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return text[start_idx:i+1]
        
        return None
    
    def get_format_instructions(self) -> str:
        """获取格式化指令"""
        schema = self.pydantic_object.model_json_schema()
        return f"请以JSON格式返回结果，遵循以下schema：\n```json\n{json.dumps(schema, indent=2, ensure_ascii=False)}\n```"