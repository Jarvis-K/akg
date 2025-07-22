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

import re
from typing import Dict, Any, List
from jinja2 import Template as Jinja2Template


class PromptTemplate:
    """简单的提示模板类，替换langchain的PromptTemplate"""
    
    def __init__(self, template: str, template_format: str = "jinja2", input_variables: List[str] = None):
        """
        初始化提示模板
        
        Args:
            template: 模板字符串
            template_format: 模板格式，支持 "jinja2" 和 "f-string"
            input_variables: 输入变量列表，如果为None则自动提取
        """
        self.template = template
        self.template_format = template_format
        self.input_variables = input_variables or self._extract_variables()
        
        if template_format == "jinja2":
            self.jinja_template = Jinja2Template(template)
    
    def _extract_variables(self) -> List[str]:
        """从模板中提取变量名"""
        if self.template_format == "jinja2":
            # 提取Jinja2变量 {{ variable }}
            pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}'
            variables = re.findall(pattern, self.template)
            return list(set(variables))
        else:
            # 提取f-string变量 {variable}
            pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
            variables = re.findall(pattern, self.template)
            return list(set(variables))
    
    def format(self, **kwargs) -> str:
        """格式化模板"""
        if self.template_format == "jinja2":
            return self.jinja_template.render(**kwargs)
        else:
            return self.template.format(**kwargs)
    
    @classmethod
    def from_template(cls, template: str, template_format: str = "f-string") -> "PromptTemplate":
        """从模板字符串创建PromptTemplate实例"""
        return cls(template=template, template_format=template_format)
    
    def __str__(self) -> str:
        return f"PromptTemplate(template='{self.template[:50]}...', input_variables={self.input_variables})"